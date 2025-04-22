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

def generate_filogix_style_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="MortgageMate AI - Full Mortgage Application Summary", ln=True, align='C')
    pdf.set_font("Arial", '', 11)
    pdf.ln(5)

    # Agent Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="1. Agent Information", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Broker: {data.get('broker_name', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Agent Name: {data.get('agent_name', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"License Number: {data.get('license_number', 'N/A')}", ln=True)
    pdf.ln(5)

    # Applicant Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="2. Applicant Information", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Name: {data.get('applicant_name', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Date of Birth: {data.get('dob', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Marital Status: {data.get('marital_status', 'N/A')}", ln=True)
    pdf.ln(5)

    # Employment Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="3. Employment Information", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Employment Type: {data.get('employment_type', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Annual Income: {data.get('annual_income', 'N/A')}", ln=True)
    pdf.ln(5)

    # Rent
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="4. Other Income", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Monthly Rent: {data.get('monthly_rent', 'N/A')}", ln=True)
    pdf.ln(5)

    # Liabilities
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="5. Liabilities", ln=True)
    pdf.set_font("Arial", '', 11)
    if data.get("liabilities"):
        for liab in data["liabilities"]:
            pdf.cell(200, 10, txt=f"{liab['type']}: Balance ${liab['balance']}, Payment ${liab['payment']}", ln=True)
    else:
        pdf.cell(200, 10, txt="No liabilities detected", ln=True)
    pdf.ln(5)

    # Assets & Down Payment
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="6. Assets & Down Payment", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Purchase Price: {data.get('purchase_price', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Mortgage Amount: {data.get('mortgage_amount', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"LTV: {data.get('ltv', 'N/A')}", ln=True)
    pdf.ln(5)

    # Financing Request
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="7. Financing Request", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Beacon Score: {data.get('beacon_score', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"GDS: {data.get('gds', 'N/A')}%", ln=True)
    pdf.cell(200, 10, txt=f"TDS: {data.get('tds', 'N/A')}%", ln=True)
    pdf.ln(5)

    # Property Profile
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="8. Property Details", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Property Type: {data.get('property_type', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Occupancy: {data.get('occupancy', 'N/A')}", ln=True)

    filename = "Filogix_Style_MortgageMate_Summary.pdf"
    pdf.output(filename)
    return filename

def deploy_filogix_pdf_streamlit(data):
    report_path = generate_filogix_style_pdf(data)
    with open(report_path, "rb") as f:
        st.download_button("⬇️ Download Filogix-Style Mortgage Summary", f, file_name=report_path, mime="application/pdf")
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

# Manual inputs (only ones we can't extract)
st.markdown("### Property & Deal Info")
property_type = st.selectbox("Property Type", ["Detached", "Semi-Detached", "Condo", "Townhouse", "Other"])
occupancy = st.selectbox("Occupancy", ["Owner-Occupied", "Rental", "Second Home"])
purchase_price = st.number_input("Purchase Price ($)", min_value=0.0, value=500000.0)
mortgage_amount = st.number_input("Mortgage Amount ($)", min_value=0.0, value=450000.0)
property_tax = st.number_input("Monthly Property Tax ($)", min_value=0.0, value=300.0)
heat = st.number_input("Monthly Heat ($)", min_value=0.0, value=100.0)

# === EXTRACT DATA ===
income = None
if t4_file:
    income = extract_t4_income(t4_file)
elif noa_file:
    income = extract_noa_line_15000(noa_file)
elif paystub_file:
    income = extract_paystub_ytd(paystub_file)

lease_rent, lease_tenant = (0, "N/A")
if lease_file:
    lease_rent, lease_tenant = extract_lease_rent(lease_file)

beacon = 680
liabilities = []
if credit_file:
    beacon_score, liabilities = extract_credit_score_and_liabilities(credit_file)
    if beacon_score:
        beacon = beacon_score

# === CALCULATE RATIOS ===
total_monthly_debt = sum(l["payment"] for l in liabilities)
gds, tds = calculate_gds_tds(income or 0, mortgage_amount * 0.006, property_tax, heat, lease_rent, total_monthly_debt)
ltv = calculate_ltv(purchase_price, mortgage_amount)

# === BUILD PDF DATA DICT ===
file_data = {
    "broker_name": "Your Brokerage Name",
    "agent_name": "Agent Full Name",
    "license_number": "123456",

    "applicant_name": "Client Name",
    "dob": "YYYY-MM-DD",
    "marital_status": "Single",
    "employment_type": "Salaried",
    "annual_income": f"${income:,.2f}" if income else "Not available",

    "monthly_rent": f"${lease_rent:,.2f}" if lease_rent else "N/A",
    "liabilities": liabilities,

    "purchase_price": f"${purchase_price:,.2f}",
    "mortgage_amount": f"${mortgage_amount:,.2f}",
    "ltv": f"{ltv:.2f}%" if ltv else "N/A",

    "beacon_score": beacon,
    "gds": gds or "N/A",
    "tds": tds or "N/A",

    "property_type": property_type,
    "occupancy": occupancy
}

# === GENERATE FINAL PDF ===
if st.button("📄 Generate Filogix-Style Mortgage PDF"):
    deploy_filogix_pdf_streamlit(file_data)

