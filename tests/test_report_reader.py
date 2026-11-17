"""
DASHBOARD REPORT READER TESTS
-----------------------------
The Testing Dashboard must show ONLY real results. These tests feed small
sample report files (written to a temporary folder) into report_reader.py
and check they are counted correctly - and that missing files give "no data"
instead of made-up numbers.
"""

import json

import pytest

from report_reader import (
    load_coverage,
    load_history,
    load_junit_results,
    technique_distribution,
    technique_for,
)

pytestmark = pytest.mark.reports

SAMPLE_JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="1" skipped="1" tests="4"
 time="1.25" timestamp="2026-11-13T12:00:00">
  <testcase classname="tests.test_boundary" name="test_a" time="0.01"/>
  <testcase classname="tests.test_boundary" name="test_b" time="0.02"/>
  <testcase classname="tests.test_positive" name="test_c" time="0.01"><failure message="x"/></testcase>
  <testcase classname="tests.test_negative" name="test_d" time="0.00"><skipped message="y"/></testcase>
</testsuite></testsuites>"""


def test_junit_results_are_counted_correctly(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(SAMPLE_JUNIT, encoding="utf-8")
    result = load_junit_results(path)
    s = result["summary"]
    assert (s["total"], s["passed"], s["failed"], s["skipped"]) == (4, 2, 1, 1)
    assert s["status"] == "FAILED"
    assert s["duration"] == 1.25
    assert result["cases"][2]["technique"] == "Positive Testing"


def test_technique_distribution_counts_and_sorts(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(SAMPLE_JUNIT, encoding="utf-8")
    dist = technique_distribution(load_junit_results(path)["cases"])
    assert list(dist.items())[0] == ("Boundary Value Analysis", 2)
    assert sum(dist.values()) == 4


def test_coverage_json_is_read(tmp_path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({
        "meta": {"timestamp": "2026-11-13T12:00:00"},
        "totals": {"percent_covered": 97.456},
        "files": {"validation.py": {"summary": {"percent_covered": 100.0}}},
    }), encoding="utf-8")
    cov = load_coverage(path)
    assert cov["percent"] == 97.46
    assert cov["files"]["validation.py"] == 100.0


def test_history_is_returned_newest_first(tmp_path):
    path = tmp_path / "history.json"
    path.write_text(json.dumps([{"run_at": "first"}, {"run_at": "second"}]), encoding="utf-8")
    assert [run["run_at"] for run in load_history(path)] == ["second", "first"]


def test_missing_files_return_no_data_instead_of_fake_results(tmp_path):
    missing = tmp_path / "does_not_exist"
    assert load_junit_results(missing) is None
    assert load_coverage(missing) is None
    assert load_history(missing) == []


def test_corrupt_files_are_handled_safely(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("this is not xml or json", encoding="utf-8")
    assert load_junit_results(bad) is None
    assert load_coverage(bad) is None
    assert load_history(bad) == []


def test_crashed_tests_are_reported_as_errors(tmp_path):
    """A test that crashes (error, not assertion failure) must also mark the run FAILED."""
    path = tmp_path / "junit.xml"
    path.write_text('<testsuite time="0.5"><testcase classname="tests.test_taxes" name="t">'
                    '<error message="boom"/></testcase></testsuite>', encoding="utf-8")
    s = load_junit_results(path)["summary"]
    assert (s["total"], s["errors"], s["status"]) == (1, 1, "FAILED")


def test_xml_without_testsuite_gives_no_data(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text("<testsuites></testsuites>", encoding="utf-8")
    assert load_junit_results(path) is None


def test_unknown_test_file_maps_to_other():
    assert technique_for("tests.test_boundary") == "Boundary Value Analysis"
    assert technique_for("tests.test_something_new") == "Other"
