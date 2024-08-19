import streamlit as st
import requests
import base64

st.set_page_config(page_title="Argus - TV Ad Audit Tool", layout="wide")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

st.title("Argus - TV Ad Audit Tool")

st.write("Upload your Invoice file to generate an audit report.")

invoice_file = st.file_uploader("Upload Invoice CSV", type="csv")

if invoice_file is not None:
    st.write(f"File uploaded: {invoice_file.name}")
    st.write(f"File size: {invoice_file.size} bytes")
    
    if st.button("Process Files"):
        files = {'invoice': invoice_file}
        response = requests.post('http://localhost:8000/process', files=files)
        
        if response.status_code == 200:
            report = response.json()['report']
            
            st.subheader("Audit Report")
            for line in report:
                st.text(line)

            # Create a download link for the report
            report_text = "\n".join(report)
            b64 = base64.b64encode(report_text.encode()).decode()
            href = f'<a href="data:file/txt;base64,{b64}" download="audit_report.txt">Download Audit Report</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("An error occurred while processing the files. Please try again.")
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
    "3. Click 'Process Files' to generate the audit report\n"
    "4. Download the report using the link provided"
)
