from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
from audit_logic import process_schedule, process_invoice, compare_schedule_invoice, generate_report, parse_time
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Argus API"}

@app.post("/process")
async def process_files(invoice: UploadFile = File(...)):
    spectrum_schedule = pd.read_csv("Spectrum_Schedule.csv")
    
    invoice_content = await invoice.read()
    invoice_df = pd.read_csv(StringIO(invoice_content.decode("utf-8")), header=None, names=['ID1', 'ID2', 'ID3', 'ID4', 'ID5', 'Network', 'Date', 'Time', 'Day', 'ID6', 'Description', 'Program', 'ID7', 'Duration', 'Rate', 'Currency'])

    schedule = process_schedule(spectrum_schedule)
    invoice = process_invoice(invoice_df)
    results = compare_schedule_invoice(schedule, invoice)
    report = generate_report(results)

    return {"report": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)