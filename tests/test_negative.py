"""
NEGATIVE TESTING + EXCEPTION HANDLING
-------------------------------------
Invalid inputs must be REJECTED with the correct exception type and a
meaningful error message. `pytest.raises(..., match=...)` checks both.
"""

import pytest

from bill_calculator import calculate_total_bill, generate_bill
from validation import (
    BillValidationError,
    InvalidCategoryError,
    InvalidCustomerError,
    InvalidUnitsError,
)

pytestmark = pytest.mark.negative


# --- Negative units --------------------------------------------------------
@pytest.mark.parametrize("units", [-1, -50, -1000, "-10"])
def test_negative_units_are_rejected(units):
    with pytest.raises(InvalidUnitsError, match="cannot be negative"):
        calculate_total_bill(units)


# --- Text instead of numbers -----------------------------------------------
@pytest.mark.parametrize("units", ["abc", "hundred", "12a", "1,000", "@#$"])
def test_text_units_are_rejected(units):
    with pytest.raises(InvalidUnitsError, match="must be numeric"):
        calculate_total_bill(units)


# --- Empty input -----------------------------------------------------------
@pytest.mark.parametrize("units", ["", "   "])
def test_empty_units_are_rejected(units):
    with pytest.raises(InvalidUnitsError, match="cannot be empty"):
        calculate_total_bill(units)


# --- Null values -----------------------------------------------------------
def test_null_units_are_rejected():
    with pytest.raises(InvalidUnitsError, match="cannot be empty"):
        calculate_total_bill(None)


def test_null_customer_name_is_rejected():
    with pytest.raises(InvalidCustomerError, match="name cannot be empty"):
        generate_bill(None, "EB1001", 100, "Residential")


def test_null_customer_id_is_rejected():
    with pytest.raises(InvalidCustomerError, match="ID cannot be empty"):
        generate_bill("Ravi", None, 100, "Residential")


def test_null_category_is_rejected():
    with pytest.raises(InvalidCategoryError, match="cannot be empty"):
        generate_bill("Ravi", "EB1001", 100, None)


# --- Invalid customer category ---------------------------------------------
@pytest.mark.parametrize("category", ["Industrial", "Agriculture", "res", "123"])
def test_invalid_category_is_rejected(category):
    with pytest.raises(InvalidCategoryError, match="Invalid category"):
        calculate_total_bill(100, category)


# --- Invalid customer ID ---------------------------------------------------
@pytest.mark.parametrize(
    "customer_id",
    ["1001", "EB12", "EB123456789", "XY1001", "EB10A1", "EB 1001", "EB-1001"],
)
def test_invalid_customer_id_is_rejected(customer_id):
    with pytest.raises(InvalidCustomerError, match="must be 'EB' followed by"):
        generate_bill("Ravi Kumar", customer_id, 100, "Residential")


# --- Invalid units types / values ------------------------------------------
@pytest.mark.parametrize("units", [12.5, "99.9"])
def test_decimal_units_are_rejected(units):
    with pytest.raises(InvalidUnitsError, match="whole number"):
        calculate_total_bill(units)


@pytest.mark.parametrize("units", [True, False, [100], {"units": 100}])
def test_wrong_type_units_are_rejected(units):
    with pytest.raises(InvalidUnitsError, match="must be a number"):
        calculate_total_bill(units)


@pytest.mark.parametrize("units", [float("nan"), float("inf")])
def test_nan_and_infinity_are_rejected(units):
    with pytest.raises(InvalidUnitsError, match="finite"):
        calculate_total_bill(units)


# --- Exception hierarchy ---------------------------------------------------
@pytest.mark.parametrize(
    "args",
    [
        ("Ravi", "EB1001", -5, "Residential"),     # bad units
        ("", "EB1001", 100, "Residential"),        # bad name
        ("Ravi", "BAD", 100, "Residential"),       # bad ID
        ("Ravi", "EB1001", 100, "Industrial"),     # bad category
    ],
)
def test_all_validation_errors_share_one_base_class(args):
    """The UI catches BillValidationError, so every error must inherit from it (and ValueError)."""
    with pytest.raises(BillValidationError):
        generate_bill(*args)
    with pytest.raises(ValueError):
        generate_bill(*args)
