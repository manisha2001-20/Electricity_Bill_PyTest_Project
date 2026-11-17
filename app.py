"""
app.py
------
Streamlit dashboard for the Electricity Bill Calculator.

Tabs:
  1. Bill Calculator    - customer form, slab-wise breakdown, tax breakdown, final bill
  2. Tariff Details     - Residential & Commercial slabs, fixed charges, taxes
  3. Testing Dashboard  - REAL pytest results read from the reports/ folder

The UI contains NO calculation logic. It only collects inputs, calls
`generate_bill()` from bill_calculator.py and displays the result, so all
business logic stays testable with PyTest.

Run with:  streamlit run app.py
"""

import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import report_reader
from bill_calculator import TARIFFS, generate_bill
from validation import BillValidationError, VALID_CATEGORIES

PROJECT_DIR = Path(__file__).resolve().parent
ACCENT = "#0f766e"

st.set_page_config(page_title="Electricity Bill Calculator", page_icon="⚡", layout="wide")

st.markdown(
    f"""
    <style>
    .block-container {{padding-top: 2rem; max-width: 1200px;}}
    .total-box {{background: {ACCENT}; color: #ffffff; padding: 1.2rem 1.5rem;
                border-radius: 12px; margin-top: 0.5rem;}}
    .total-box .label {{font-size: 0.95rem; opacity: 0.9;}}
    .total-box .amount {{font-size: 2.2rem; font-weight: 700;}}
    div[data-testid="stMetric"] {{border: 1px solid rgba(128,128,128,0.25);
                border-radius: 10px; padding: 0.6rem 0.9rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def format_rupees(amount):
    """Format a number as Indian Rupees, e.g. 1150 -> '₹1,150.00'."""
    return f"₹{amount:,.2f}"


def tariff_table(category):
    """Build a small table describing the slabs of one category."""
    rows, lower = [], 0
    for upper, rate in TARIFFS[category]["slabs"]:
        label = f"Above {lower}" if upper is None else f"{lower + 1} – {upper}"
        rows.append({"Units slab": label, "Rate (₹/unit)": rate})
        lower = upper if upper is not None else lower
    return pd.DataFrame(rows)


def run_test_suite():
    """Run the real pytest suite in a separate process and return its output."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider"],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=600,
    )
    return result.returncode, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# Header + sidebar
# ---------------------------------------------------------------------------
st.title("⚡ Electricity Bill Calculator")
st.write(
    "A slab-based electricity bill calculator built for the Software Testing AAT "
    "*Automated Unit Testing of an Electricity Bill Calculator Using PyTest: "
    "Positive, Negative and Boundary Value Testing*."
)
st.warning(
    "**Disclaimer:** All tariff rates, surcharges and duties used here are **illustrative "
    "academic rates** created for this project. They are **not** official electricity board rates.",
    icon="⚠️",
)

with st.sidebar:
    st.header("📘 How the bill is calculated")
    st.markdown(
        "1. **Energy charge** – progressive slabs: each slab's rate applies only to the units inside it.\n"
        "2. **+ Fixed charge** – per bill, even at 0 units.\n"
        "3. **+ Fuel surcharge** – a small amount per unit.\n"
        "4. **+ Electricity duty** – a % tax on steps 1–3.\n"
        "5. **= Net payable amount**"
    )
    st.info(
        "**Example (Residential, 250 units)**\n\n"
        "100 × ₹3 + 100 × ₹5 + 50 × ₹7 = ₹1,150\n\n"
        "+ Fixed ₹50 + Surcharge ₹50.00 = ₹1,250.00\n\n"
        "+ Duty 5% ₹62.50 = **₹1,312.50**"
    )

tab_bill, tab_tariff, tab_tests = st.tabs(["🧾 Bill Calculator", "📘 Tariff Details", "🧪 Testing Dashboard"])

# ---------------------------------------------------------------------------
# TAB 1: Bill calculator
# ---------------------------------------------------------------------------
with tab_bill:
    left, right = st.columns([1, 1.4], gap="large")

    with left:
        st.subheader("👤 Customer Information")
        with st.form("bill_form"):
            customer_name = st.text_input("Customer Name", placeholder="e.g. Ravi Kumar", key="name")
            customer_id = st.text_input("Customer ID", placeholder="e.g. EB1001", key="customer_id")
            category = st.selectbox("Customer Category", VALID_CATEGORIES, key="category")
            units = st.text_input("Electricity Consumption (units / kWh)", placeholder="e.g. 250", key="units")
            submitted = st.form_submit_button("Calculate Bill", type="primary", width="stretch")
        st.caption(
            "Customer ID: **EB** + 4–8 digits. Units: whole number from 0 to 100,000 "
            "(meters record whole kWh, so decimals such as 150.5 are rejected)."
        )

    with right:
        st.subheader("💡 Bill Summary")
        if not submitted:
            st.info("Fill in the customer details and click **Calculate Bill**.")
        else:
            try:
                bill = generate_bill(customer_name, customer_id, units, category)
            except BillValidationError as error:
                # Validation failed: show the meaningful message from validation.py
                st.error(f"❌ {error}")
            else:
                st.success("✅ Bill calculated successfully.")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Customer", bill["customer_name"])
                c2.metric("Customer ID", bill["customer_id"])
                c3.metric("Category", bill["category"])
                c4.metric("Units consumed", f"{bill['units']:,}")

                st.markdown("**Slab-wise Breakdown**")
                if bill["slab_breakdown"]:
                    table = pd.DataFrame(bill["slab_breakdown"])
                    table["calculation"] = [f"{r['units']} × ₹{r['rate']}" for r in bill["slab_breakdown"]]
                    table = table[["slab", "units", "rate", "calculation", "amount"]]
                    table.columns = ["Slab (units)", "Units charged", "Rate (₹/unit)", "Calculation", "Amount (₹)"]
                    st.dataframe(table, hide_index=True, width="stretch")
                else:
                    st.write("No energy consumed — only fixed charge (and duty on it) applies.")

                st.markdown("**Charges, Surcharge & Tax Breakdown**")
                charges = pd.DataFrame([
                    ("Energy charge (slabs)", "Sum of slab amounts", bill["energy_charge"]),
                    ("Fixed charge", f"{bill['category']} fixed charge", bill["fixed_charge"]),
                    ("Fuel adjustment surcharge",
                     f"{bill['units']:,} units × ₹{bill['fuel_surcharge_rate']:.2f}", bill["fuel_surcharge"]),
                    ("Subtotal", "Energy + Fixed + Surcharge", bill["subtotal"]),
                    ("Electricity duty",
                     f"{bill['electricity_duty_percent']:g}% of subtotal", bill["electricity_duty"]),
                ], columns=["Component", "Basis", "Amount"])
                charges["Amount"] = charges["Amount"].map(format_rupees)
                st.dataframe(charges, hide_index=True, width="stretch")

                st.markdown(
                    f"<div class='total-box'><div class='label'>Final Bill Amount (Net Payable)</div>"
                    f"<div class='amount'>{format_rupees(bill['total_amount'])}</div></div>",
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# TAB 2: Tariff details
# ---------------------------------------------------------------------------
with tab_tariff:
    st.subheader("Residential and Commercial Tariffs")
    cols = st.columns(2, gap="large")
    for col, cat in zip(cols, VALID_CATEGORIES):
        t = TARIFFS[cat]
        with col:
            st.markdown(f"#### {cat}")
            st.dataframe(tariff_table(cat), hide_index=True, width="stretch")
            st.markdown(
                f"- Fixed charge: **{format_rupees(t['fixed_charge'])}** per bill\n"
                f"- Fuel surcharge: **₹{t['fuel_surcharge_per_unit']}** per unit\n"
                f"- Electricity duty: **{t['electricity_duty_percent']}%** of subtotal"
            )
    st.caption("All values are configured in the TARIFFS dictionary in bill_calculator.py.")

# ---------------------------------------------------------------------------
# TAB 3: Testing dashboard (real results only)
# ---------------------------------------------------------------------------
with tab_tests:
    st.subheader("🧪 Testing Dashboard")
    st.caption(
        "Every number here is read from files that **pytest** writes in the reports/ folder "
        "(junit_results.xml, coverage.json, test_history.json). Nothing is typed in by hand."
    )

    if st.button("▶ Run test suite now", key="run_tests"):
        with st.spinner("Running pytest… (takes about 10–20 seconds)"):
            code, output = run_test_suite()
        (st.success if code == 0 else st.error)(f"pytest finished with exit code {code}.")
        with st.expander("Terminal output of this run"):
            st.code(output[-6000:], language="text")

    results = report_reader.load_junit_results()
    coverage = report_reader.load_coverage()

    if results is None:
        st.info("No test results found yet. Click **Run test suite now** or run `pytest` in the terminal.")
    else:
        s = results["summary"]
        if s["status"] == "PASSED":
            st.success(f"✅ **Status: PASSED** — all {s['passed']} executed tests passed.  (Run: {s['timestamp']})")
        else:
            st.error(f"❌ **Status: FAILED** — {s['failed']} failed, {s['errors']} errors.  (Run: {s['timestamp']})")

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total test cases", s["total"])
        m2.metric("✅ Passed", s["passed"])
        m3.metric("❌ Failed", s["failed"] + s["errors"])
        m4.metric("📊 Code coverage", f"{coverage['percent']:.2f}%" if coverage else "n/a")
        m5.metric("⏱ Duration", f"{s['duration']:.2f}s")

        chart_col, cov_col = st.columns([1.5, 1], gap="large")
        with chart_col:
            st.markdown("**Testing technique distribution**")
            dist = report_reader.technique_distribution(results["cases"])
            dist_df = pd.DataFrame({"Technique": list(dist), "Test cases": list(dist.values())})
            bars = alt.Chart(dist_df).mark_bar(color=ACCENT, cornerRadiusEnd=4, height=18).encode(
                x=alt.X("Test cases:Q", title="Test cases"),
                y=alt.Y("Technique:N", sort="-x", title=None),
                tooltip=["Technique", "Test cases"],
            )
            labels = bars.mark_text(align="left", dx=4).encode(text="Test cases:Q", color=alt.value("gray"))
            st.altair_chart((bars + labels).properties(height=34 * len(dist_df)), width="stretch")
            with st.expander("Table view"):
                st.dataframe(dist_df, hide_index=True, width="stretch")
        with cov_col:
            st.markdown("**Code coverage by module**")
            if coverage:
                cov_df = pd.DataFrame({"Module": list(coverage["files"]),
                                       "Coverage %": list(coverage["files"].values())})
                st.dataframe(cov_df, hide_index=True, width="stretch",
                             column_config={"Coverage %": st.column_config.ProgressColumn(
                                 min_value=0, max_value=100, format="%.1f%%")})
                st.caption(f"Coverage measured: {coverage['timestamp']}")
            else:
                st.info("No coverage.json found yet.")

        st.markdown("**Individual test case results**")
        f1, f2 = st.columns(2)
        status_filter = f1.selectbox("Status", ["All", "passed", "failed", "error", "skipped"], key="status_filter")
        tech_filter = f2.selectbox("Technique", ["All"] + list(dist), key="tech_filter")
        cases_df = pd.DataFrame(results["cases"])
        if status_filter != "All":
            cases_df = cases_df[cases_df["status"] == status_filter]
        if tech_filter != "All":
            cases_df = cases_df[cases_df["technique"] == tech_filter]
        cases_df["status"] = cases_df["status"].map(
            {"passed": "✅ passed", "failed": "❌ failed", "error": "⚠️ error", "skipped": "⏭ skipped"})
        st.dataframe(cases_df[["technique", "file", "name", "status", "time"]],
                     hide_index=True, width="stretch", height=320)

    st.markdown("**Recent test execution summary**")
    history = report_reader.load_history()
    if history:
        hist_df = pd.DataFrame(history)[["run_at", "command", "total", "passed", "failed",
                                         "errors", "duration_s", "status"]]
        hist_df["status"] = hist_df["status"].map({"PASSED": "✅ PASSED", "FAILED": "❌ FAILED"})
        st.dataframe(hist_df, hide_index=True, width="stretch")
    else:
        st.info("No test runs recorded yet.")

    if report_reader.HTML_REPORT_FILE.exists():
        st.download_button("⬇ Download detailed HTML test report",
                           report_reader.HTML_REPORT_FILE.read_bytes(),
                           file_name="test_report.html", mime="text/html")
    st.caption("HTML coverage report: open reports/coverage_html/index.html in a browser.")
