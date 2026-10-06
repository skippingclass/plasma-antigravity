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
    """Find the interactive agy CLI process PID, ignoring background usage queries."""
    try:
        res = subprocess.run(["pgrep", "-x", "agy"], capture_output=True, text=True)
        if res.returncode == 0:
            for pid_str in res.stdout.strip().split():
                pid = int(pid_str)
                try:
                    with open(f"/proc/{pid}/cmdline", "rb") as f:
                        cmdline = f.read().decode("utf-8", errors="ignore")
                    # Ignore background usage fetchers and one-shot commands
                    if "/usage" in cmdline or "--refresh-only" in cmdline:
                        continue
                    return pid
                except Exception:
                    continue
    except Exception:
        pass
    return None

def check_agy_status(active_pid):
    """
    Determine agent state:
    - спит: no interactive agy process is running
    - думает: streamGenerateContent active in current session log (< 5s)
    - работает: tool/bash active in current session log (< 5s)
    - отдыхает: session is idle, waiting for user input
    """
    if not active_pid:
        return "спит"

    now = time.time()
    active_log = None

    # Get the exact log file being written by this active agy process
    try:
        fd1 = os.readlink(f"/proc/{active_pid}/fd/1")
        if os.path.exists(fd1) and fd1.endswith(".log"):
            active_log = fd1
    except Exception:
        pass

    # Fallback to the latest log file if fd1 wasn't a log
    if not active_log:
        logs = sorted(glob.glob(os.path.expanduser("~/.gemini/antigravity-cli/log/cli-*.log")), key=os.path.getmtime)
        if logs:
            active_log = logs[-1]

    if active_log and os.path.exists(active_log):
        try:
            mtime = os.path.getmtime(active_log)
            # If written to within the last 5 seconds, it is actively processing
            if (now - mtime) < 5.0:
                with open(active_log, "rb") as f:
                    f.seek(max(0, os.path.getsize(active_log) - 4096))
                    tail = f.read().decode("utf-8", errors="ignore")
                if "streamGenerateContent" in tail or "Thinking" in tail or "reasoning" in tail:
                    return "думает"
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

    # Only fetch if active or no cache at all
    if not cached or "timestamp" not in cached:
        live = fetch_live_quota()
        if live:
            return live
    elif is_active and (now - cached.get("timestamp", 0)) > CACHE_TTL:
        # Refresh in background only when agy is actually active
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
