"""
conftest.py
-----------
PyTest loads this file automatically. It records a one-line summary of
EVERY real test run into reports/test_history.json, which the Testing
Dashboard shows as "Recent Test Executions". Only actual counts reported
by pytest are stored.
"""

import json
import time
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent.parent / "reports" / "test_history.json"
MAX_HISTORY = 20
_start_time = None


def pytest_sessionstart(session):
    global _start_time
    _start_time = time.time()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    stats = terminalreporter.stats
    run = {
        "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "command": "pytest " + " ".join(config.invocation_params.args),
        "passed": len(stats.get("passed", [])),
        "failed": len(stats.get("failed", [])),
        "errors": len(stats.get("error", [])),
        "skipped": len(stats.get("skipped", [])),
        "duration_s": round(time.time() - _start_time, 2) if _start_time else None,
    }
    run["total"] = run["passed"] + run["failed"] + run["errors"] + run["skipped"]
    run["status"] = "PASSED" if exitstatus == 0 else "FAILED"

    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8")) if HISTORY_FILE.exists() else []
    except ValueError:
        history = []
    history.append(run)
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history[-MAX_HISTORY:], indent=2), encoding="utf-8")
