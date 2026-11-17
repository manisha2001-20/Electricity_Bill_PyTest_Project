"""
VALIDATION FUNCTION TESTS
-------------------------
Direct unit tests for each function in validation.py, covering both
accepted values (and how they are cleaned) and rejected values.
"""

import pytest

from validation import (
    InvalidCategoryError,
    InvalidCustomerError,
    InvalidUnitsError,
    validate_category,
    validate_customer_id,
    validate_customer_name,
    validate_units,
)

pytestmark = pytest.mark.validation


# --- validate_units --------------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [(0, 0), (250, 250), ("250", 250), ("  42 ", 42), (300.0, 300), ("75.0", 75)],
)
def test_validate_units_accepts_and_converts(raw, expected):
    result = validate_units(raw)
    assert result == expected
    assert isinstance(result, int)


@pytest.mark.parametrize("raw", [None, "", "-5", "xyz", 2.5, True, [1]])
def test_validate_units_rejects_invalid(raw):
    with pytest.raises(InvalidUnitsError):
        validate_units(raw)


# --- validate_customer_name ------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [("Ravi", "Ravi"), ("  Ravi   Kumar  ", "Ravi Kumar"), ("Dr. A. Rao", "Dr. A. Rao")],
)
def test_validate_customer_name_accepts_and_cleans(raw, expected):
    assert validate_customer_name(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "A", "Ravi123", "R@vi", 12345, "A" * 51])
def test_validate_customer_name_rejects_invalid(raw):
    with pytest.raises(InvalidCustomerError):
        validate_customer_name(raw)


# --- validate_customer_id --------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [("EB1001", "EB1001"), ("eb1001", "EB1001"), (" EB12345678 ", "EB12345678")],
)
def test_validate_customer_id_accepts_and_normalises(raw, expected):
    assert validate_customer_id(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "EB123", "EB123456789", "AB1001", 1001])
def test_validate_customer_id_rejects_invalid(raw):
    with pytest.raises(InvalidCustomerError):
        validate_customer_id(raw)


# --- validate_category -----------------------------------------------------
@pytest.mark.parametrize(
    "raw, expected",
    [("Residential", "Residential"), ("residential", "Residential"),
     (" COMMERCIAL ", "Commercial"), ("commercial", "Commercial")],
)
def test_validate_category_accepts_and_normalises(raw, expected):
    assert validate_category(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "Industrial", "Resident", 1])
def test_validate_category_rejects_invalid(raw):
    with pytest.raises(InvalidCategoryError):
        validate_category(raw)
