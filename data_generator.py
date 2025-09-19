import pandas as pd
import numpy as np
from datetime import date, timedelta
import random
import json

# --- CONFIGURATION ---
NUM_TRAINS = 24
FLEET_IDS = [f"CR{101 + i}" for i in range(NUM_TRAINS)]
START_DATE = date(2025, 8, 1)
SIMULATION_DAYS = 45

def generate_fleet_data():
    """
    Generates a complete dataset including detailed usage stats for the mileage service.
    """
    print("Generating synthetic KMRL fleet data for all modules...")
    
    # (Static Info, Branding, Depot Layout, Cleaning Schedule code remains the same as before...)
    
    # --- Static Train Information ---
    static_info = [{"Train_ID": train_id, "Model": f"Alstom M{random.randint(1,3)}"} for train_id in FLEET_IDS]
    pd.DataFrame(static_info).to_csv("fleet_static_info.csv", index=False)
    print("✅ fleet_static_info.csv generated.")

    # --- Branding Contracts ---
    branding_data = [
        {"Contract_ID": 101, "Train_ID": "CR102", "Advertiser": "Lulu Mall"},
        {"Contract_ID": 102, "Train_ID": "CR105", "Advertiser": "MyG"},
    ]
    pd.DataFrame(branding_data).to_csv("branding_contracts.csv", index=False)
    print("✅ branding_contracts.csv generated.")

    # --- Depot Layout ---
    depot_layout = { "Maintenance Bay": [f"M-{i}" for i in range(1, 5)], "Standard Stabling": [f"S-{i}" for i in range(1, 22)], "Cleaning Bay": ["C-1", "C-2"] }
    with open('depot_layout.json', 'w') as f: json.dump(depot_layout, f, indent=4)
    print("✅ depot_layout.json generated.")

    # --- Cleaning Schedule ---
    cleaning_data = []
    for i in range(SIMULATION_DAYS):
        current_date = START_DATE + timedelta(days=i)
        trains_to_clean = random.sample(FLEET_IDS, 2)
        for train_id in trains_to_clean:
            cleaning_data.append({"Date": current_date, "Train_ID": train_id})
    pd.DataFrame(cleaning_data).to_csv("cleaning_schedule.csv", index=False)
    print("✅ cleaning_schedule.csv generated.")

    # --- NEW: Daily Usage Stats for the Mileage Service ---
    usage_log = []
    fleet_usage = {
        train_id: {
            "Bogie_Mileage": random.uniform(5000, 80000),
            "BrakePad_Mileage": random.uniform(1000, 40000),
            "HVAC_Hours": random.uniform(1000, 20000)
        } for train_id in FLEET_IDS
    }
    # Make one train overused for the demo
    fleet_usage["CR107"]["Bogie_Mileage"] = 95000

    for i in range(SIMULATION_DAYS):
        current_date = START_DATE + timedelta(days=i)
        daily_snapshot = []
        for train_id in FLEET_IDS:
            usage = fleet_usage[train_id]
            # Simulate daily usage increase
            usage["Bogie_Mileage"] += random.uniform(450, 600)
            usage["BrakePad_Mileage"] += random.uniform(450, 600)
            usage["HVAC_Hours"] += random.uniform(12, 18)
            
            row = {"Date": current_date.strftime("%Y-%m-%d"), "Train_ID": train_id}
            row.update({k: round(v) for k, v in usage.items()})
            daily_snapshot.append(row)
        usage_log.extend(daily_snapshot)

    usage_df = pd.DataFrame(usage_log)
    usage_df.to_csv("fleet_usage_log.csv", index=False)
    print("✅ fleet_usage_log.csv generated (for Mileage Service).")
    print("\nAll data files generated successfully!")

if __name__ == "__main__":
    generate_fleet_data()

