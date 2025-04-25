import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="MortgageMate AI", layout="centered")

# --- LANDING PAGE ---
def landing_page():
    st.markdown("# 🤖 MortgageMate AI")
    st.markdown("### Your AI-Powered Mortgage Underwriting Assistant")
    
    st.markdown("""
    Welcome to MortgageMate AI — the smarter, faster way to underwrite mortgage files.
    
    **What We Do:**
    - 📑 **Smart Document Extraction**: Upload client docs, and let AI handle the data.
    - ⚡ **Automated GDS/TDS & LTV**: Instant calculations based on lender guidelines.
    - 🏦 **Lender-Ready Packaging**: Generate Filogix-style submissions in seconds.
    - 🎯 **Accuracy Guaranteed**: Reduce errors, save time, and focus on closing deals.
    """)

    if st.button("🚀 Start Underwriting Now"):
        st.session_state["page"] = "underwriting"

# --- UNDERWRITING PAGE PLACEHOLDER ---
def underwriting_page():
    st.markdown("# 📄 MortgageMate AI - Underwriting Form")
    st.markdown("_(Underwriting form coming in Phase 2...)_")

# --- NAVIGATION LOGIC ---
if "page" not in st.session_state:
    st.session_state["page"] = "landing"

if st.session_state["page"] == "landing":
    landing_page()
elif st.session_state["page"] == "underwriting":
    underwriting_page()
def underwriting_page():
    st.markdown("# 📝 MortgageMate AI - Underwriting Form")

    with st.form("underwriting_form"):
        # --- Section 1: Primary Borrower ---
        st.subheader("👤 Primary Borrower Information")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        employment_type = st.selectbox("Employment Type", ["Salaried", "Self-Employed"])

        add_borrower = st.checkbox("➕ Add Secondary Borrower")

        # --- Section 2: Property & Application Details ---
        st.subheader("🏠 Application & Property Details")
        transaction_type = st.selectbox("Transaction Type", ["Purchase", "Switch", "Refinance"])
        property_address = st.text_input("Property Address")
        city = st.text_input("City")
        province = st.text_input("Province")
        postal_code = st.text_input("Postal Code")
        property_value = st.number_input("Property Value ($)", min_value=0.0)
        interest_type = st.selectbox("Interest Rate Type", ["Fixed", "Variable"])
        amortization = st.slider("Amortization (Years)", 0, 30, 25)

        if transaction_type == "Purchase":
            down_payment = st.number_input("Down Payment ($)", min_value=0.0)
        else:
            mortgage_owed = st.number_input("Current Mortgage Owed ($)", min_value=0.0)
            ltv = (mortgage_owed / property_value) * 100 if property_value else 0
            st.write(f"**Estimated LTV:** {ltv:.2f}%")

        # --- Dynamic Document Uploads ---
        st.subheader("📂 Upload Required Documents")

        # Income Docs
        st.markdown("**Income Documents**")
        if employment_type == "Salaried":
            st.file_uploader("Paystubs", type=["pdf"])
            st.file_uploader("Letter of Employment", type=["pdf"])
            st.file_uploader("T4 Slips (Last 2 Years)", type=["pdf"])
        else:  # Self-Employed
            st.file_uploader("Notice of Assessment (Last 2 Years)", type=["pdf"])
            st.file_uploader("T1 Generals (Last 2 Years)", type=["pdf"])
            st.file_uploader("Bank Statements (Last 6 Months)", type=["pdf"])
            st.file_uploader("Paystubs", type=["pdf"])
            st.file_uploader("Letter of Employment", type=["pdf"])
            st.file_uploader("T4 Slips", type=["pdf"])

        # Transaction Docs
        if transaction_type == "Purchase":
            st.file_uploader("Agreement of Purchase & Sale", type=["pdf"])
            st.file_uploader("MLS Listing", type=["pdf"])
        else:  # Switch or Refinance
            st.file_uploader("Current Mortgage Statement", type=["pdf"])
            st.file_uploader("Property Tax Statement", type=["pdf"])

        # Always Request
        st.markdown("**Government Issued ID**")
        st.file_uploader("Upload ID (Passport, Citizenship Card, or Driver’s License)", type=["pdf"])

        submitted = st.form_submit_button("Run AI Underwriting")

    if submitted:
        st.success("✅ Documents received. Running AI underwriting logic... (Phase 3 coming next)")
if submitted:
    st.success("✅ Documents received. Running AI underwriting...")

    # --- Example Extraction Logic ---
    extracted_income = None
    if employment_type == "Salaried":
        extracted_income = extract_t4_income(st.session_state["Paystubs"]) or 60000  # Placeholder fallback
    else:
        extracted_income = extract_noa_line_15000(st.session_state["Notice of Assessment"]) or 75000

    lease_rent = 0
    if transaction_type == "Rental":
        lease_rent, _ = extract_lease_rent(st.session_state["Lease Agreement"])

    beacon_score, liabilities = extract_credit_score_and_liabilities(st.session_state["Credit Report"])
    total_monthly_debt = sum(l["payment"] for l in liabilities)

    # --- Calculate GDS / TDS / LTV ---
    mortgage_payment = mortgage_amount * 0.006  # Approx stress-tested payment
    gds, tds = calculate_gds_tds(extracted_income, mortgage_payment, property_tax, heat, lease_rent, total_monthly_debt)
    ltv = calculate_ltv(purchase_price, mortgage_amount)

    # --- Prepare Data for PDF ---
    file_data = {
        "broker_name": "Your Brokerage",
        "agent_name": "John Doe",
        "license_number": "123456",

        "applicant_name": f"{first_name} {last_name}",
        "dob": "N/A",
        "marital_status": "N/A",
        "employment_type": employment_type,
        "annual_income": f"${extracted_income:,.2f}",

        "monthly_rent": f"${lease_rent:,.2f}",
        "liabilities": liabilities,

        "purchase_price": f"${purchase_price:,.2f}",
        "mortgage_amount": f"${mortgage_amount:,.2f}",
        "ltv": f"{ltv:.2f}%" if ltv else "N/A",

        "beacon_score": beacon_score or "N/A",
        "gds": f"{gds:.2f}%" if gds else "N/A",
        "tds": f"{tds:.2f}%" if tds else "N/A",

        "property_type": property_type,
        "occupancy": occupancy
    }

   pdf_file = generate_filogix_compliant_pdf(file_data)
with open(pdf_file, "rb") as f:
    st.download_button("⬇️ Download Mortgage Application (Filogix Format)", f, file_name=pdf_file, mime="application/pdf")
def generate_filogix_compliant_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Mortgage Application Summary", ln=True, align='C')
    pdf.ln(5)

    # [ ... rest of the PDF generator code from Phase 4 ... ]
    
    filename = "MortgageMate_Filogix_Application.pdf"
    pdf.output(filename)
    return filename



