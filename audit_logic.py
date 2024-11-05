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
