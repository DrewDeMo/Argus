import streamlit as st
import pandas as pd
from io import StringIO
from audit_logic import process_schedule, process_invoice, compare_schedule_invoice, generate_report

st.set_page_config(page_title="Argus - TV Ad Audit Tool", layout="wide")

st.title("Argus - TV Ad Audit Tool")

st.write("Upload your Schedule and Invoice files to generate an audit report.")

schedule_file = st.file_uploader("Upload Schedule CSV", type="csv")
invoice_file = st.file_uploader("Upload Invoice CSV", type="csv")

if schedule_file and invoice_file:
    schedule_df = pd.read_csv(StringIO(schedule_file.getvalue().decode("utf-8")))
    invoice_df = pd.read_csv(StringIO(invoice_file.getvalue().decode("utf-8")))

    schedule = process_schedule(schedule_df)
    invoice = process_invoice(invoice_df)
    results = compare_schedule_invoice(schedule, invoice)
    report = generate_report(results)

    st.subheader("Audit Report")
    for line in report:
        st.text(line)
else:
    st.info("Please upload both Schedule and Invoice files to generate the report.")
