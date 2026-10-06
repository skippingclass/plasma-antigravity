#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import time
import glob

CACHE_FILE = "/tmp/agy_quota_cache.json"
CACHE_TTL = 60  # seconds

def check_custom_script(script_path):
    if script_path and os.path.exists(script_path) and os.access(script_path, os.X_OK):
        try:
            res = subprocess.run([script_path], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                data = json.loads(res.stdout.strip())
                return data
        except Exception:
            pass
    return None

def get_active_agy_pid():
    """
    Find the interactive agy CLI process PID attached to a terminal (TTY/PTS).
    Background fetchers (pipes) and non-interactive daemons are strictly ignored.
    """
    try:
        res = subprocess.run(["pgrep", "-x", "agy"], capture_output=True, text=True)
        if res.returncode == 0:
            for pid_str in res.stdout.strip().split():
                pid = int(pid_str)
                try:
                    # Interactive CLI session must have stdin attached to a PTS or TTY
                    fd0 = os.readlink(f"/proc/{pid}/fd/0")
                    if not (fd0.startswith("/dev/pts/") or fd0.startswith("/dev/tty")):
                        continue

                    with open(f"/proc/{pid}/cmdline", "rb") as f:
                        cmdline = f.read().decode("utf-8", errors="ignore")
                    # Ignore background usage fetchers or one-shots
                    if "/usage" in cmdline or "--refresh-only" in cmdline or "-p" in cmdline:
                        continue
                    return pid
                except Exception:
                    continue
    except Exception:
        pass
    return None

import re
from datetime import datetime

GLOG_RE = re.compile(r'^[IWEF](\d{2})(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\.(\d{6})')

def parse_glog_timestamp(line):
    m = GLOG_RE.match(line)
    if not m:
        return None
    month, day, hour, minute, second, micro = map(int, m.groups())
    now = datetime.now()
    try:
        dt = datetime(now.year, month, day, hour, minute, second, micro)
        return dt.timestamp()
    except Exception:
        return None

def check_agy_status(active_pid):
    """
    Determine agent state:
    - спит: no interactive agy process running in any terminal
    - думает: streamGenerateContent active within last 4s
    - работает: tool/bash running (< 4s or child process active)
    - отдыхает: interactive session is idle, waiting for user input
    """
    if not active_pid:
        return "спит"

    now = time.time()
    active_log = None

    # 1. Check if the active agy process is currently running child commands (tools/bash)
    try:
        res = subprocess.run(["pgrep", "-P", str(active_pid)], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return "работает"
    except Exception:
        pass

    # 2. Get the exact log file being written by this active agy process
    try:
        fd1 = os.readlink(f"/proc/{active_pid}/fd/1")
        if os.path.exists(fd1) and fd1.endswith(".log"):
            active_log = fd1
    except Exception:
        pass

    if not active_log:
        logs = sorted(glob.glob(os.path.expanduser("~/.gemini/antigravity-cli/log/cli-*.log")), key=os.path.getmtime)
        if logs:
            active_log = logs[-1]

    if active_log and os.path.exists(active_log):
        try:
            with open(active_log, "r", errors="ignore") as f:
                lines = f.readlines()[-40:]
            
            # Check recent log events in reverse order
            for line in reversed(lines):
                ts = parse_glog_timestamp(line)
                if ts and (now - ts) <= 4.0:
                    if "streamGenerateContent" in line or "Thinking" in line or "reasoning" in line:
                        return "думает"
                    if "go_command.go" in line or "ExecuteTool" in line:
                        return "работает"
        except Exception:
            pass

    return "отдыхает"

def fetch_live_quota():
    """Fetch exact quota from Antigravity CLI via agy -p /usage --output-format json."""
    try:
        res = subprocess.run(
            ["agy", "-p", "/usage", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=8
        )
        if res.returncode == 0:
            data = json.loads(res.stdout.strip())
            groups = data.get("command", {}).get("data", {}).get("groups", [])
            gemini_group = next((g for g in groups if "gemini" in g.get("name", "").lower()), groups[0] if groups else None)
            if gemini_group:
                rem_5h = 100
                rem_week = 100
                for b in gemini_group.get("buckets", []):
                    frac = b.get("remaining_fraction", 1.0)
                    pct = max(0, min(100, int(round(frac * 100))))
                    if b.get("id") == "gemini-5h" or b.get("window") == "5h":
                        rem_5h = pct
                    elif b.get("id") == "gemini-weekly" or b.get("window") == "weekly":
                        rem_week = pct

                quota = {
                    "bar1_label": "5 часов",
                    "bar1_percent": rem_5h,
                    "bar2_label": "неделя",
                    "bar2_percent": rem_week,
                    "timestamp": time.time()
                }
                try:
                    with open(CACHE_FILE, "w") as f:
                        json.dump(quota, f)
                except Exception:
                    pass
                return quota
    except Exception:
        pass
    return None

def get_agy_usage(is_active):
    cached = None
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached = json.load(f)
        except Exception:
            pass

    now = time.time()

    # If agy is active and cache is expired or missing, trigger background refresh
    if is_active:
        if not cached or (now - cached.get("timestamp", 0)) > CACHE_TTL:
            try:
                subprocess.Popen(
                    [sys.executable, "-c", "import sys; from status_provider import fetch_live_quota; fetch_live_quota()"],
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
            except Exception:
                pass

    if cached:
        return cached

    return {
        "bar1_label": "5 часов",
        "bar1_percent": 100,
        "bar2_label": "неделя",
        "bar2_percent": 100
    }

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--refresh-only":
        fetch_live_quota()
        return

    custom_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if custom_path and not custom_path.startswith("-"):
        custom_data = check_custom_script(custom_path)
        if custom_data:
            print(json.dumps(custom_data, ensure_ascii=False))
            return

    active_pid = get_active_agy_pid()
    current_status = check_agy_status(active_pid)
    usage = get_agy_usage(is_active=(active_pid is not None))

    result = {
        "status": current_status,
        "bar1_label": usage.get("bar1_label", "5 часов"),
        "bar1_percent": usage.get("bar1_percent", 100),
        "bar2_label": usage.get("bar2_label", "неделя"),
        "bar2_percent": usage.get("bar2_percent", 100)
    }
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
