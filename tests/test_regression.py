"""
REGRESSION TESTING
------------------
Regression testing checks that NEW changes (here: taxes, surcharges and the
testing dashboard) did not BREAK behaviour that already worked.

The values below are a frozen BASELINE taken from version 1 of the
calculator (before the upgrade) and verified by hand. If any future change
alters them, these tests fail and warn us immediately.
"""

import re
from decimal import Decimal
from pathlib import Path

import pytest

from bill_calculator import (
    REQUIRED_TARIFF_KEYS,
    TARIFFS,
    calculate_energy_charge,
    calculate_slab_charges,
    calculate_total_bill,
    check_tariff_config,
    generate_bill,
)

pytestmark = pytest.mark.regression

# (units, category, energy charge, base bill = energy + fixed)
V1_BASELINE = [
    (37,   "Residential", 111,   161),    # 37x3
    (128,  "Residential", 440,   490),    # 300 + 28x5
    (222,  "Residential", 954,   1004),   # 800 + 22x7
    (345,  "Residential", 1860,  1910),   # 1500 + 45x8
    (777,  "Residential", 5316,  5366),   # 1500 + 477x8
    (2500, "Residential", 19100, 19150),  # 1500 + 2200x8
    (37,   "Commercial",  222,   322),    # 37x6
    (128,  "Commercial",  796,   896),    # 600 + 28x7
    (222,  "Commercial",  1476,  1576),   # 1300 + 22x8
    (345,  "Commercial",  2505,  2605),   # 2100 + 45x9
    (777,  "Commercial",  6393,  6493),   # 2100 + 477x9
    (2500, "Commercial",  21900, 22000),  # 2100 + 2200x9
]


@pytest.mark.parametrize("units, category, energy, base", V1_BASELINE)
def test_v1_slab_results_unchanged(units, category, energy, base):
    assert calculate_energy_charge(units, category) == energy
    assert calculate_total_bill(units, category) == base


def test_v1_tariff_rates_unchanged():
    assert TARIFFS["Residential"]["slabs"] == [(100, 3), (200, 5), (300, 7), (None, 8)]
    assert TARIFFS["Commercial"]["slabs"] == [(100, 6), (200, 7), (300, 8), (None, 9)]
    assert TARIFFS["Residential"]["fixed_charge"] == 50
    assert TARIFFS["Commercial"]["fixed_charge"] == 100


# --- Regression for bug: KeyError 'fuel_surcharge_per_unit' in Tariff Details tab ---
def test_every_category_has_all_required_tariff_keys():
    for category, tariff in TARIFFS.items():
        assert set(REQUIRED_TARIFF_KEYS).issubset(tariff), f"{category} tariff is incomplete"


def test_all_categories_use_identical_key_names():
    key_sets = [set(tariff) for tariff in TARIFFS.values()]
    assert all(keys == key_sets[0] for keys in key_sets)


def test_configured_surcharge_and_duty_values():
    assert TARIFFS["Residential"]["fuel_surcharge_per_unit"] == Decimal("0.20")
    assert TARIFFS["Residential"]["electricity_duty_percent"] == Decimal("5")
    assert TARIFFS["Commercial"]["fuel_surcharge_per_unit"] == Decimal("0.30")
    assert TARIFFS["Commercial"]["electricity_duty_percent"] == Decimal("8")


def test_every_tariff_key_used_by_app_exists():
    """Scan app.py for t['...'] / TARIFFS[cat]['...'] lookups and check each key is configured."""
    source = (Path(__file__).resolve().parent.parent / "app.py").read_text(encoding="utf-8")
    used = set(re.findall(r"""(?:\bt|TARIFFS\[\w+\])\[["'](\w+)["']\]""", source))
    assert used, "expected app.py to read tariff keys"
    for tariff in TARIFFS.values():
        assert used.issubset(tariff), f"app.py uses keys missing from config: {used - set(tariff)}"


@pytest.mark.parametrize("broken_key", REQUIRED_TARIFF_KEYS)
def test_incomplete_tariff_is_rejected_with_clear_message(broken_key):
    broken = {"Residential": {k: v for k, v in TARIFFS["Residential"].items() if k != broken_key}}
    with pytest.raises(ValueError, match=f"missing required keys: {broken_key}"):
        check_tariff_config(broken)


@pytest.mark.parametrize("change", [
    {"slabs": [(100, 3), (200, 5)]},          # no open-ended last slab
    {"fixed_charge": -1},
    {"fuel_surcharge_per_unit": Decimal("-0.10")},
    {"electricity_duty_percent": Decimal("-5")},
])
def test_invalid_tariff_values_are_rejected(change):
    with pytest.raises(ValueError):
        check_tariff_config({"Residential": {**TARIFFS["Residential"], **change}})


def test_v1_slab_row_format_unchanged():
    """The UI depends on these exact keys - renaming one would break the slab table."""
    row = calculate_slab_charges(150, TARIFFS["Residential"]["slabs"])[0]
    assert set(row) == {"slab", "units", "rate", "amount"}


def test_v1_bill_fields_still_present():
    """Every field returned by version 1 of generate_bill() must still exist."""
    bill = generate_bill("Ravi Kumar", "EB1001", 250, "Residential")
    v1_fields = {"customer_name", "customer_id", "category", "units",
                 "slab_breakdown", "energy_charge", "fixed_charge", "total_amount"}
    assert v1_fields.issubset(bill)
    assert bill["base_amount"] == 1200      # v1 total, now kept as base_amount
