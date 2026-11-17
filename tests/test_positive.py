"""
POSITIVE TESTING
----------------
Valid inputs must produce the correct bill.

Expected values are calculated BY HAND (shown in comments) so the tests
verify the code independently instead of re-using its own logic.
Residential: 0-100 @3, 101-200 @5, 201-300 @7, >300 @8, fixed charge 50
Commercial : 0-100 @6, 101-200 @7, 201-300 @8, >300 @9, fixed charge 100
"""

import pytest

from bill_calculator import (
    calculate_energy_charge,
    calculate_slab_charges,
    calculate_total_bill,
    generate_bill,
    TARIFFS,
)

pytestmark = pytest.mark.positive


@pytest.mark.parametrize(
    "units, expected_energy, expected_total",
    [
        (50, 150, 200),     # 50x3 = 150
        (100, 300, 350),    # 100x3 = 300
        (150, 550, 600),    # 300 + 50x5 = 550
        (250, 1150, 1200),  # 300 + 500 + 50x7 = 1150
        (500, 3100, 3150),  # 300 + 500 + 700 + 200x8 = 3100
    ],
)
def test_residential_bill_for_valid_units(units, expected_energy, expected_total):
    assert calculate_energy_charge(units, "Residential") == expected_energy
    assert calculate_total_bill(units, "Residential") == expected_total


@pytest.mark.parametrize(
    "units, expected_total",
    [
        (50, 400),     # 50x6 = 300 + 100
        (250, 1800),   # 600 + 700 + 50x8 = 1700 + 100
        (500, 4000),   # 600 + 700 + 800 + 200x9 = 3900 + 100
    ],
)
def test_commercial_bill_for_valid_units(units, expected_total):
    assert calculate_total_bill(units, "Commercial") == expected_total


def test_example_from_problem_statement_250_units():
    """The worked example: 250 units -> 300 + 500 + 350 = 1150 energy charge."""
    breakdown = calculate_slab_charges(250, TARIFFS["Residential"]["slabs"])
    assert [row["amount"] for row in breakdown] == [300, 500, 350]
    assert [row["units"] for row in breakdown] == [100, 100, 50]
    assert sum(row["amount"] for row in breakdown) == 1150


def test_generate_bill_returns_complete_bill():
    bill = generate_bill("Ravi Kumar", "EB1001", 250, "Residential")
    assert bill["customer_name"] == "Ravi Kumar"
    assert bill["customer_id"] == "EB1001"
    assert bill["category"] == "Residential"
    assert bill["units"] == 250
    assert bill["energy_charge"] == 1150
    assert bill["fixed_charge"] == 50
    assert bill["base_amount"] == 1200          # 1150 + 50
    assert bill["fuel_surcharge"] == 50.00      # 250 x 0.20
    assert bill["electricity_duty"] == 62.50    # 1250 x 5%
    assert bill["total_amount"] == 1312.50      # 1250 + 62.50
    assert len(bill["slab_breakdown"]) == 3


def test_generate_bill_slab_labels_for_high_consumption():
    bill = generate_bill("Asha", "EB2002", 500, "Residential")
    labels = [row["slab"] for row in bill["slab_breakdown"]]
    assert labels == ["1-100", "101-200", "201-300", "Above 300"]


def test_generate_bill_normalises_inputs():
    """Messy but valid inputs are cleaned: spaces, lowercase ID/category, numeric string."""
    bill = generate_bill("  Priya   Sharma ", " eb12345 ", " 150 ", "commercial")
    assert bill["customer_name"] == "Priya Sharma"
    assert bill["customer_id"] == "EB12345"
    assert bill["category"] == "Commercial"
    assert bill["units"] == 150
    assert bill["base_amount"] == 1050    # 600 + 50x7 = 950 + 100
    # surcharge 150 x 0.30 = 45 ; subtotal 1095 ; duty 8% = 87.60
    assert bill["total_amount"] == 1182.60
