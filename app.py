import streamlit as st
from fpdf import FPDF
import fitz  # PyMuPDF for PDF parsing

# === PDF TEXT EXTRACTION HELPERS ===

def extract_t4_income(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        if "14" in text:
            lines = text.splitlines()
            for line in lines:
                if "14" in line:
                    try:
                        value = line.split("14")[-1].strip().replace(",", "").replace("$", "")
                        income = float(value)
                        return income
                    except:
                        continue
    return None

def extract_noa_line_15000(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        if "15000" in text or "Line 15000" in text:
            lines = text.splitlines()
            for line in lines:
                if "15000" in line:
                    try:
                        value = line.split("15000")[-1].strip().replace(",", "").replace("$", "")
                        income = float(value)
                        return income
                    except:
                        continue
    return None

def extract_paystub_ytd(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text = page.get_text()
        if "YTD" in text:
            lines = text.splitlines()
            for line in lines:
                if "YTD" in line:
                    try:
                        parts = line.split()
                        for part in parts:
                            if part.replace(",", "").replace("$", "").replace(".", "").isdigit():
                                income = float(part.replace(",", "").replace("$", ""))
                                return income
                    except:
                        continue
    return None

# === PDF REPORT GENERATION ===
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
st.title("MortgageMate AI - Underwriting Engine with Document Extraction")

with st.expander("Upload Income Documents"):
    t4_file = st.file_uploader("T4 Slip (PDF only)", type=["pdf"], key="t4")
    noa_file = st.file_uploader("Notice of Assessment (NOA)", type=["pdf"], key="noa")
    paystub_file = st.file_uploader("Paystub", type=["pdf"], key="paystub")

income_type = st.selectbox("Income Type", ["Salaried", "Self-Employed", "Commission"])

extracted_income = None
if t4_file:
    extracted_income = extract_t4_income(t4_file)
elif noa_file:
    extracted_income = extract_noa_line_15000(noa_file)
elif paystub_file:
    extracted_income = extract_paystub_ytd(paystub_file)

if extracted_income:
    st.success(f"Extracted Income: ${extracted_income:,.2f}")
else:
    st.warning("No income could be extracted from the uploaded documents.")

beacon = st.number_input("Beacon Score", min_value=300, max_value=900, value=680)
gds = st.number_input("GDS (%)", min_value=0.0, max_value=100.0, value=30.0)
tds = st.number_input("TDS (%)", min_value=0.0, max_value=100.0, value=38.0)

if st.button("Generate Underwriting Summary PDF"):
    file_data = {
        "Beacon Score": beacon,
        "GDS": f"{gds}%",
        "TDS": f"{tds}%",
        "Income Type": income_type,
        "Extracted Income": f"${extracted_income:,.2f}" if extracted_income else "Not available"
    }
    report_path = generate_underwriting_summary(file_data)
    with open(report_path, "rb") as f:
        st.download_button("Download Underwriting Summary PDF", f, file_name=report_path, mime="application/pdf")
