#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import time
import glob
from datetime import datetime, timezone

CACHE_FILE = "/tmp/agy_quota_cache.json"
CACHE_TTL = 30  # seconds

def format_reset_time(iso_str):
    if not iso_str:
        return ""
    try:
        target = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = int((target - now).total_seconds())
        if diff <= 0:
            return "скоро"
        hours = diff // 3600
        mins = (diff % 3600) // 60
        if hours >= 24:
            days = hours // 24
            rem_h = hours % 24
            return f"{days}д {rem_h}ч"
        elif hours > 0:
            return f"{hours}ч {mins}м"
        else:
            return f"{mins}м"
    except Exception:
        return ""

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

def check_agy_status():
    now = time.time()
    
    # 1. Process check: check if agy or antigravity AppImage/binary is running
    is_running = False
    try:
        res = subprocess.run(["pgrep", "-f", "(agy|antigravity)"], capture_output=True)
        is_running = (res.returncode == 0)
    except Exception:
        pass

    if not is_running:
        return "спит"

    # 2. Check real-time activity via latest CLI log file
    log_files = sorted(glob.glob(os.path.expanduser("~/.gemini/antigravity-cli/log/cli-*.log")), key=os.path.getmtime)
    if log_files:
        latest_log = log_files[-1]
        try:
            mtime = os.path.getmtime(latest_log)
            # If log was written to in the last 6 seconds, agent is actively executing
            if (now - mtime) < 6.0:
                with open(latest_log, "rb") as f:
                    f.seek(max(0, os.path.getsize(latest_log) - 4096))
                    tail = f.read().decode("utf-8", errors="ignore")
                if "streamGenerateContent" in tail or "Thinking" in tail or "reasoning" in tail:
                    return "думает"
                return "работает"
        except Exception:
            pass

    return "отдыхает"

def fetch_live_quota():
    """Fetch exact live quota from Antigravity CLI via agy -p /usage --output-format json"""
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
            # Priority: group containing 'gemini', else first available group
            gemini_group = next((g for g in groups if "gemini" in g.get("name", "").lower()), groups[0] if groups else None)
            if gemini_group:
                rem_5h = 100
                rem_week = 100
                exact_5h = 100.0
                exact_week = 100.0
                reset_5h = ""
                reset_week = ""

                for b in gemini_group.get("buckets", []):
                    frac = b.get("remaining_fraction", 1.0)
                    pct = max(0, min(100, int(round(frac * 100))))
                    exact = round(frac * 100, 1)
                    r_time = format_reset_time(b.get("reset_time", ""))

                    if b.get("id") == "gemini-5h" or b.get("window") == "5h":
                        rem_5h = pct
                        exact_5h = exact
                        reset_5h = r_time
                    elif b.get("id") == "gemini-weekly" or b.get("window") == "weekly":
                        rem_week = pct
                        exact_week = exact
                        reset_week = r_time

                quota = {
                    "bar1_label": "5 часов",
                    "bar1_percent": rem_5h,
                    "bar1_exact": exact_5h,
                    "bar1_reset": reset_5h,
                    "bar2_label": "неделя",
                    "bar2_percent": rem_week,
                    "bar2_exact": exact_week,
                    "bar2_reset": reset_week,
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

def get_agy_usage():
    cached = None
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached = json.load(f)
        except Exception:
            pass

    now = time.time()

    if not cached or "timestamp" not in cached:
        # First run: fetch synchronously
        live = fetch_live_quota()
        if live:
            return live
    elif (now - cached.get("timestamp", 0)) > CACHE_TTL:
        # Background refresh without blocking current status report
        try:
            subprocess.Popen([sys.executable, "-c", "import sys; from status_provider import fetch_live_quota; fetch_live_quota()"], cwd=os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            pass

    if cached:
        return cached

    return {
        "bar1_label": "5 часов",
        "bar1_percent": 100,
        "bar1_exact": 100.0,
        "bar1_reset": "",
        "bar2_label": "неделя",
        "bar2_percent": 100,
        "bar2_exact": 100.0,
        "bar2_reset": ""
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

    current_status = check_agy_status()
    usage = get_agy_usage()

    result = {
        "status": current_status,
        "bar1_label": usage.get("bar1_label", "5 часов"),
        "bar1_percent": usage.get("bar1_percent", 100),
        "bar1_exact": usage.get("bar1_exact", usage.get("bar1_percent", 100)),
        "bar1_reset": usage.get("bar1_reset", ""),
        "bar2_label": usage.get("bar2_label", "неделя"),
        "bar2_percent": usage.get("bar2_percent", 100),
        "bar2_exact": usage.get("bar2_exact", usage.get("bar2_percent", 100)),
        "bar2_reset": usage.get("bar2_reset", "")
    }
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
