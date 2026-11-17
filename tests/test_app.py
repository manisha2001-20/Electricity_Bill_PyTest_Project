"""
FRONTEND INTEGRATION TESTS
--------------------------
Uses Streamlit's built-in testing tool (AppTest) to run app.py headlessly,
fill in the form, click "Calculate Bill" and check what the user would see.
This proves the frontend is correctly connected to bill_calculator.py.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.frontend

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def submit_form(name, customer_id, units, category="Residential"):
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    at.text_input(key="name").input(name)
    at.text_input(key="customer_id").input(customer_id)
    at.selectbox(key="category").select(category)
    at.text_input(key="units").input(units)
    next(b for b in at.button if b.label == "Calculate Bill").click().run()
    return at


def test_app_loads_without_errors():
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not at.exception
    assert "Electricity Bill Calculator" in at.title[0].value
    assert [t.label for t in at.tabs] == ["🧾 Bill Calculator", "📘 Tariff Details", "🧪 Testing Dashboard"]


def test_app_shows_correct_bill_for_valid_input():
    at = submit_form("Ravi Kumar", "EB1001", "250")
    assert not at.exception
    assert len(at.error) == 0
    assert "calculated successfully" in at.success[0].value
    page_html = " ".join(m.value for m in at.markdown)
    assert "₹1,312.50" in page_html        # 1150 + 50 + 50.00 surcharge + 62.50 duty


def test_app_shows_error_for_invalid_units():
    at = submit_form("Ravi Kumar", "EB1001", "abc")
    assert not at.exception
    assert "must be numeric" in at.error[0].value


def test_app_shows_error_for_invalid_customer_id():
    at = submit_form("Ravi Kumar", "1234", "100")
    assert "Customer ID" in at.error[0].value


def test_tariff_details_tab_shows_surcharge_and_duty():
    """Regression: this tab crashed with KeyError 'fuel_surcharge_per_unit'."""
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not at.exception
    tariff_text = " ".join(m.value for m in at.tabs[1].markdown)
    assert "Fuel surcharge: **₹0.20**" in tariff_text      # Residential
    assert "Fuel surcharge: **₹0.30**" in tariff_text      # Commercial
    assert "Electricity duty: **5%**" in tariff_text
    assert "Electricity duty: **8%**" in tariff_text


def test_testing_dashboard_renders_without_errors():
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not at.exception
    assert any("Testing Dashboard" in s.value for s in at.subheader)
