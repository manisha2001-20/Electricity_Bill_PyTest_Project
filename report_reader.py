"""
report_reader.py
----------------
Reads the REAL result files produced by pytest so the Streamlit Testing
Dashboard can display them. Nothing here invents numbers: if a file does
not exist yet, the functions return None / [] and the dashboard tells the
user to run the tests first.

Files read (all written automatically by `pytest`, see pytest.ini):
    reports/junit_results.xml  -> every test case and its pass/fail status
    reports/coverage.json      -> code coverage percentage
    reports/test_history.json  -> one summary line per test run (tests/conftest.py)
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
JUNIT_FILE = REPORTS_DIR / "junit_results.xml"
COVERAGE_FILE = REPORTS_DIR / "coverage.json"
HISTORY_FILE = REPORTS_DIR / "test_history.json"
HTML_REPORT_FILE = REPORTS_DIR / "test_report.html"

# Which testing technique each test file demonstrates
TECHNIQUE_BY_FILE = {
    "test_positive": "Positive Testing",
    "test_negative": "Negative & Exception Testing",
    "test_boundary": "Boundary Value Analysis",
    "test_equivalence": "Equivalence Partitioning",
    "test_validation": "Validation Unit Testing",
    "test_taxes": "Tax & Surcharge Testing",
    "test_regression": "Regression Testing",
    "test_integration": "Integration Testing",
    "test_report_reader": "Dashboard Reader Testing",
    "test_app": "Frontend (UI) Testing",
}


def technique_for(classname):
    """Map a JUnit classname such as 'tests.test_boundary' to a technique name."""
    module = classname.split(".")[-1]
    return TECHNIQUE_BY_FILE.get(module, "Other")


def load_junit_results(path=JUNIT_FILE):
    """
    Parse a JUnit XML file. Returns None if the file is missing or unreadable,
    otherwise {"summary": {...}, "cases": [ {...}, ... ]}.
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None

    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return None

    cases = []
    for case in suite.iter("testcase"):
        if case.find("failure") is not None:
            status = "failed"
        elif case.find("error") is not None:
            status = "error"
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"
        classname = case.get("classname", "")
        cases.append({
            "file": classname.split(".")[-1],
            "technique": technique_for(classname),
            "name": case.get("name", ""),
            "time": float(case.get("time", 0) or 0),
            "status": status,
        })

    def count(status):
        return sum(1 for c in cases if c["status"] == status)

    summary = {
        "total": len(cases),
        "passed": count("passed"),
        "failed": count("failed"),
        "errors": count("error"),
        "skipped": count("skipped"),
        "duration": float(suite.get("time", 0) or 0),
        "timestamp": suite.get("timestamp", ""),
    }
    summary["status"] = "PASSED" if summary["failed"] == 0 and summary["errors"] == 0 else "FAILED"
    return {"summary": summary, "cases": cases}


def technique_distribution(cases):
    """Count test cases per testing technique, largest first."""
    counts = {}
    for case in cases:
        counts[case["technique"]] = counts.get(case["technique"], 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def load_coverage(path=COVERAGE_FILE):
    """Return {"percent": float, "files": {name: percent}, "timestamp": str} or None."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "percent": round(data["totals"]["percent_covered"], 2),
            "files": {name: round(info["summary"]["percent_covered"], 2)
                      for name, info in data["files"].items()},
            "timestamp": data.get("meta", {}).get("timestamp", ""),
        }
    except (ValueError, KeyError):
        return None


def load_history(path=HISTORY_FILE):
    """Return the list of recorded test runs, newest first ([] if none)."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        runs = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return []
    return list(reversed(runs)) if isinstance(runs, list) else []
