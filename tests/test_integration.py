"""
INTEGRATION TESTING
-------------------
Unit tests check each function alone. Integration tests check that the
validation module and the calculation module WORK TOGETHER correctly
through generate_bill(), the function the frontend uses.
"""

import pytest

import bill_calculator
from bill_calculator import generate_bill
from validation import InvalidCustomerError, InvalidUnitsError

pytestmark = pytest.mark.integration


def test_raw_user_input_flows_through_validation_into_calculation():
    """Messy text (as typed in the UI) is cleaned by validation, then billed correctly."""
    bill = generate_bill("  meena  devi ", "eb4321", " 301 ", " residential ")
    assert bill["customer_id"] == "EB4321"
    assert bill["category"] == "Residential"
    assert bill["units"] == 301
    assert bill["energy_charge"] == 1508           # 1500 + 1x8
    assert bill["net_amount"] == 1699.11           # (1508+50+60.20) x 1.05


def test_calculation_is_never_called_when_validation_fails(monkeypatch):
    """Invalid input must be stopped by validation BEFORE any calculation happens."""
    calls = []
    monkeypatch.setattr(bill_calculator, "calculate_slab_charges",
                        lambda *args: calls.append(args) or [])
    with pytest.raises(InvalidUnitsError):
        generate_bill("Ravi Kumar", "EB1001", "-20", "Residential")
    with pytest.raises(InvalidCustomerError):
        generate_bill("Ravi Kumar", "WRONG", 100, "Residential")
    assert calls == []


@pytest.mark.parametrize("units, category", [(0, "Residential"), (150, "Commercial"),
                                             (301, "Residential"), (4321, "Commercial")])
def test_bill_components_add_up_to_total(units, category):
    """Slab units sum to consumption, slab amounts sum to energy, components sum to total."""
    bill = generate_bill("Test User", "EB9999", units, category)
    assert sum(r["units"] for r in bill["slab_breakdown"]) == units
    assert sum(r["amount"] for r in bill["slab_breakdown"]) == bill["energy_charge"]
    assert bill["subtotal"] == pytest.approx(
        bill["energy_charge"] + bill["fixed_charge"] + bill["fuel_surcharge"])
    assert bill["total_amount"] == pytest.approx(bill["subtotal"] + bill["electricity_duty"])


def test_same_units_cost_more_for_commercial_than_residential():
    res = generate_bill("Asha", "EB1111", 250, "Residential")
    com = generate_bill("Asha", "EB1111", 250, "Commercial")
    assert com["total_amount"] > res["total_amount"]    # 2025.00 > 1312.50
