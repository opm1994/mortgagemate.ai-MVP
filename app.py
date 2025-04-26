import streamlit as st
from fpdf import FPDF
import fitz  # For PDF parsing (PyMuPDF)

# === CUSTOM STYLING ===
st.markdown("""
    <style>
        .main {
            background-color: #e6f0fa;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #003366;
        }
        .stButton>button {
            background-color: #0066cc;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
        }
    </style>
""", unsafe_allow_html=True)

# === INCOME EXTRACTION ===
def extract_t4_income(file):
    if file:
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
    if file:
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

# === CREDIT REPORT EXTRACTION ===
def extract_credit_score_and_liabilities(file):
    beacon_score = None
    liabilities = []
    if file:
        doc = fitz.open(stream=file.read(), filetype="pdf")
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
                        amount = payment = None
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

# === CALCULATIONS ===
def calculate_gds_tds(income, mortgage_payment, property_tax, heat, rent=0, other_debts=0):
    if not income or income <= 0:
        return None, None
    gross_monthly_income = income / 12
    gds = ((mortgage_payment + property_tax + heat + rent) / gross_monthly_income) * 100
    tds = ((mortgage_payment + property_tax + heat + rent + other_debts) / gross_monthly_income) * 100
    return round(gds, 2), round(tds, 2)

def calculate_ltv(purchase_price, mortgage_amount):
    if not purchase_price or purchase_price <= 0:
        return None
    ltv = (mortgage_amount / purchase_price) * 100
    return round(ltv, 2)

# === PDF GENERATOR ===
def generate_filogix_compliant_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Mortgage Application Summary", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Broker/Agent Information", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 6, txt=f"{data.get('broker_name')} | Agent: {data.get('agent_name')} | License: {data.get('license_number')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Applicant & Employment", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 6, txt=f"{data.get('applicant_name')} | {data.get('employment_type')} | Income: {data.get('annual_income')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Liabilities", ln=True)
    pdf.set_font("Arial", '', 11)
    if data.get("liabilities"):
        pdf.cell(60, 6, "Type", border=1)
        pdf.cell(60, 6, "Balance", border=1)
        pdf.cell(60, 6, "Payment", border=1, ln=True)
        for liab in data["liabilities"]:
            pdf.cell(60, 6, liab['type'], border=1)
            pdf.cell(60, 6, f"${liab['balance']:,.2f}", border=1)
            pdf.cell(60, 6, f"${liab['payment']:,.2f}", border=1, ln=True)
    else:
        pdf.cell(200, 6, txt="No liabilities found.", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Property & Financing", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 6, txt=f"{data.get('property_type')} | {data.get('occupancy')}", ln=True)
    pdf.cell(200, 6, txt=f"Price: {data.get('purchase_price')} | Mortgage: {data.get('mortgage_amount')} | LTV: {data.get('ltv')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt="Qualification Summary", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 6, txt=f"Beacon: {data.get('beacon_score')} | GDS: {data.get('gds')}% | TDS: {data.get('tds')}%", ln=True)

    filename = "MortgageMate_Filogix_Application.pdf"
    pdf.output(filename)
    return filename
# === LANDING PAGE ===
def landing_page():
    st.markdown("<h1>🤖 MortgageMate AI</h1>", unsafe_allow_html=True)
    st.markdown("### Your AI-Powered Mortgage Underwriting Assistant")
    
    st.markdown("""
    Welcome to **MortgageMate AI** — the smarter, faster way to underwrite mortgage files.
    """)
    st.markdown("""
    - 📑 **Smart Document Extraction**
    - ⚡ **Automated GDS/TDS & LTV Calculations**
    - 🏦 **Lender-Ready Filogix Packaging**
    - 🎯 **Reduce Errors & Focus on Closing Deals**
    """)

    if st.button("🚀 Start Underwriting Now"):
        st.session_state["page"] = "underwriting"

# === UNDERWRITING PAGE ===
def underwriting_page():
    st.markdown("<h2>📝 MortgageMate AI - Underwriting Form</h2>", unsafe_allow_html=True)

    with st.form("underwriting_form"):
        # Borrower Info
        st.header("👤 Borrower Information")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        employment_type = st.selectbox("Employment Type", ["Salaried", "Self-Employed"])

        # Property Details
        st.header("🏠 Property & Application Details")
        transaction_type = st.selectbox("Transaction Type", ["Purchase", "Switch", "Refinance"])
        property_value = st.number_input("Property Value ($)", min_value=0.0)
        mortgage_amount = st.number_input("Mortgage Amount ($)", min_value=0.0)
        property_tax = st.number_input("Monthly Property Tax ($)", min_value=0.0)
        heat = st.number_input("Monthly Heat ($)", min_value=0.0, value=100.0)
        property_type = st.selectbox("Property Type", ["Detached", "Condo", "Townhouse", "Other"])
        occupancy = st.selectbox("Occupancy", ["Owner-Occupied", "Rental"])

        # Document Uploads
        st.header("📂 Upload Documents")
        t4_file = noa_file = None
        if employment_type == "Salaried":
            t4_file = st.file_uploader("Upload T4 Slip", type=["pdf"])
        else:
            noa_file = st.file_uploader("Upload Notice of Assessment", type=["pdf"])
        credit_file = st.file_uploader("Upload Credit Report", type=["pdf"])

        submitted = st.form_submit_button("Run AI Underwriting")

    if submitted:
        st.success("✅ Running AI underwriting...")

        # Extraction Logic
        income = extract_t4_income(t4_file) if employment_type == "Salaried" else extract_noa_line_15000(noa_file)
        beacon_score, liabilities = extract_credit_score_and_liabilities(credit_file)

        mortgage_payment = mortgage_amount * 0.006
        gds, tds = calculate_gds_tds(income, mortgage_payment, property_tax, heat, 0, sum(l['payment'] for l in liabilities))
        ltv = calculate_ltv(property_value, mortgage_amount)

        file_data = {
            "broker_name": "Your Brokerage",
            "agent_name": "John Doe",
            "license_number": "123456",
            "applicant_name": f"{first_name} {last_name}",
            "employment_type": employment_type,
            "annual_income": f"${income:,.2f}" if income else "N/A",
            "liabilities": liabilities,
            "purchase_price": f"${property_value:,.2f}",
            "mortgage_amount": f"${mortgage_amount:,.2f}",
            "ltv": f"{ltv:.2f}%" if ltv else "N/A",
            "beacon_score": beacon_score or "N/A",
            "gds": gds or "N/A",
            "tds": tds or "N/A",
            "property_type": property_type,
            "occupancy": occupancy
        }

        pdf_file = generate_filogix_compliant_pdf(file_data)
        with open(pdf_file, "rb") as f:
            st.download_button("⬇️ Download Mortgage Application (Filogix Format)", f, file_name=pdf_file, mime="application/pdf")

# === NAVIGATION LOGIC ===
if "page" not in st.session_state:
    st.session_state["page"] = "landing"

if st.session_state["page"] == "landing":
    landing_page()
elif st.session_state["page"] == "underwriting":
    underwriting_page()
