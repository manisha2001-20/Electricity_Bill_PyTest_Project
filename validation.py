"""
validation.py
-------------
Input validation for the Electricity Bill Calculator.

Every value that comes from the user (name, customer ID, units, category)
passes through one of these functions BEFORE any calculation happens.
If a value is invalid, a clear custom exception is raised with a message
that can be shown directly to the user.

Exception hierarchy (useful for exception-handling tests):

    BillValidationError (ValueError)
    ├── InvalidUnitsError       -> bad electricity consumption
    ├── InvalidCustomerError    -> bad customer name / customer ID
    └── InvalidCategoryError    -> category is not Residential / Commercial
"""

import math
import re

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_UNITS = 100_000                      # sanity upper limit for one bill
VALID_CATEGORIES = ("Residential", "Commercial")
CUSTOMER_ID_PATTERN = re.compile(r"^EB\d{4,8}$")         # e.g. EB1001
CUSTOMER_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .]{1,49}$")


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class BillValidationError(ValueError):
    """Base class for every validation error in this project."""


class InvalidUnitsError(BillValidationError):
    """Raised when electricity units are missing, non-numeric or out of range."""


class InvalidCustomerError(BillValidationError):
    """Raised when the customer name or customer ID is invalid."""


class InvalidCategoryError(BillValidationError):
    """Raised when the customer category is not supported."""


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------
def validate_units(units):
    """
    Validate electricity consumption and return it as an int.

    Accepts: a whole number (int), a float with no fractional part (e.g. 150.0),
             or a numeric string (e.g. "150", " 150 ").
    Rejects: None, empty strings, text, booleans, decimals, negatives,
             NaN/infinity and values above MAX_UNITS.
    """
    # 1. Null / missing value
    if units is None:
        raise InvalidUnitsError("Units cannot be empty. Please enter electricity units consumed.")

    # 2. bool is a subclass of int in Python, so reject it explicitly
    if isinstance(units, bool):
        raise InvalidUnitsError("Units must be a number, not True/False.")

    # 3. Convert strings to numbers
    if isinstance(units, str):
        text = units.strip()
        if text == "":
            raise InvalidUnitsError("Units cannot be empty. Please enter electricity units consumed.")
        try:
            units = int(text)
        except ValueError:
            try:
                units = float(text)
            except ValueError:
                raise InvalidUnitsError(f"Units must be numeric. '{text}' is not a valid number.") from None

    # 4. Floats are allowed only if they are whole numbers (meter readings are whole kWh)
    if isinstance(units, float):
        if math.isnan(units) or math.isinf(units):
            raise InvalidUnitsError("Units must be a finite number.")
        if not units.is_integer():
            raise InvalidUnitsError("Units must be a whole number (e.g. 150, not 150.5).")
        units = int(units)

    # 5. Anything else (list, dict, ...) is not acceptable
    if not isinstance(units, int):
        raise InvalidUnitsError(f"Units must be a number, got {type(units).__name__}.")

    # 6. Range checks
    if units < 0:
        raise InvalidUnitsError("Units cannot be negative.")
    if units > MAX_UNITS:
        raise InvalidUnitsError(f"Units cannot exceed {MAX_UNITS:,} for a single bill.")

    return units


def validate_customer_name(name):
    """Return the cleaned customer name, or raise InvalidCustomerError."""
    if name is None or not isinstance(name, str) or name.strip() == "":
        raise InvalidCustomerError("Customer name cannot be empty.")
    name = " ".join(name.split())        # collapse extra spaces
    if not CUSTOMER_NAME_PATTERN.match(name):
        raise InvalidCustomerError(
            "Customer name must be 2-50 characters and contain only letters, spaces and dots."
        )
    return name


def validate_customer_id(customer_id):
    """
    Return the customer ID in upper case, or raise InvalidCustomerError.
    Valid format: 'EB' followed by 4 to 8 digits, e.g. EB1001 or eb20250001.
    """
    if customer_id is None or not isinstance(customer_id, str) or customer_id.strip() == "":
        raise InvalidCustomerError("Customer ID cannot be empty.")
    customer_id = customer_id.strip().upper()
    if not CUSTOMER_ID_PATTERN.match(customer_id):
        raise InvalidCustomerError(
            "Customer ID must be 'EB' followed by 4 to 8 digits (e.g. EB1001)."
        )
    return customer_id


def validate_category(category):
    """Return the category in canonical form ('Residential'/'Commercial')."""
    if category is None or not isinstance(category, str) or category.strip() == "":
        raise InvalidCategoryError("Customer category cannot be empty.")
    cleaned = category.strip().capitalize()
    if cleaned not in VALID_CATEGORIES:
        raise InvalidCategoryError(
            f"Invalid category '{category}'. Choose one of: {', '.join(VALID_CATEGORIES)}."
        )
    return cleaned
