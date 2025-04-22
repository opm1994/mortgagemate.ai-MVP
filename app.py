import streamlit as st
from fpdf import FPDF
import fitz  # PyMuPDF

# === DOCUMENT EXTRACTION HELPERS ===

def extract_t4_income(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        for line in text.splitlines():
            if "14" in line:
                try:
                    value = line.split("14")[-1].strip().replace(",", "").replace("$", "")
                    return float(value)
                except:
                    continue
    return None

def extract_noa_line_15000(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        for line in text.splitlines():
            if "15000" in line:
                try:
                    value = line.split("15000")[-1].strip().replace(",", "").replace("$", "")
                    return float(value)
                except:
                    continue
    return None

def extract_paystub_ytd(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        for line in text.splitlines():
            if "YTD" in line:
                try:
                    parts = line.split()
                    for part in parts:
                        if part.replace(",", "").replace("$", "").replace(".", "").isdigit():
                            return float(part.replace(",", "").replace("$", ""))
                except:
                    continue
    return None

def extract_lease_rent(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    rent = None
    tenant = None
    for page in doc:
        text = page.get_text()
        for line in text.splitlines():
            if "rent" in line.lower() and "$" in line:
                try:
                    parts = line.split()
                    for part in parts:
                        if "$" in part or part.replace(",", "").replace(".", "").isdigit():
                            clean = part.replace("$", "").replace(",", "").replace(".", "")
                            if clean.isdigit():
                                rent = float(part.replace("$", "").replace(",", ""))
                except:
                    continue
            if "tenant" in line.lower():
                tenant = line
    return rent, tenant

def extract_credit_score_and_liabilities(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    beacon_score = None
    liabilities = []
    for page in doc:
        text = page.get_text()
        lines = text.splitlines()
        for line in lines:
            if "Beacon" in line and beacon_score is None:
                try:
                    for part in line.split():
                        if part.isdigit() and 300 <= int(part) <= 900:
                            beacon_score = int(part)
                except:
                    continue
            if any(term in line.lower() for term in ["credit card", "loan", "line of credit", "auto", "student", "mortgage"]):
                try:
                    amount = None
                    payment = None
                    for part in line.split():
                        if "$" in part or part.replace(",", "").replace(".", "").isdigit():
                            cleaned = part.replace("$", "").replace(",", "")
                            if amount is None:
                                amount = float(cleaned)
                            elif payment is None:
                                payment = float(cleaned)
                    if amount and payment:
                        liabilities.append({"type": line.split()[0], "balance": amount, "payment": payment})
                except:
                    continue
    return beacon_score, liabilities

def calculate_gds_tds(income, mortgage_payment, property_tax, heat, rent=0, other_debts=0):
    if income <= 0:
        return None, None
    gross_monthly_income = income / 12
    gds = ((mortgage_payment + property_tax + heat + rent) / gross_monthly_income) * 100
    tds = ((mortgage_payment + property_tax + heat + rent + other_debts) / gross_monthly_income) * 100
    return round(gds, 2), round(tds, 2)

def calculate_ltv(purchase_price, mortgage_amount):
    if purchase_price <= 0:
        return None
    ltv = (mortgage_amount / purchase_price) * 100
    return round(ltv, 2)

def generate_underwriting_summary(file_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="MortgageMate AI - Underwriting Summary", ln=True, align='C')
    pdf.ln(10)
    for key, value in file_data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    filename = "underwriting_summary.pdf"
    pdf.output(filename)
    return filename

# === STREAMLIT UI ===
st.set_page_config(page_title="MortgageMate AI", layout="centered")
st.markdown("# 🏡 MortgageMate AI - Underwriting Automation")
st.markdown("Upload your client documents and let AI extract key underwriting details automatically.")

with st.expander("📂 Upload Income Documents"):
    t4_file = st.file_uploader("T4 Slip", type=["pdf"], key="t4")
    noa_file = st.file_uploader("NOA", type=["pdf"], key="noa")
    paystub_file = st.file_uploader("Paystub", type=["pdf"], key="paystub")

with st.expander("📂 Upload Lease Agreement"):
    lease_file = st.file_uploader("Lease Agreement", type=["pdf"], key="lease")

with st.expander("📂 Upload Credit Report"):
    credit_file = st.file_uploader("Credit Report", type=["pdf"], key="credit")

income_type = st.selectbox("Income Type", ["Salaried", "Self-Employed", "Commission"])
purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, value=500000.0)
mortgage_amount = st.number_input("Mortgage Amount ($)", min_value=0.0, value=450000.0)
property_tax = st.number_input("Monthly Property Tax ($)", min_value=0.0, value=300.0)
heat = st.number_input("Monthly Heat ($)", min_value=0.0, value=100.0)

# === INCOME EXTRACTION ===
extracted_income = None
if t4_file:
    extracted_income = extract_t4_income(t4_file)
elif noa_file:
    extracted_income = extract_noa_line_15000(noa_file)
elif paystub_file:
    extracted_income = extract_paystub_ytd(paystub_file)

if extracted_income:
    st.success(f"✅ Extracted Annual Income: ${extracted_income:,.2f}")
else:
    st.warning("⚠️ No income could be extracted from uploaded documents.")

# === LEASE EXTRACTION ===
lease_rent = 0
lease_tenant = None
if lease_file:
    lease_rent, lease_tenant = extract_lease_rent(lease_file)
    if lease_rent:
        st.success(f"✅ Monthly Rent: ${lease_rent:,.2f}")
    if lease_tenant:
        st.info(f"Tenant: {lease_tenant}")

# === CREDIT REPORT EXTRACTION ===
beacon = 680
liabilities = []
total_monthly_debt = 0
if credit_file:
    beacon_score, liabilities = extract_credit_score_and_liabilities(credit_file)
    if beacon_score:
        beacon = beacon_score
        st.success(f"✅ Beacon Score Extracted: {beacon}")
    if liabilities:
        total_monthly_debt = sum(liab["payment"] for liab in liabilities)
        st.info(f"🧾 Liabilities Found: {len(liabilities)} with ${total_monthly_debt:,.2f} monthly obligations")

# === CALCULATIONS ===
gds, tds = calculate_gds_tds(extracted_income or 0, mortgage_amount * 0.006, property_tax, heat, lease_rent, total_monthly_debt)
ltv = calculate_ltv(purchase_price, mortgage_amount)

# === GENERATE PDF ===
if st.button("📄 Generate Underwriting Summary PDF"):
    file_data = {
        "Beacon Score": beacon,
        "Income Type": income_type,
        "Annual Income": f"${extracted_income:,.2f}" if extracted_income else "Not available",
        "Monthly Rent": f"${lease_rent:,.2f}" if lease_rent else "Not available",
        "Tenant Info": lease_tenant or "Not found",
        "Purchase Price": f"${purchase_price:,.2f}",
        "Mortgage Amount": f"${mortgage_amount:,.2f}",
        "LTV": f"{ltv:.2f}%" if ltv else "Not available",
        "GDS": f"{gds:.2f}%" if gds else "Not available",
        "TDS": f"{tds:.2f}%" if tds else "Not available"
    }
    report_path = generate_underwriting_summary(file_data)
    with open(report_path, "rb") as f:
        st.download_button("⬇️ Download Underwriting Summary PDF", f, file_name=report_path, mime="application/pdf")

