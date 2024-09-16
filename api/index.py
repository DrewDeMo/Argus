from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
from audit_logic import (
    process_schedule,
    process_invoice,
    compare_schedule_invoice,
    generate_report,
    parse_time,
)

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
    invoice_df = pd.read_csv(StringIO(invoice_content.decode("utf-8")))

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
    report = generate_report(results)

    return {"report": report}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
