"""
TAX & SURCHARGE TESTING
-----------------------
Residential: fuel surcharge Rs.0.20/unit, electricity duty 5%
Commercial : fuel surcharge Rs.0.30/unit, electricity duty 8%
    subtotal = energy + fixed + units x surcharge
    duty     = subtotal x duty%            (rounded to paise, half-up)
    net      = subtotal + duty
All expected values are calculated by hand.
"""

from decimal import Decimal

import pytest

import bill_calculator
from bill_calculator import calculate_charges, calculate_net_bill, to_money

pytestmark = pytest.mark.taxes


@pytest.mark.parametrize(
    "units, category, surcharge, subtotal, duty, net",
    [
        # 1150 + 50 + 50.00 = 1250.00 ; 5% = 62.50
        (250, "Residential", 50.00, 1250.00, 62.50, 1312.50),
        # 1700 + 100 + 75.00 = 1875.00 ; 8% = 150.00
        (250, "Commercial", 75.00, 1875.00, 150.00, 2025.00),
        # 0 units: only fixed charge is taxed. 50 x 5% = 2.50
        (0, "Residential", 0.00, 50.00, 2.50, 52.50),
        # 0 units commercial: 100 x 8% = 8.00
        (0, "Commercial", 0.00, 100.00, 8.00, 108.00),
    ],
)
def test_full_charge_breakdown(units, category, surcharge, subtotal, duty, net):
    charges = calculate_charges(units, category)
    assert charges["fuel_surcharge"] == surcharge
    assert charges["subtotal"] == subtotal
    assert charges["electricity_duty"] == duty
    assert charges["net_amount"] == net


@pytest.mark.parametrize(
    "units, expected_net",
    [
        (1, 114.80),   # 6+100+0.30 = 106.30 ; 8% = 8.504 -> 8.50 (rounded down)
        (3, 128.41),   # 18+100+0.90 = 118.90 ; 8% = 9.512 -> 9.51
        (7, 155.63),   # 42+100+2.10 = 144.10 ; 8% = 11.528 -> 11.53 (rounded up)
    ],
)
def test_duty_is_rounded_to_paise(units, expected_net):
    assert calculate_net_bill(units, "Commercial") == expected_net


def test_to_money_rounds_half_up():
    assert to_money("2.665") == Decimal("2.67")    # float round(2.665, 2) gives 2.66 - a classic money bug
    assert to_money("2.664") == Decimal("2.66")
    assert to_money(10) == Decimal("10.00")


def test_net_bill_is_always_greater_than_base_bill():
    for units in (0, 50, 250, 900):
        charges = calculate_charges(units)
        assert charges["net_amount"] > charges["energy_charge"] + charges["fixed_charge"]


def test_tax_rates_are_configurable(monkeypatch):
    """Changing only the configuration changes the bill - no code changes needed."""
    monkeypatch.setitem(bill_calculator.TARIFFS["Residential"], "electricity_duty_percent", Decimal("0"))
    monkeypatch.setitem(bill_calculator.TARIFFS["Residential"], "fuel_surcharge_per_unit", Decimal("0"))
    # With no tax or surcharge, net bill == old base bill (1150 + 50)
    assert calculate_net_bill(250, "Residential") == 1200.00


def test_increased_duty_rate_is_applied(monkeypatch):
    monkeypatch.setitem(bill_calculator.TARIFFS["Residential"], "electricity_duty_percent", Decimal("10"))
    # subtotal 1250.00 ; 10% = 125.00
    assert calculate_net_bill(250, "Residential") == 1375.00
