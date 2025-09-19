import pandas as pd
import joblib
from datetime import datetime

class Train:
    """A class to hold all information and decisions about a single train."""
    def __init__(self, train_id, mileage):
        self.id = train_id
        self.mileage = mileage
        self.is_branded = False
        self.needs_cleaning = False
        self.failure_probability = 0.0
        self.health_status = "Healthy"
        self.decision = "Standby"
        self.reason = "Default"
        self.stabling_track = "Not Assigned"

def load_all_data(selected_date):
    """Loads all necessary data files for a given date."""
    telemetry_df = pd.read_csv("fleet_health_log.csv")
    branding_df = pd.read_csv("branding_contracts.csv")
    cleaning_df = pd.read_csv("cleaning_schedule.csv")
    
    # Filter data for the selected day
    today_telemetry = telemetry_df[telemetry_df['timestamp'] == selected_date.strftime("%Y-%m-%d")]
    today_cleaning = cleaning_df[cleaning_df['Date'] == selected_date.strftime("%Y-%m-%d")]
    
    return today_telemetry, branding_df, today_cleaning

def initialize_fleet(today_data, branding_df, cleaning_df):
    """Initializes a dictionary of Train objects with branding and cleaning info."""
    fleet = {}
    for _, row in today_data.iterrows():
        train_id = row['Train_ID']
        train = Train(train_id, row['mileage'])
        if train_id in branding_df['Train_ID'].values:
            train.is_branded = True
        if train_id in cleaning_df['Train_ID'].values:
            train.needs_cleaning = True
        fleet[train_id] = train
    return fleet

def run_predictive_maintenance(fleet, today_data):
    """Scores fleet health using the pre-trained PdM model."""
    try:
        model = joblib.load('pdm_model.pkl')
    except FileNotFoundError:
        raise Exception("Model 'pdm_model.pkl' not found. Please run predictive_maintenance.py first.")

    # Engineer features for the current day's data
    data = today_data.copy()
    # In a real-time scenario, we'd calculate rolling averages from historical data.
    # For this daily snapshot, we use the current values as a proxy.
    data['motor_current_avg_3d'] = data['motor_current']
    data['oil_temp_avg_3d'] = data['oil_temperature']
    data['dv_pressure_avg_3d'] = data['dv_pressure']
    
    features = ['motor_current_avg_3d', 'oil_temp_avg_3d', 'dv_pressure_avg_3d', 'mileage']
    X_today = data.set_index('Train_ID')[features]
    
    # Predict failure probability for all trains at once
    probabilities = model.predict_proba(X_today)[:, 1]
    
    for train_id, prob in zip(X_today.index, probabilities):
        if train_id in fleet:
            fleet[train_id].failure_probability = prob
            if prob > 0.6: # Risk threshold
                fleet[train_id].health_status = "At Risk"

def run_induction_planner(fleet):
    """
    Decides which trains to run, maintain, or keep on standby based on a hierarchy of rules.
    """
    SERVICE_REQUIREMENT = 18 # Total number of trains needed for the next day's service

    # Rule 1: 'At Risk' trains are prioritized for maintenance
    for train in fleet.values():
        if train.health_status == "At Risk":
            train.decision = "Needs Maintenance"
            train.reason = f"High failure risk ({train.failure_probability:.0%})"

    # Rule 2: Branded trains MUST run if they are healthy
    branded_trains = sorted([t for t in fleet.values() if t.is_branded], key=lambda x: x.failure_probability)
    for train in branded_trains:
        if train.decision != "Needs Maintenance":
            train.decision = "Run (Branding)"
            train.reason = "Advertising contract"

    # Rule 3: Fill remaining service slots with the healthiest, lowest-mileage trains
    eligible_trains = [t for t in fleet.values() if t.decision == "Standby"]
    eligible_trains.sort(key=lambda x: (x.failure_probability, x.mileage)) # Sort by health, then mileage
    
    slots_filled = len([t for t in fleet.values() if "Run" in t.decision])
    slots_to_fill = SERVICE_REQUIREMENT - slots_filled
    
    for i in range(min(slots_to_fill, len(eligible_trains))):
        train = eligible_trains[i]
        train.decision = "Run (Mileage Balance)"
        train.reason = "Low mileage & healthy"

def run_stabling_planner(fleet, depot_layout):
    """Assigns each train to a stabling track based on its final decision."""
    maintenance_tracks = depot_layout["Maintenance Bay"][:]
    cleaning_tracks = depot_layout["Cleaning Bay"][:]
    standard_tracks = depot_layout["Standard Stabling"][:]
    
    # Sort trains for efficient parking (maintenance/cleaning first, then high-priority runs)
    trains_sorted = sorted(fleet.values(), key=lambda x: (x.decision != "Needs Maintenance", x.needs_cleaning, "Run" not in x.decision, x.mileage))

    for train in trains_sorted:
        if train.decision == "Needs Maintenance":
            if maintenance_tracks: train.stabling_track = maintenance_tracks.pop(0)
            else: train.stabling_track = "OVERFLOW"
        elif train.needs_cleaning:
            if cleaning_tracks: train.stabling_track = cleaning_tracks.pop(0)
            elif standard_tracks: train.stabling_track = standard_tracks.pop(0) # Use standard if cleaning is full
            else: train.stabling_track = "OVERFLOW"
        elif "Run" in train.decision:
            if standard_tracks: train.stabling_track = standard_tracks.pop(0) # Front spots for easy exit
            else: train.stabling_track = "OVERFLOW"
        else: # Standby trains
            if standard_tracks: train.stabling_track = standard_tracks.pop(-1) # Back spots
            else: train.stabling_track = "OVERFLOW"

