#!/usr/bin/env python3
import sys
import os
import re
import glob
import json
import time
import fcntl
import sqlite3
import subprocess
from datetime import datetime, timezone

CACHE_FILE = "/tmp/agy_quota_cache.json"
LOCK_FILE = "/tmp/agy_quota_fetch.lock"
CACHE_TTL = 60  # seconds

GLOG_RE = re.compile(r"^[IWEF](\d{2})(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\.(\d{6})")

# SQLite step_type constants in Antigravity conversation DB
STEP_USER_INPUT = 14
STEP_PLANNER_RESPONSE = 15
STEP_ERROR_MESSAGE = 17
IGNORED_SYSTEM_STEP_TYPES = (23, 90, 98, 101)
TOOL_STEP_TYPES = (5, 7, 8, 9, 21, 31, 33, 127, 132)

# SQLite status constants
STATUS_PENDING = 1
STATUS_RUNNING = 2
STATUS_DONE = 3
STATUS_CANCELED = 4
STATUS_INVALID = 5
STATUS_RUNNING_ALT = 6
STATUS_ERROR = 7
ACTIVE_STATUSES = (STATUS_PENDING, STATUS_RUNNING, STATUS_RUNNING_ALT)

STATUS_PRIORITY = {
    "спит": 0,
    "отдыхает": 1,
    "думает": 2,
    "работает": 3,
    "ошибка": 4,
}


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
        return f"{mins}м"
    except Exception:
        return ""


def check_custom_script(script_path):
    if script_path and os.path.exists(script_path) and os.access(script_path, os.X_OK):
        try:
            res = subprocess.run([script_path], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                return json.loads(res.stdout.strip())
        except Exception:
            pass
    return None


def get_active_agy_pids():
    """Return all interactive agy CLI PIDs attached to a terminal (TTY/PTS)."""
    pids = []
    try:
        res = subprocess.run(["pgrep", "-x", "agy"], capture_output=True, text=True)
        if res.returncode == 0:
            for pid_str in res.stdout.strip().split():
                try:
                    pid = int(pid_str)
                    fd0 = os.readlink(f"/proc/{pid}/fd/0")
                    if not (fd0.startswith("/dev/pts/") or fd0.startswith("/dev/tty")):
                        continue
                    with open(f"/proc/{pid}/cmdline", "rb") as f:
                        cmdline = f.read().decode("utf-8", errors="ignore")
                    if "/usage" in cmdline or "--refresh-only" in cmdline or "\x00-p\x00" in cmdline:
                        continue
                    pids.append(pid)
                except Exception:
                    continue
    except Exception:
        pass
    return pids


def decode_varint(buf, pos):
    val = 0
    shift = 0
    while pos < len(buf):
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7
    return val, pos


def parse_meta_timestamps(meta):
    """Extract protobuf timestamps (1=created, 6=started, 7=updated, 8=completed) from steps.metadata."""
    res = {}
    if not meta:
        return res
    i = 0
    n = len(meta)
    while i < n:
        tag, i = decode_varint(meta, i)
        wire = tag & 7
        field_num = tag >> 3
        if wire == 2:
            length, i = decode_varint(meta, i)
            sub = meta[i : i + length]
            i += length
            if field_num in (1, 6, 7, 8) and len(sub) >= 5 and sub[0] == 0x08:
                sec, p2 = decode_varint(sub, 1)
                nanos = 0
                if p2 < len(sub) and sub[p2] == 0x10:
                    nanos, _ = decode_varint(sub, p2 + 1)
                if 1700000000 < sec < 2100000000:
                    res[field_num] = sec + nanos / 1e9
        elif wire == 0:
            _, i = decode_varint(meta, i)
        else:
            break
    return res


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


def inspect_pid_fds(pid):
    """Find open conversation SQLite DBs and log file for a specific agy PID."""
    dbs = set()
    log_file = None
    fd_dir = f"/proc/{pid}/fd"
    try:
        for fd_name in os.listdir(fd_dir):
            try:
                target = os.readlink(f"{fd_dir}/{fd_name}")
                if target.endswith(".db") and "/conversations/" in target and os.path.exists(target):
                    dbs.add(target)
                elif fd_name in ("1", "2") and target.endswith(".log") and os.path.exists(target):
                    log_file = target
            except Exception:
                continue
    except Exception:
        pass
    return list(dbs), log_file


def check_db_status(db_path, now):
    """Determine conversation status directly from Antigravity SQLite trajectory steps."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.2)
        cur = conn.cursor()
        cur.execute(
            "SELECT idx, step_type, status, metadata, substr(step_payload, 1, 160) "
            "FROM steps WHERE step_type NOT IN (23, 90, 98, 101) "
            "ORDER BY idx DESC LIMIT 6"
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        return None

    if not rows:
        return "отдыхает"

    # Hold 'работает' for 2.8s after any fast built-in tool (view_file, grep_search, etc.) completes
    for idx, st_type, status, meta, payload in rows:
        if st_type in TOOL_STEP_TYPES:
            ts_map = parse_meta_timestamps(meta)
            latest_ts = max(ts_map.values()) if ts_map else 0
            if status in ACTIVE_STATUSES and (now - latest_ts) <= 120.0:
                if payload and b"ask_question" in payload:
                    return "отдыхает"
                return "работает"
            if status == STATUS_DONE and (now - latest_ts) <= 2.8:
                return "работает"

    top_idx, top_type, top_status, top_meta, top_payload = rows[0]
    top_ts_map = parse_meta_timestamps(top_meta)
    top_ts = max(top_ts_map.values()) if top_ts_map else 0
    top_age = (now - top_ts) if top_ts else 999999.0

    # 1. Error check
    if (top_status == STATUS_ERROR or top_type == STEP_ERROR_MESSAGE) and top_age <= 12.0:
        return "ошибка"

    # 2. Planner response actively streaming / thinking
    if top_type == STEP_PLANNER_RESPONSE:
        if top_status in ACTIVE_STATUSES and top_age <= 180.0:
            return "думает"
        return "отдыхает"

    # 3. User just sent input, or a tool just finished and LLM is thinking on the next step
    if top_type == STEP_USER_INPUT and top_age <= 120.0:
        return "думает"

    if top_type in TOOL_STEP_TYPES and top_status == STATUS_DONE and top_age <= 90.0:
        return "думает"

    return "отдыхает"


def check_single_pid_status(pid, now):
    # 1. Check if agy has active child processes (e.g. bash command via run_command)
    try:
        res = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return "работает"
    except Exception:
        pass

    dbs, active_log = inspect_pid_fds(pid)
    best_status = "отдыхает"

    # 2. Check SQLite trajectory databases open by this PID
    for db_path in dbs:
        st = check_db_status(db_path, now)
        if st and STATUS_PRIORITY.get(st, 0) > STATUS_PRIORITY.get(best_status, 0):
            best_status = st

    # 3. Check active glog file for immediate pre-DB events (e.g. first 1s of request)
    if active_log and os.path.exists(active_log):
        try:
            with open(active_log, "r", errors="ignore") as f:
                lines = f.readlines()[-30:]
            for line in reversed(lines):
                ts = parse_glog_timestamp(line)
                if ts and (now - ts) <= 5.0:
                    if any(
                        k in line
                        for k in (
                            "streamGenerateContent",
                            "generateContent",
                            "SEND_USER_CASCADE_MESSAGE",
                            "fetchAvailableModels",
                            "LLM Monitor",
                        )
                    ):
                        if STATUS_PRIORITY["думает"] > STATUS_PRIORITY.get(best_status, 0):
                            best_status = "думает"
                    elif "go_command.go" in line or "ExecuteTool" in line or "agy_tool_safety" in line:
                        if STATUS_PRIORITY["работает"] > STATUS_PRIORITY.get(best_status, 0):
                            best_status = "работает"
        except Exception:
            pass

    return best_status


def check_agy_status(active_pids):
    if not active_pids:
        return "спит"

    now = time.time()
    best_status = "отдыхает"
    for pid in active_pids:
        st = check_single_pid_status(pid, now)
        if STATUS_PRIORITY.get(st, 0) > STATUS_PRIORITY.get(best_status, 0):
            best_status = st
    return best_status


def fetch_live_quota():
    """Fetch exact quota from Antigravity CLI with a non-blocking file lock to prevent process stampedes."""
    lock_fd = None
    try:
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        if lock_fd:
            lock_fd.close()
        return None

    log_dir = os.path.expanduser("~/.gemini/antigravity-cli/log")
    before_logs = set(glob.glob(f"{log_dir}/cli-*.log")) if os.path.isdir(log_dir) else set()

    try:
        res = subprocess.run(
            ["agy", "-p", "/usage", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            data = json.loads(res.stdout.strip())
            groups = data.get("command", {}).get("data", {}).get("groups", [])
            gemini_group = next(
                (g for g in groups if "gemini" in g.get("name", "").lower()),
                groups[0] if groups else None,
            )
            if gemini_group:
                rem_5h, rem_week = 100, 100
                exact_5h, exact_week = 100.0, 100.0
                reset_5h, reset_week = "", ""

                for b in gemini_group.get("buckets", []):
                    frac = b.get("remaining_fraction", 1.0)
                    pct = max(0, min(100, int(round(frac * 100))))
                    exact = round(frac * 100, 1)
                    r_time = format_reset_time(b.get("reset_time", ""))

                    if b.get("id") == "gemini-5h" or b.get("window") == "5h":
                        rem_5h, exact_5h, reset_5h = pct, exact, r_time
                    elif b.get("id") == "gemini-weekly" or b.get("window") == "weekly":
                        rem_week, exact_week, reset_week = pct, exact, r_time

                quota = {
                    "bar1_label": "5 часов",
                    "bar1_percent": rem_5h,
                    "bar1_exact": exact_5h,
                    "bar1_reset": reset_5h,
                    "bar2_label": "неделя",
                    "bar2_percent": rem_week,
                    "bar2_exact": exact_week,
                    "bar2_reset": reset_week,
                    "timestamp": time.time(),
                }
                try:
                    with open(CACHE_FILE, "w") as f:
                        json.dump(quota, f)
                except Exception:
                    pass
                return quota
    except Exception:
        pass
    finally:
        # Clean up one-shot log files created by `agy -p /usage` so ~/.gemini/antigravity-cli/log doesn't bloat
        if os.path.isdir(log_dir):
            after_logs = set(glob.glob(f"{log_dir}/cli-*.log"))
            for new_log in after_logs - before_logs:
                try:
                    with open(new_log, "r", errors="ignore") as lf:
                        head = lf.read(4096)
                    if "running slash command /usage" in head or "You are not logged into Antigravity" in head:
                        os.remove(new_log)
                except Exception:
                    pass
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
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

    if is_active and (not cached or (now - cached.get("timestamp", 0)) > CACHE_TTL):
        try:
            subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "--refresh-only"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
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
        "bar2_reset": "",
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

    active_pids = get_active_agy_pids()
    current_status = check_agy_status(active_pids)
    usage = get_agy_usage(is_active=bool(active_pids))

    result = {
        "status": current_status,
        "bar1_label": usage.get("bar1_label", "5 часов"),
        "bar1_percent": usage.get("bar1_percent", 100),
        "bar1_exact": usage.get("bar1_exact", usage.get("bar1_percent", 100)),
        "bar1_reset": usage.get("bar1_reset", ""),
        "bar2_label": usage.get("bar2_label", "неделя"),
        "bar2_percent": usage.get("bar2_percent", 100),
        "bar2_exact": usage.get("bar2_exact", usage.get("bar2_percent", 100)),
        "bar2_reset": usage.get("bar2_reset", ""),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
