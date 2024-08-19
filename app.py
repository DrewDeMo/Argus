import streamlit as st
import pandas as pd
from io import StringIO
import base64
from audit_logic import process_schedule, process_invoice, compare_schedule_invoice, generate_report

st.set_page_config(page_title="Argus - TV Ad Audit Tool", layout="wide")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

st.title("Argus - TV Ad Audit Tool")

st.write("Upload your Invoice file to generate an audit report.")

# Load the Spectrum Schedule
spectrum_schedule = pd.read_csv("Spectrum_Schedule.csv")

invoice_file = st.file_uploader("Upload Invoice CSV", type="csv")

if invoice_file:
    try:
        # Read the CSV file without headers and assign column names
        column_names = ['ID1', 'ID2', 'ID3', 'ID4', 'ID5', 'Network', 'Date', 'Time', 'Day', 'ID6', 'Description', 'Program', 'ID7', 'Duration', 'Rate', 'Currency']
        invoice_df = pd.read_csv(StringIO(invoice_file.getvalue().decode("utf-8")), header=None, names=column_names)

        schedule = process_schedule(spectrum_schedule)
        invoice = process_invoice(invoice_df)
        results = compare_schedule_invoice(schedule, invoice)
        report = generate_report(results)

        st.subheader("Audit Report")
        for line in report:
            st.text(line)

        # Create a download link for the report
        report_text = "\n".join(report)
        b64 = base64.b64encode(report_text.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="audit_report.txt">Download Audit Report</a>'
        st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while processing the files: {str(e)}")
else:
    st.info("Please upload the Invoice file to generate the report.")

st.sidebar.title("About")
st.sidebar.info(
    "Argus is a TV Ad Audit Tool that compares scheduled ads with invoiced ads "
    "to identify discrepancies and calculate pre-empted spots and values."
)
st.sidebar.title("Help")
st.sidebar.info(
    "1. The Spectrum Schedule is pre-loaded\n"
    "2. Upload your Invoice CSV file\n"
    "3. The audit report will be generated automatically\n"
    "4. Download the report using the link provided"
)
