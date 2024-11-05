# Argus Codebase Export


## File: app.py

```
py


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


```


## File: index.html

```
html


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Argus - TV Ad Audit Tool</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f2f5;
        }
        .container {
            text-align: center;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #1a73e8;
        }
        p {
            margin-bottom: 20px;
        }
        .button {
            display: inline-block;
            background-color: #1a73e8;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        .button:hover {
            background-color: #1557b0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Argus - TV Ad Audit Tool</h1>
        <p>Welcome to Argus, your TV Ad Audit Tool. Click the button below to launch the application.</p>
        <a href="/app" class="button">Launch Argus</a>
    </div>
</body>
</html>

```


## File: style.css

```
css


@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;700&display=swap');

body {
    font-family: 'Manrope', sans-serif;
}

.stApp {
    max-width: 1200px;
    margin: 0 auto;
}

h1 {
    color: #2c3e50;
}

.stButton>button {
    background-color: #3498db;
    color: white;
}

.stTextInput>div>div>input {
    border-radius: 5px;
}

.stFileUploader>div>div>button {
    background-color: #2ecc71;
    color: white;
}


```


## File: config.py

```
py


# Date format
DATE_FORMAT = "%m-%d-%Y"  # Adjusted to match your CSV date format

# Time format
TIME_FORMAT = "%H:%M:%S"  # Adjusted to match your CSV time format

# Currency symbol
CURRENCY_SYMBOL = "$"

# Decimal places for monetary values
DECIMAL_PLACES = 2

# Number of weeks to process
WEEKS_TO_PROCESS = 4


```


## File: audit_logic.py

```
py


import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import DATE_FORMAT, TIME_FORMAT


def process_schedule(schedule_df):
    repeated_schedule = pd.concat([schedule_df] * 4, ignore_index=True)
    repeated_schedule["Week"] = repeated_schedule.index // len(schedule_df) + 1
    return repeated_schedule


def process_invoice(invoice_df):
    try:
        invoice_df["Date"] = pd.to_datetime(invoice_df["Date"], format="%m-%d-%Y")
    except ValueError as e:
        raise ValueError(f"Error parsing 'Date' column: {e}")

    # Get the earliest and latest dates in the invoice data
    min_date = invoice_df["Date"].min()
    
    # Ensure min_date starts at the beginning of the week (Monday)
    while min_date.weekday() != 0:  # 0 = Monday
        min_date = min_date - pd.Timedelta(days=1)
    
    # Define week boundaries starting from Monday
    week_starts = [min_date + pd.Timedelta(days=7 * i) for i in range(4)]
    week_ends = [start + pd.Timedelta(days=6) for start in week_starts]

    def assign_week(date):
        for i, (start, end) in enumerate(zip(week_starts, week_ends)):
            if start <= date <= end:
                return i + 1
        return None

    invoice_df["Week"] = invoice_df["Date"].apply(assign_week)

    # Remove rows where 'Week' is None
    invoice_df = invoice_df[invoice_df["Week"].notnull()]

    invoice_df["Time"] = pd.to_datetime(invoice_df["Time"], format="%H:%M:%S").dt.time

    # Store week start dates in the DataFrame, ensuring week numbers are integers
    invoice_df["WeekStart"] = invoice_df["Week"].apply(lambda x: week_starts[int(x - 1)] if pd.notnull(x) else None)

    return invoice_df


def parse_time(time_str):
    time_str = time_str.lower().strip()
    if ":" in time_str:
        # Handle cases like '7:59am' or '11:30 pm'
        return datetime.strptime(time_str, "%I:%M%p")
    elif time_str.endswith("am") or time_str.endswith("pm"):
        # Handle cases like '7am' or '11pm'
        return datetime.strptime(time_str, "%I%p")
    else:
        # Handle cases like '7:00' or '23:59'
        return datetime.strptime(time_str, "%H:%M")


def compare_schedule_invoice(schedule, invoice):
    results = {}
    networks = schedule["Network"].unique()

    for network in networks:
        network_schedule = schedule[schedule["Network"] == network]
        network_invoice = invoice[invoice["Network"] == network]

        for week_num in range(1, 5):
            week_schedule = network_schedule[network_schedule["Week"] == week_num]
            week_invoice = network_invoice[network_invoice["Week"] == week_num]
            
            # Get the week start date from any row in week_invoice
            week_start = None
            if not week_invoice.empty:
                week_start = week_invoice.iloc[0]["WeekStart"]

            timeslots = week_schedule["Time"].unique()
            week_results = []

            for timeslot in timeslots:
                slot_schedule = week_schedule[week_schedule["Time"] == timeslot]
                slot_start_time = parse_time(timeslot.split("-")[0])
                slot_end_time = parse_time(timeslot.split("-")[1])

                slot_start_with_tolerance = (
                    slot_start_time - timedelta(minutes=3)
                ).time()
                slot_end_with_tolerance = (slot_end_time + timedelta(minutes=3)).time()

                slot_invoice = week_invoice[
                    (week_invoice["Time"] >= slot_start_with_tolerance)
                    & (week_invoice["Time"] <= slot_end_with_tolerance)
                ]

                scheduled_spots = slot_schedule["Spots"].sum()
                scheduled_value = (
                    slot_schedule["Spots"] * slot_schedule["Cost"]
                ).sum()

                aired_spots = len(slot_invoice)
                pre_empted_spots = max(0, scheduled_spots - aired_spots)
                pre_empted_value = pre_empted_spots * slot_schedule["Cost"].iloc[0]

                extra_spots = max(0, aired_spots - scheduled_spots)
                extra_value = extra_spots * slot_schedule["Cost"].iloc[0]

                week_results.append(
                    {
                        "timeslot": timeslot.split("-")[0],
                        "scheduled_spots": scheduled_spots,
                        "scheduled_value": scheduled_value,
                        "aired_spots": aired_spots,
                        "pre_empted_spots": pre_empted_spots,
                        "pre_empted_value": pre_empted_value,
                        "extra_spots": extra_spots,
                        "extra_value": extra_value,
                    }
                )

            # Check for spots that aired outside their scheduled slots
            for _, spot in week_invoice.iterrows():
                spot_time = spot["Time"]
                scheduled_slot = None
                for timeslot in timeslots:
                    slot_start_time = parse_time(timeslot.split("-")[0])
                    slot_end_time = parse_time(timeslot.split("-")[1])
                    slot_start_with_tolerance = (slot_start_time - timedelta(minutes=3)).time()
                    slot_end_with_tolerance = (slot_end_time + timedelta(minutes=3)).time()
                    if slot_start_with_tolerance <= spot_time <= slot_end_with_tolerance:
                        scheduled_slot = timeslot
                        break

                if scheduled_slot is None:
                    # Spot aired outside of any scheduled slot
                    actual_slot = f"{spot_time.strftime('%I:%M %p')}-{(datetime.combine(datetime.min, spot_time) + timedelta(hours=1)).time().strftime('%I:%M %p')}"
                    for result in week_results:
                        if result["timeslot"] == actual_slot.split("-")[0]:
                            result["extra_spots"] += 1
                            result["extra_value"] += spot["Rate"]
                            break
                    else:
                        week_results.append(
                            {
                                "timeslot": actual_slot.split("-")[0],
                                "scheduled_spots": 0,
                                "scheduled_value": 0,
                                "aired_spots": 0,
                                "pre_empted_spots": 0,
                                "pre_empted_value": 0,
                                "extra_spots": 1,
                                "extra_value": spot["Rate"],
                            }
                        )

            if network not in results:
                results[network] = {
                    "total_pre_empted_spots": 0,
                    "total_pre_empted_value": 0,
                    "total_extra_spots": 0,
                    "total_extra_value": 0,
                    "weeks": [],
                }

            results[network]["total_pre_empted_spots"] += sum(
                slot["pre_empted_spots"] for slot in week_results
            )
            results[network]["total_pre_empted_value"] += sum(
                slot["pre_empted_value"] for slot in week_results
            )
            results[network]["total_extra_spots"] += sum(
                slot["extra_spots"] for slot in week_results
            )
            results[network]["total_extra_value"] += sum(
                slot["extra_value"] for slot in week_results
            )
            results[network]["weeks"].append(
                {
                    "week": week_num,
                    "start_date": week_start,
                    "slots": week_results,
                }
            )

    return results


def get_ordinal_suffix(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return suffix


def generate_report(results, invoice_df):
    report = []
    for network, data in results.items():
        network_report = [f"{network}"]
        for week in data["weeks"]:
            if week["start_date"] is None:
                continue
                
            week_start = week["start_date"]
            month = week_start.strftime("%B")
            day = week_start.day
            ordinal_suffix = get_ordinal_suffix(day)
            network_report.append(f"Week of {month} {day}{ordinal_suffix}")

            total_pre_empted = sum(
                slot["pre_empted_spots"] for slot in week["slots"]
            )
            total_pre_empted_value = sum(
                slot["pre_empted_value"] for slot in week["slots"]
            )

            for slot in week["slots"]:
                if slot["scheduled_spots"] > 0:
                    network_report.append(
                        f"{slot['scheduled_spots']} spot{'s' if slot['scheduled_spots'] > 1 else ''} {'were' if slot['scheduled_spots'] > 1 else 'was'} scheduled to run at {slot['timeslot']} at a value of ${slot['scheduled_value'] / slot['scheduled_spots']:.0f} each"
                    )

                if slot["pre_empted_spots"] > 0:
                    network_report.append(
                        f"{slot['pre_empted_spots']} spot{'s' if slot['pre_empted_spots'] > 1 else ''} {'were' if slot['pre_empted_spots'] > 1 else 'was'} pre-empted at a value of ${slot['pre_empted_value'] / slot['pre_empted_spots']:.0f}"
                    )
                elif slot["aired_spots"] == slot["scheduled_spots"]:
                    network_report.append(
                        f"Spots ran as scheduled at {slot['timeslot']}"
                    )

                if slot["extra_spots"] > 0:
                    network_report.append(
                        f"{slot['extra_spots']} extra spot{'s' if slot['extra_spots'] > 1 else ''} ran at {slot['timeslot']} at a value of ${slot['extra_value'] / slot['extra_spots']:.0f} each"
                    )

            if total_pre_empted == 0:
                network_report.append("Spots ran as scheduled")
                network_report.append("0 total spots were pre-empted")
                network_report.append("Total pre-empted value is $0")
            else:
                network_report.append(
                    f"{total_pre_empted} total spot{'s' if total_pre_empted > 1 else ''} {'were' if total_pre_empted > 1 else 'was'} pre-empted"
                )
                network_report.append(
                    f"Total pre-empted value is ${total_pre_empted_value:.0f}"
                )

            network_report.append("")  # Empty line between weeks

        network_report.extend(
            [
                f"Total pre-empted spots for {network} = {data['total_pre_empted_spots']}",
                f"Total pre-empted value for {network} = ${data['total_pre_empted_value']:.0f}",
                f"Total extra spots for {network} = {data['total_extra_spots']}",
                f"Total extra value for {network} = ${data['total_extra_value']:.0f}",
                "",  # Empty line between networks
            ]
        )
        report.extend(network_report)
    return report


```


## File: api/index.py

```
py


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


```


## File: requirements.txt

```
txt


streamlit==1.29.0
pandas==2.1.4
numpy==1.26.2


```


## File: vercel.json

```
json


{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "STREAMLIT_SERVER_PORT": "8080",
    "STREAMLIT_SERVER_HEADLESS": "true"
  }
}

```
