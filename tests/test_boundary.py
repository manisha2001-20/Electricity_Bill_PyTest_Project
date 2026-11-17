"""
BOUNDARY VALUE ANALYSIS (BVA)
-----------------------------
Bugs often hide at the edges of ranges (e.g. using < instead of <=).
We test each slab boundary (100, 200, 300) plus the values just below
and just above it, and the lower boundary 0/1.

Residential: 0-100 @3, 101-200 @5, 201-300 @7, >300 @8, fixed 50
"""

import pytest

from bill_calculator import calculate_energy_charge, calculate_net_bill, calculate_total_bill
from validation import InvalidUnitsError, MAX_UNITS

pytestmark = pytest.mark.boundary


@pytest.mark.parametrize(
    "units, expected_energy, expected_total",
    [
        (0,   0,    50),     # no consumption: fixed charge only
        (1,   3,    53),     # 1x3
        (99,  297,  347),    # 99x3
        (100, 300,  350),    # 100x3            (end of slab 1)
        (101, 305,  355),    # 300 + 1x5        (start of slab 2)
        (199, 795,  845),    # 300 + 99x5
        (200, 800,  850),    # 300 + 100x5      (end of slab 2)
        (201, 807,  857),    # 800 + 1x7        (start of slab 3)
        (299, 1493, 1543),   # 800 + 99x7
        (300, 1500, 1550),   # 800 + 100x7      (end of slab 3)
        (301, 1508, 1558),   # 1500 + 1x8       (start of slab 4)
    ],
)
def test_residential_slab_boundaries(units, expected_energy, expected_total):
    assert calculate_energy_charge(units, "Residential") == expected_energy
    assert calculate_total_bill(units, "Residential") == expected_total


@pytest.mark.parametrize(
    "units, expected_energy",
    [
        (100, 600),    # 100x6
        (101, 607),    # 600 + 1x7
        (200, 1300),   # 600 + 700
        (201, 1308),   # 1300 + 1x8
        (300, 2100),   # 1300 + 800
        (301, 2109),   # 2100 + 1x9
    ],
)
def test_commercial_slab_boundaries(units, expected_energy):
    assert calculate_energy_charge(units, "Commercial") == expected_energy


@pytest.mark.parametrize(
    "units, expected_net",
    [
        # Residential net = (energy + 50 + units x 0.20) x 1.05
        (0,   52.50),     # 50.00 + 2.50
        (1,   55.86),     # 53.20 + 2.66
        (99,  385.14),    # 366.80 + 18.34
        (100, 388.50),    # 370.00 + 18.50
        (101, 393.96),    # 375.20 + 18.76
        (199, 929.04),    # 884.80 + 44.24
        (200, 934.50),    # 890.00 + 44.50
        (201, 942.06),    # 897.20 + 44.86
        (299, 1682.94),   # 1602.80 + 80.14
        (300, 1690.50),   # 1610.00 + 80.50
        (301, 1699.11),   # 1618.20 + 80.91
    ],
)
def test_residential_net_bill_at_boundaries(units, expected_net):
    """Same boundaries, but checking the FINAL payable amount including surcharge and duty."""
    assert calculate_net_bill(units, "Residential") == expected_net


@pytest.mark.parametrize(
    "units, expected_net",
    [
        # Commercial net = (energy + 100 + units x 0.30) x 1.08
        (100, 788.40),    # 730.00 + 58.40
        (101, 796.28),    # 737.30 + 58.98
        (300, 2473.20),   # 2290.00 + 183.20
        (301, 2483.24),   # 2299.30 + 183.94
    ],
)
def test_commercial_net_bill_at_boundaries(units, expected_net):
    assert calculate_net_bill(units, "Commercial") == expected_net


@pytest.mark.parametrize(
    "units, expected_net",
    [
        (1000,  7717.50),     # (7100 + 50 + 200.00) = 7350.00 + 367.50
        (5000,  42157.50),    # (39100 + 50 + 1000.00) = 40150.00 + 2007.50
        (99999, 860098.89),   # (799092 + 50 + 19999.80) = 819141.80 + 40957.09
    ],
)
def test_high_consumption_values(units, expected_net):
    assert calculate_net_bill(units, "Residential") == expected_net


def test_rate_changes_exactly_at_each_boundary():
    """The cost of ONE extra unit must jump to the next slab's rate right after the boundary."""
    def cost_of_unit(n):
        return calculate_energy_charge(n) - calculate_energy_charge(n - 1)

    assert cost_of_unit(100) == 3 and cost_of_unit(101) == 5
    assert cost_of_unit(200) == 5 and cost_of_unit(201) == 7
    assert cost_of_unit(300) == 7 and cost_of_unit(301) == 8


# --- Lower and upper limits of the valid input range -----------------------
def test_minus_one_is_just_below_valid_range():
    with pytest.raises(InvalidUnitsError):
        calculate_total_bill(-1)


def test_maximum_allowed_units_is_accepted():
    # 1500 + (100000 - 300) x 8 = 1500 + 797600 = 799100 (+50 fixed)
    assert calculate_total_bill(MAX_UNITS) == 799_150


def test_one_above_maximum_is_rejected():
    with pytest.raises(InvalidUnitsError, match="cannot exceed"):
        calculate_total_bill(MAX_UNITS + 1)
