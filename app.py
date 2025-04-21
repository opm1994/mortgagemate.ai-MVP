import streamlit as st
from fpdf import FPDF

# === PDF REPORT GENERATION (Underwriting Summary) ===
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
st.title("MortgageMate AI - Underwriting Engine (MVP)")

uploaded_file = st.file_uploader("Upload Mortgage Application Summary (PDF only)", type=["pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.error("Only PDF files are accepted. Please upload a valid mortgage document.")
    st.stop()

beacon = st.number_input("Beacon Score", min_value=300, max_value=900, value=680)
gds = st.number_input("GDS (%)", min_value=0.0, max_value=100.0, value=30.0)
tds = st.number_input("TDS (%)", min_value=0.0, max_value=100.0, value=38.0)
income_type = st.selectbox("Income Type", ["Salaried", "Self-Employed", "Commission"])

if st.button("Generate Underwriting Summary PDF"):
    file_data = {
        "Beacon Score": beacon,
        "GDS": f"{gds}%",
        "TDS": f"{tds}%",
        "Income Type": income_type
    }
    report_path = generate_underwriting_summary(file_data)
    with open(report_path, "rb") as f:
        st.download_button("Download Underwriting Summary PDF", f, file_name=report_path, mime="application/pdf")
