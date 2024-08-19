import streamlit as st
import pandas as pd
from io import StringIO
import base64
from audit_logic import process_schedule, process_invoice, compare_schedule_invoice, generate_report, parse_time
from datetime import datetime, timedelta
from flask import Flask, send_from_directory
import subprocess
import os

app = Flask(__name__)

def run_streamlit():
    st.set_page_config(page_title="Argus - TV Ad Audit Tool", layout="wide")

    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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
            # Read the CSV file without headers and assign column names
            column_names = ['ID1', 'ID2', 'ID3', 'ID4', 'ID5', 'Network', 'Date', 'Time', 'Day', 'ID6', 'Description', 'Program', 'ID7', 'Duration', 'Rate', 'Currency']
            invoice_df = pd.read_csv(StringIO(invoice_file.getvalue().decode("utf-8")), header=None, names=column_names)
            
            debug_info = []
            debug_info.append("Invoice DataFrame:")
            debug_info.append(invoice_df.to_string())

            schedule = process_schedule(spectrum_schedule)
            debug_info.append("\nProcessed Schedule:")
            debug_info.append(schedule.to_string())

            invoice = process_invoice(invoice_df)
            debug_info.append("\nProcessed Invoice:")
            debug_info.append(invoice.to_string())

            # Debug information
            debug_info.append(f"\nUnique Networks in Schedule: {schedule['Network'].unique()}")
            debug_info.append(f"Unique Networks in Invoice: {invoice['Network'].unique()}")

            for network in schedule['Network'].unique():
                debug_info.append(f"\nNetwork: {network}")
                network_schedule = schedule[schedule['Network'] == network]
                network_invoice = invoice[invoice['Network'] == network]
                
                debug_info.append("Schedule for this network:")
                debug_info.append(network_schedule.to_string())
                
                debug_info.append("\nInvoice for this network:")
                debug_info.append(network_invoice.to_string())

                # Additional debug information
                for week in range(1, 5):
                    debug_info.append(f"\nWeek {week}:")
                    week_schedule = network_schedule[network_schedule['Week'] == week]
                    week_invoice = network_invoice[network_invoice['Week'] == week]
                    
                    debug_info.append("Week Schedule:")
                    debug_info.append(week_schedule.to_string())
                    
                    debug_info.append("\nWeek Invoice:")
                    debug_info.append(week_invoice.to_string())

                    for timeslot in week_schedule['Time'].unique():
                        debug_info.append(f"\nTimeslot: {timeslot}")
                        slot_schedule = week_schedule[week_schedule['Time'] == timeslot]
                        
                        slot_start_time = parse_time(timeslot.split('-')[0])
                        slot_end_time = parse_time(timeslot.split('-')[1])
                        slot_start_with_tolerance = (slot_start_time - timedelta(minutes=3)).time()
                        slot_end_with_tolerance = (slot_end_time + timedelta(minutes=3)).time()
                        
                        slot_invoice = week_invoice[
                            (week_invoice['Time'].dt.time >= slot_start_with_tolerance) &
                            (week_invoice['Time'].dt.time <= slot_end_with_tolerance)
                        ]
                        
                        debug_info.append("Slot Schedule:")
                        debug_info.append(slot_schedule.to_string())
                        
                        debug_info.append("\nSlot Invoice:")
                        debug_info.append(slot_invoice.to_string())

            results = compare_schedule_invoice(schedule, invoice)
            debug_info.append("\nComparison Results:")
            debug_info.append(str(results))

            report = generate_report(results)

            st.subheader("Audit Report")
            for line in report:
                st.text(line)

            # Create a download link for the report
            report_text = "\n".join(report)
            b64 = base64.b64encode(report_text.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="audit_report.txt">Download Audit Report</a>'
            st.markdown(href, unsafe_allow_html=True)

            # Add a button to copy debug information and result output
            debug_and_result = "\n".join(debug_info) + "\n\nAudit Report:\n" + report_text
            if st.button("Copy Debug Info and Result"):
                st.text_area("Debug Information and Result Output", debug_and_result, height=300)
                st.markdown(f'<textarea id="debug-info" style="position: absolute; left: -9999px;">{debug_and_result}</textarea>', unsafe_allow_html=True)
                st.markdown("""
                <script>
                function copyDebugInfo() {
                    var copyText = document.getElementById("debug-info");
                    copyText.select();
                    document.execCommand("copy");
                }
                </script>
                """, unsafe_allow_html=True)
                st.markdown('<button onclick="copyDebugInfo()">Copy to Clipboard</button>', unsafe_allow_html=True)

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

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    subprocess.Popen(["streamlit", "run", __file__, "--server.port", str(port), "--server.address", "0.0.0.0"])
    app.run(host='0.0.0.0', port=port)
