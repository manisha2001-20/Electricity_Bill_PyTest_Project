"""
EQUIVALENCE PARTITIONING (EP)
-----------------------------
Inputs are divided into classes (partitions) that the program should treat
the same way. Testing one or a few representatives from each class gives
good coverage with fewer test cases.

  Partition                     Representatives            Expected
  ----------------------------  -------------------------  --------------
  P1 Valid consumption          0, 45, 160, 275, 1000      Bill calculated
  P2 Invalid negative values    -1, -75, -9999             InvalidUnitsError
  P3 Invalid non-numeric        "abc", "ten", "5kWh"       InvalidUnitsError
  P4 Empty / missing values     None, "", "   "            InvalidUnitsError

Valid partition is further split by slab (one representative per slab).
"""

import pytest

from bill_calculator import calculate_total_bill
from validation import InvalidUnitsError

pytestmark = pytest.mark.equivalence


# P1 - Valid consumption: one representative from each slab
@pytest.mark.parametrize(
    "units, expected_total",
    [
        (0, 50),       # zero-consumption class: fixed charge only
        (45, 185),     # slab 1: 45x3 = 135 + 50
        (160, 650),    # slab 2: 300 + 60x5 = 600 + 50
        (275, 1375),   # slab 3: 800 + 75x7 = 1325 + 50
        (1000, 7150),  # slab 4: 1500 + 700x8 = 7100 + 50
    ],
)
def test_partition_valid_consumption(units, expected_total):
    assert calculate_total_bill(units) == expected_total


# P2 - Invalid negative values
@pytest.mark.parametrize("units", [-1, -75, -9999])
def test_partition_negative_values(units):
    with pytest.raises(InvalidUnitsError, match="negative"):
        calculate_total_bill(units)


# P3 - Invalid non-numeric values
@pytest.mark.parametrize("units", ["abc", "ten", "5kWh"])
def test_partition_non_numeric_values(units):
    with pytest.raises(InvalidUnitsError, match="numeric"):
        calculate_total_bill(units)


# P4 - Empty or missing values
@pytest.mark.parametrize("units", [None, "", "   "])
def test_partition_empty_or_missing_values(units):
    with pytest.raises(InvalidUnitsError, match="empty"):
        calculate_total_bill(units)


# Valid partition, different input FORMATS must give the same result
@pytest.mark.parametrize("units", [160, "160", " 160 ", 160.0, "160.0"])
def test_equivalent_formats_give_same_bill(units):
    assert calculate_total_bill(units) == 650
