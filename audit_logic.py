import pandas as pd
from datetime import datetime, timedelta

def process_schedule(schedule_df):
    repeated_schedule = pd.concat([schedule_df] * 4, ignore_index=True)
    repeated_schedule['Week'] = repeated_schedule.index // len(schedule_df) + 1
    return repeated_schedule

def process_invoice(invoice_df):
    invoice_df['Date'] = pd.to_datetime(invoice_df['Date'], format='%m-%d-%Y')
    invoice_df['Week'] = (invoice_df['Date'].dt.day - 1) // 7 + 1
    invoice_df['Time'] = pd.to_datetime(invoice_df['Time']).dt.strftime('%I:%M %p').str.lower()
    return invoice_df

def compare_schedule_invoice(schedule, invoice):
    results = {}
    networks = schedule['Network'].unique()

    for network in networks:
        network_schedule = schedule[schedule['Network'] == network]
        network_invoice = invoice[invoice['Network'] == network]

        for week in range(1, 5):
            week_schedule = network_schedule[network_schedule['Week'] == week]
            week_invoice = network_invoice[network_invoice['Week'] == week]

            timeslots = week_schedule['Time'].unique()
            week_results = []

            for timeslot in timeslots:
                slot_schedule = week_schedule[week_schedule['Time'] == timeslot]
                slot_invoice = week_invoice[week_invoice['Time'].str.startswith(timeslot.split('-')[0])]

                scheduled_spots = slot_schedule['Spots'].sum()
                scheduled_value = (slot_schedule['Spots'] * slot_schedule['Cost']).sum()

                aired_spots = len(slot_invoice)
                pre_empted_spots = max(0, scheduled_spots - aired_spots)
                pre_empted_value = pre_empted_spots * slot_schedule['Cost'].iloc[0]

                week_results.append({
                    'timeslot': timeslot.split('-')[0],
                    'scheduled_spots': scheduled_spots,
                    'scheduled_value': scheduled_value,
                    'pre_empted_spots': pre_empted_spots,
                    'pre_empted_value': pre_empted_value
                })

            if network not in results:
                results[network] = {'total_pre_empted_spots': 0, 'total_pre_empted_value': 0, 'weeks': []}

            results[network]['total_pre_empted_spots'] += sum(slot['pre_empted_spots'] for slot in week_results)
            results[network]['total_pre_empted_value'] += sum(slot['pre_empted_value'] for slot in week_results)
            results[network]['weeks'].append({
                'week': week,
                'slots': week_results
            })

    return results

def get_ordinal_suffix(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return suffix

def generate_report(results):
    report = []
    for network, data in results.items():
        network_report = [f"{network}"]
        for week in data['weeks']:
            week_start = 1 + (week['week'] - 1) * 7
            ordinal_suffix = get_ordinal_suffix(week_start)
            network_report.append(f"Week of April {week_start}{ordinal_suffix}")
            
            total_pre_empted = sum(slot['pre_empted_spots'] for slot in week['slots'])
            total_pre_empted_value = sum(slot['pre_empted_value'] for slot in week['slots'])
            
            all_spots_ran = all(slot['pre_empted_spots'] == 0 for slot in week['slots'])
            
            for slot in week['slots']:
                if slot['scheduled_spots'] > 0:
                    network_report.append(f"{slot['scheduled_spots']} spot{'s' if slot['scheduled_spots'] > 1 else ''} were scheduled to run at {slot['timeslot']} at a value of ${slot['scheduled_value'] / slot['scheduled_spots']:.0f} each")
                if slot['pre_empted_spots'] > 0:
                    network_report.append(f"{slot['pre_empted_spots']} spot{'s were' if slot['pre_empted_spots'] > 1 else ' was'} pre-empted at a value of ${slot['pre_empted_value'] / slot['pre_empted_spots']:.0f} each")
            
            if all_spots_ran:
                network_report.append("Spots ran as scheduled")
            else:
                network_report.append(f"{total_pre_empted} total spot{'s were' if total_pre_empted > 1 else ' was'} pre-empted")
                network_report.append(f"Total pre-empted value is ${total_pre_empted_value:.0f}")
            
            network_report.append("")  # Empty line between weeks
        
        network_report.extend([
            f"Total pre-empted spots for {network} = {data['total_pre_empted_spots']}",
            f"Total pre-empted value for {network} = ${data['total_pre_empted_value']:.0f}",
            f"Total extra Spots for {network} = 0",
            f"Total extra value for {network} = $0",
            ""  # Empty line between networks
        ])
        report.extend(network_report)
    return report
