import streamlit as st
import pandas as pd
from io import StringIO
import base64
from audit_logic import (
    process_schedule,
    process_invoice,
    compare_schedule_invoice,
    generate_report,
    parse_time,
)
from datetime import datetime, timedelta

st.set_page_config(page_title="Argus - TV Ad Audit Tool", layout="wide")


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")

st.title("Argus - TV Ad Audit Tool")

st.write("Upload your Invoice file to generate an audit report.")

# Load the Spectrum Schedule
spectrum_schedule = pd.read_csv("Spectrum_Schedule.csv")
st.write("Spectrum Schedule:")
st.write(spectrum_schedule)

invoice_file = st.file_uploader("Upload Invoice CSV", type="csv")

if invoice_file is not None:
    st.write(f"File uploaded: {invoice_file.name}")
    st.write(f"File size: {invoice_file.size} bytes")
    try:
        # Read the CSV file
        invoice_df = pd.read_csv(StringIO(invoice_file.getvalue().decode("utf-8")))

        # Rename columns to match expected column names
        column_mapping = {
            "Invoice": "ID1",
            "Order Number": "ID2",
            "Line Number": "ID3",
            "Sys Code": "ID4",
            "Retail Unit": "ID5",
            "Network": "Network",
            "Date": "Date",
            "Time": "Time",
            "Day": "Day",
            "Spot ID": "ID6",
            "Spot Title": "Description",
            "Program Description": "Program",
            "ISCI Code": "ID7",
            "Spot Length": "Duration",
            "Amount": "Rate",
            "Currency": "Currency",
        }
        invoice_df.rename(columns=column_mapping, inplace=True)

        schedule = process_schedule(spectrum_schedule)
        invoice = process_invoice(invoice_df)
        results = compare_schedule_invoice(schedule, invoice)
        report = generate_report(results, invoice)

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
        st.write("Error details:", str(e))
        import traceback

        st.write("Traceback:", traceback.format_exc())
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
