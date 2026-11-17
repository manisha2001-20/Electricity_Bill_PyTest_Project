"""
bill_calculator.py
------------------
Slab-based (progressive) electricity bill calculation.

NOTE: All rates below are ILLUSTRATIVE ACADEMIC TARIFF RATES created for a
college Software Testing project. They are NOT official electricity board rates.

How progressive slabs work (Residential, 250 units):
    First 100 units  (0-100)   x Rs.3 = Rs.300
    Next 100 units   (101-200) x Rs.5 = Rs.500
    Remaining 50     (201-300) x Rs.7 = Rs.350
    Energy charge                     = Rs.1,150
    + Fixed charge                    = Rs.50
    = Base bill                       = Rs.1,200
    + Fuel surcharge  250 x Rs.0.20   = Rs.50.00
    = Subtotal                        = Rs.1,250.00
    + Electricity duty 5% of subtotal = Rs.62.50
    = NET PAYABLE                     = Rs.1,312.50
"""

from decimal import Decimal, ROUND_HALF_UP

from validation import (
    validate_category,
    validate_customer_id,
    validate_customer_name,
    validate_units,
)

# ---------------------------------------------------------------------------
# Tariff configuration (change values here - no code changes needed elsewhere)
# Each slab is (upper_limit_in_units, rate_per_unit). None = no upper limit.
# fuel_surcharge_per_unit : extra Rs. charged on every unit consumed
# electricity_duty_percent: tax (%) on energy + fixed + fuel surcharge
# ---------------------------------------------------------------------------
TARIFFS = {
    "Residential": {
        "slabs": [(100, 3), (200, 5), (300, 7), (None, 8)],
        "fixed_charge": 50,
        "fuel_surcharge_per_unit": Decimal("0.20"),
        "electricity_duty_percent": Decimal("5"),
    },
    "Commercial": {
        "slabs": [(100, 6), (200, 7), (300, 8), (None, 9)],
        "fixed_charge": 100,
        "fuel_surcharge_per_unit": Decimal("0.30"),
        "electricity_duty_percent": Decimal("8"),
    },
}


# Every category MUST define exactly these keys (app.py and the calculations use all of them)
REQUIRED_TARIFF_KEYS = ("slabs", "fixed_charge", "fuel_surcharge_per_unit", "electricity_duty_percent")


def check_tariff_config(tariffs):
    """
    Fail fast with a clear message if any tariff is incomplete or invalid,
    instead of a confusing KeyError later in the UI.
    """
    for category, tariff in tariffs.items():
        missing = [key for key in REQUIRED_TARIFF_KEYS if key not in tariff]
        if missing:
            raise ValueError(f"Tariff '{category}' is missing required keys: {', '.join(missing)}")
        if not tariff["slabs"] or tariff["slabs"][-1][0] is not None:
            raise ValueError(f"Tariff '{category}' must end with an open-ended slab (None, rate).")
        for key in ("fixed_charge", "fuel_surcharge_per_unit", "electricity_duty_percent"):
            if tariff[key] < 0:
                raise ValueError(f"Tariff '{category}': {key} cannot be negative.")


check_tariff_config(TARIFFS)   # runs once when the module is imported


def to_money(value):
    """Round a value to 2 decimal places (paise) using normal 'round half up'."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_tariff(category):
    """Return the tariff dictionary for a (validated) category."""
    return TARIFFS[validate_category(category)]


def calculate_slab_charges(units, slabs):
    """
    Split `units` across the slabs and return one row per slab used.

    Each row: {"slab": "101-200", "units": 50, "rate": 5, "amount": 250}
    """
    breakdown = []
    lower_limit = 0      # units already covered by previous slabs

    for upper_limit, rate in slabs:
        if units <= lower_limit:
            break        # nothing left to charge

        # Units that fall inside this slab
        slab_top = units if upper_limit is None else min(units, upper_limit)
        units_in_slab = slab_top - lower_limit

        label = f"Above {lower_limit}" if upper_limit is None else f"{lower_limit + 1}-{upper_limit}"
        breakdown.append({
            "slab": label,
            "units": units_in_slab,
            "rate": rate,
            "amount": units_in_slab * rate,
        })

        if upper_limit is None:
            break
        lower_limit = upper_limit

    return breakdown


def calculate_energy_charge(units, category="Residential"):
    """Return only the energy (slab) charge, without the fixed charge."""
    units = validate_units(units)
    slabs = get_tariff(category)["slabs"]
    return sum(row["amount"] for row in calculate_slab_charges(units, slabs))


def calculate_total_bill(units, category="Residential"):
    """Return the BASE bill: energy charge + fixed charge (before surcharge and tax)."""
    tariff = get_tariff(category)
    return calculate_energy_charge(units, category) + tariff["fixed_charge"]


def calculate_charges(units, category="Residential"):
    """
    Return every component of the bill (amounts in Rs., rounded to paise):
    energy_charge, fixed_charge, fuel_surcharge, subtotal, electricity_duty, net_amount.
    """
    category = validate_category(category)
    units = validate_units(units)
    tariff = TARIFFS[category]

    breakdown = calculate_slab_charges(units, tariff["slabs"])
    energy_charge = sum(row["amount"] for row in breakdown)
    fixed_charge = tariff["fixed_charge"]

    surcharge_rate = Decimal(str(tariff["fuel_surcharge_per_unit"]))
    duty_percent = Decimal(str(tariff["electricity_duty_percent"]))

    fuel_surcharge = to_money(units * surcharge_rate)
    subtotal = to_money(energy_charge + fixed_charge + fuel_surcharge)
    electricity_duty = to_money(subtotal * duty_percent / 100)
    net_amount = to_money(subtotal + electricity_duty)

    return {
        "slab_breakdown": breakdown,
        "energy_charge": energy_charge,
        "fixed_charge": fixed_charge,
        "fuel_surcharge_rate": float(surcharge_rate),
        "fuel_surcharge": float(fuel_surcharge),
        "subtotal": float(subtotal),
        "electricity_duty_percent": float(duty_percent),
        "electricity_duty": float(electricity_duty),
        "net_amount": float(net_amount),
    }


def calculate_net_bill(units, category="Residential"):
    """Return the final payable amount including fuel surcharge and electricity duty."""
    return calculate_charges(units, category)["net_amount"]


def generate_bill(customer_name, customer_id, units, category):
    """
    Validate all customer inputs and return a complete bill as a dictionary.
    This is the single function the Streamlit frontend calls.
    """
    name = validate_customer_name(customer_name)
    cust_id = validate_customer_id(customer_id)
    category = validate_category(category)
    units = validate_units(units)

    charges = calculate_charges(units, category)

    bill = {
        "customer_name": name,
        "customer_id": cust_id,
        "category": category,
        "units": units,
    }
    bill.update(charges)
    bill["base_amount"] = charges["energy_charge"] + charges["fixed_charge"]
    bill["total_amount"] = charges["net_amount"]      # final payable amount
    return bill
