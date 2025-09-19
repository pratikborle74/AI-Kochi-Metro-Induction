import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import random
import json
import uuid

# --- CONFIGURATION ---
NUM_TRAINS = 25  # Updated to match problem statement (25 four-car trainsets)
FLEET_IDS = [f"CR{101 + i}" for i in range(NUM_TRAINS)]
START_DATE = date(2025, 1, 15)  # Current simulation period
SIMULATION_DAYS = 30
CURRENT_DATE = date(2025, 1, 20)  # Today's date for decision making

# KMRL-specific configurations
DEPARTMENTS = ["Rolling_Stock", "Signalling", "Telecom"]
MAXIMO_WORK_ORDER_TYPES = ["PM-Bogie", "PM-Brake", "PM-HVAC", "CM-Electrical", "CM-Mechanical", "Inspection-A", "Inspection-B"]
CLEANING_TYPES = ["Interior_Deep_Clean", "Exterior_Wash", "HVAC_Filter", "Window_Polish"]
STABLING_BAYS = {
    "IBL_Maintenance": ["IBL-1", "IBL-2", "IBL-3", "IBL-4", "IBL-5"],  # Inspection Bay Line
    "Cleaning_Bays": ["CB-1", "CB-2", "CB-3"],
    "Standard_Stabling": [f"SB-{i}" for i in range(1, 18)],
    "Standby_Ready": [f"RB-{i}" for i in range(1, 8)]
}

# Import advanced depot management
try:
    from depot_manager import load_depot, find_efficient_path
    ADVANCED_DEPOT_AVAILABLE = True
except ImportError:
    ADVANCED_DEPOT_AVAILABLE = False
    print("⚠️ Advanced depot manager not available, using basic stabling")

# Advertising contracts with industry-standard service hour requirements
# KMRL service hours: 5:30 AM - 11:00 PM (17.5 hours total)
BRANDING_CONTRACTS = [
    {"Contract_ID": "BRD-001", "Advertiser": "Lulu Mall", "Train_ID": "CR102", "Min_Hours_Daily": 15.5, "Contract_Value": 750000, "Penalty_Per_Hour": 2500},
    {"Contract_ID": "BRD-002", "Advertiser": "MyG Digital", "Train_ID": "CR105", "Min_Hours_Daily": 14.0, "Contract_Value": 600000, "Penalty_Per_Hour": 2000},
    {"Contract_ID": "BRD-003", "Advertiser": "Federal Bank", "Train_ID": "CR108", "Min_Hours_Daily": 16.0, "Contract_Value": 800000, "Penalty_Per_Hour": 3000},
    {"Contract_ID": "BRD-004", "Advertiser": "Kerala Tourism", "Train_ID": "CR112", "Min_Hours_Daily": 13.5, "Contract_Value": 500000, "Penalty_Per_Hour": 1500},
]

# Research-based certificate validity periods (Industry Standards)
CERT_VALIDITY_DAYS = {
    "Rolling_Stock": 365,    # 12 months (Indian Railways Act 1989, Section 113)
    "Signalling": 180,       # 6 months (RDSO Guidelines for Metro Rail)
    "Telecom": 90            # 3 months (TRAI regulations for metro systems)
}

# Renewal windows for different certificate types
RENEWAL_WINDOWS = {
    "Rolling_Stock": (30, 45),  # 30-45 days before expiry
    "Signalling": (15, 30),     # 15-30 days before expiry  
    "Telecom": (7, 15)          # 7-15 days before expiry
}

def generate_fitness_certificates():
    """
    Variable 1: Fitness Certificates from Rolling-Stock, Signalling, Telecom departments
    Updated with industry-standard validity periods and realistic operational scenarios
    """
    certificates = []
    
    for train_id in FLEET_IDS:
        for dept in DEPARTMENTS:
            # Use industry-standard validity periods
            validity_days = CERT_VALIDITY_DAYS[dept]
            renewal_window = RENEWAL_WINDOWS[dept]
            
            # Generate realistic issue dates based on certificate lifecycle
            if dept == "Rolling_Stock":
                # Annual certification - could be issued anytime in past year
                days_since_issue = random.randint(0, 365)
            elif dept == "Signalling":
                # Semi-annual certification - could be issued anytime in past 6 months
                days_since_issue = random.randint(0, 180)
            else:  # Telecom
                # Quarterly certification - could be issued anytime in past 3 months
                days_since_issue = random.randint(0, 90)
            
            issue_date = CURRENT_DATE - timedelta(days=days_since_issue)
            expiry_date = issue_date + timedelta(days=validity_days)
            
            # Realistic certificate status distribution (industry standards)
            status_random = random.random()
            
            if status_random < 0.10:  # 10% expired (realistic operational scenario)
                # Certificate expired recently
                days_expired = random.randint(1, 30)
                expiry_date = CURRENT_DATE - timedelta(days=days_expired)
                cert_status = "Expired"
            elif status_random < 0.15:  # 5% in renewal process
                # Certificate near expiry, renewal in progress
                days_to_expiry = random.randint(renewal_window[0], renewal_window[1])
                expiry_date = CURRENT_DATE + timedelta(days=days_to_expiry)
                cert_status = "Renewal_In_Progress"
            elif status_random < 0.18:  # 3% pending (new trains or major maintenance)
                cert_status = "Pending"
                expiry_date = None
            else:  # 82% valid (healthy operational state)
                cert_status = "Valid"
                
            # Enhanced certificate record with industry-standard information
            certificates.append({
                "Certificate_ID": f"CERT-{dept[:3].upper()}-{train_id}-{uuid.uuid4().hex[:6]}",
                "Train_ID": train_id,
                "Department": dept,
                "Issue_Date": issue_date.strftime("%Y-%m-%d"),
                "Expiry_Date": expiry_date.strftime("%Y-%m-%d") if expiry_date else None,
                "Validity_Days": validity_days,
                "Status": cert_status,
                "Inspector": f"{dept}_Inspector_{random.randint(1, 8)}",  # More inspectors for realism
                "Priority": "Critical" if cert_status in ["Expired", "Pending"] else "Medium",
                "Inspection_Type": "Annual" if dept == "Rolling_Stock" else "Semi_Annual" if dept == "Signalling" else "Quarterly",
                "Renewal_Window_Days": f"{renewal_window[0]}-{renewal_window[1]}",
                "Notes": f"Certificate for {dept.lower()} systems - {validity_days} day validity period"
            })
    
    return pd.DataFrame(certificates)

def generate_maximo_job_cards():
    """
    Variable 2: Job-Card Status from IBM Maximo exports
    """
    job_cards = []
    
    for train_id in FLEET_IDS:
        # Generate 1-4 job cards per train
        num_jobs = random.randint(1, 4)
        
        for _ in range(num_jobs):
            created_date = CURRENT_DATE - timedelta(days=random.randint(1, 45))
            
            work_type = random.choice(MAXIMO_WORK_ORDER_TYPES)
            priority = random.choice(["Critical", "High", "Medium", "Low"])
            
            # Determine status based on age and priority
            age_days = (CURRENT_DATE - created_date).days
            if priority == "Critical":
                status = "Open" if age_days < 2 else "In_Progress"
            elif priority == "High":
                status = random.choice(["Open", "In_Progress", "Closed"]) if age_days < 7 else "Closed"
            else:
                status = random.choice(["Open", "In_Progress", "Closed", "On_Hold"])
            
            # Estimated hours based on work type
            est_hours = {
                "PM-Bogie": random.randint(8, 16),
                "PM-Brake": random.randint(4, 8),
                "PM-HVAC": random.randint(6, 12),
                "CM-Electrical": random.randint(2, 24),
                "CM-Mechanical": random.randint(4, 20),
                "Inspection-A": random.randint(6, 10),
                "Inspection-B": random.randint(12, 20)
            }.get(work_type, random.randint(2, 12))
            
            job_cards.append({
                "Work_Order_ID": f"WO-{uuid.uuid4().hex[:8].upper()}",
                "Train_ID": train_id,
                "Work_Type": work_type,
                "Description": f"{work_type.replace('-', ' ')} for {train_id}",
                "Priority": priority,
                "Status": status,
                "Created_Date": created_date.strftime("%Y-%m-%d"),
                "Due_Date": (created_date + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
                "Estimated_Hours": est_hours,
                "Assigned_Technician": f"Tech_{random.randint(1, 20)}",
                "Department": random.choice(["Maintenance", "Electrical", "Mechanical"]),
                "Cost_Estimate": est_hours * random.randint(50, 150),
                "Notes": f"Maximo-generated work order for {work_type}"
            })
    
    return pd.DataFrame(job_cards)

def generate_enhanced_branding_data():
    """
    Variable 3: Enhanced Branding Priorities with contractual commitments
    """
    branding_data = []
    
    for contract in BRANDING_CONTRACTS:
        # Generate historical performance data
        for i in range(7):  # Last 7 days
            date_check = CURRENT_DATE - timedelta(days=i)
            # Realistic service hours: KMRL operates 5:30 AM - 11:00 PM (17.5 hours)
            # Most trains achieve 14-17 hours of service (some downtime for maintenance/delays)
            base_service_hours = 16.5  # Standard service day
            actual_hours = base_service_hours + random.uniform(-2.5, +1.0)  # 14-17.5 hour range
            
            # Calculate compliance
            shortfall = max(0, contract["Min_Hours_Daily"] - actual_hours)
            penalty_incurred = shortfall * contract["Penalty_Per_Hour"]
            compliance_pct = min(100, (actual_hours / contract["Min_Hours_Daily"]) * 100)
            
            branding_data.append({
                "Contract_ID": contract["Contract_ID"],
                "Train_ID": contract["Train_ID"],
                "Advertiser": contract["Advertiser"],
                "Date": date_check.strftime("%Y-%m-%d"),
                "Required_Hours": contract["Min_Hours_Daily"],
                "Actual_Hours": round(actual_hours, 1),
                "Compliance_Percentage": round(compliance_pct, 1),
                "Shortfall_Hours": round(shortfall, 1),
                "Penalty_Incurred": round(penalty_incurred, 0),
                "Contract_Value": contract["Contract_Value"],
                "Status": "Compliant" if shortfall == 0 else "At_Risk",
                "Priority": "Critical" if shortfall > 2 else "High" if shortfall > 0 else "Normal"
            })
    
    return pd.DataFrame(branding_data)

def generate_mileage_balancing_data():
    """
    Variable 4: Enhanced Mileage Balancing for component wear equalization
    """
    mileage_data = []
    
    # Industry-standard component service life limits (Based on Alstom Metropolis Manual)
    service_limits = {
        "Bogie_Mileage": 900000,        # 800K-1M km (manufacturer specifications)
        "BrakePad_Mileage": 65000,      # 50K-80K km typical
        "HVAC_Hours": 18000,            # 15K-20K hours for compressor
        "Motor_Hours": 18000,           # Based on DMRC experience
        "Traction_Mileage": 800000      # Traction motor life cycle
    }
    
    # Initialize fleet with realistic wear distribution
    fleet_wear = {}
    for train_id in FLEET_IDS:
        # Generate realistic wear levels (most trains should be in good condition)
        wear_factor = random.uniform(0.1, 0.7)  # Most trains at 10-70% wear
        
        fleet_wear[train_id] = {
            "Bogie_Mileage": int(service_limits["Bogie_Mileage"] * wear_factor),
            "BrakePad_Mileage": int(service_limits["BrakePad_Mileage"] * wear_factor),
            "HVAC_Hours": int(service_limits["HVAC_Hours"] * wear_factor),
            "Motor_Hours": int(service_limits["Motor_Hours"] * wear_factor),
            "Traction_Mileage": int(service_limits["Traction_Mileage"] * wear_factor)
        }
    
    # Create some high-wear trains for realistic maintenance scenarios (but not all)
    high_wear_trains = random.sample(FLEET_IDS, 3)  # Only 3 trains with high wear
    for train_id in high_wear_trains:
        high_wear_factor = random.uniform(0.85, 0.95)  # 85-95% wear for maintenance cases
        fleet_wear[train_id] = {
            "Bogie_Mileage": int(service_limits["Bogie_Mileage"] * high_wear_factor),
            "BrakePad_Mileage": int(service_limits["BrakePad_Mileage"] * high_wear_factor),
            "HVAC_Hours": int(service_limits["HVAC_Hours"] * high_wear_factor),
            "Motor_Hours": int(service_limits["Motor_Hours"] * high_wear_factor),
            "Traction_Mileage": int(service_limits["Traction_Mileage"] * high_wear_factor)
        }
    
    for train_id in FLEET_IDS:
        wear = fleet_wear[train_id]
        
        # Calculate usage percentages and remaining life
        usage_analysis = {}
        critical_components = []
        
        for component, current_usage in wear.items():
            limit = service_limits[component]
            usage_pct = (current_usage / limit) * 100
            remaining_life = limit - current_usage
            
            if usage_pct > 90:
                status = "Critical"
                critical_components.append(component)
            elif usage_pct > 75:
                status = "High_Wear"
            elif usage_pct > 50:
                status = "Moderate_Wear"
            else:
                status = "Low_Wear"
            
            usage_analysis[component] = {
                "Current_Usage": round(current_usage, 0),
                "Usage_Percentage": round(usage_pct, 1),
                "Remaining_Life": round(remaining_life, 0),
                "Status": status,
                "Days_To_Limit": round(remaining_life / 500, 0) if remaining_life > 0 else 0  # Assuming 500 km/day average
            }
        
        # Overall mileage balancing priority
        avg_usage = np.mean([usage_analysis[comp]["Usage_Percentage"] for comp in usage_analysis])
        
        if critical_components:
            priority = "Critical"
            recommendation = "Immediate_Maintenance"
        elif avg_usage > 80:
            priority = "High"
            recommendation = "Reduce_Service_Hours"
        elif avg_usage < 30:
            priority = "Low"
            recommendation = "Increase_Service_Hours"
        else:
            priority = "Medium"
            recommendation = "Maintain_Current_Schedule"
        
        mileage_data.append({
            "Train_ID": train_id,
            "Date": CURRENT_DATE.strftime("%Y-%m-%d"),
            "Bogie_Usage_Pct": usage_analysis["Bogie_Mileage"]["Usage_Percentage"],
            "BrakePad_Usage_Pct": usage_analysis["BrakePad_Mileage"]["Usage_Percentage"],
            "HVAC_Usage_Pct": usage_analysis["HVAC_Hours"]["Usage_Percentage"],
            "Motor_Usage_Pct": usage_analysis["Motor_Hours"]["Usage_Percentage"],
            "Average_Usage_Pct": round(avg_usage, 1),
            "Critical_Components": ",".join(critical_components),
            "Priority": priority,
            "Recommendation": recommendation,
            "Balancing_Score": round(100 - np.std([usage_analysis[comp]["Usage_Percentage"] for comp in usage_analysis]), 1),
            "Notes": f"Balancing required: {len(critical_components)} critical components"
        })
    
    return pd.DataFrame(mileage_data)

def generate_cleaning_detailing_schedule():
    """
    Variable 5: Cleaning & Detailing with manpower and bay constraints
    """
    cleaning_data = []
    
    # Available cleaning resources
    cleaning_crews = {
        "Interior_Team_A": {"capacity": 2, "efficiency": 1.2},
        "Interior_Team_B": {"capacity": 2, "efficiency": 1.0},
        "Exterior_Team_A": {"capacity": 3, "efficiency": 1.1},
        "HVAC_Specialist": {"capacity": 1, "efficiency": 1.5}
    }
    
    # Generate cleaning schedule for next 7 days
    for day_offset in range(7):
        schedule_date = CURRENT_DATE + timedelta(days=day_offset)
        
        # Determine daily cleaning capacity
        daily_capacity = {
            "Interior_Deep_Clean": 4,  # 2 bays × 2 teams
            "Exterior_Wash": 6,        # Can do multiple trains
            "HVAC_Filter": 2,          # Specialized work
            "Window_Polish": 3
        }
        
        # Assign trains based on priority
        trains_needing_cleaning = random.sample(FLEET_IDS, random.randint(3, 8))
        
        for i, train_id in enumerate(trains_needing_cleaning):
            if i >= sum(daily_capacity.values()):  # Capacity constraint
                break
                
            cleaning_type = random.choice(CLEANING_TYPES)
            
            # Estimate duration based on type
            duration_hours = {
                "Interior_Deep_Clean": random.uniform(4, 8),
                "Exterior_Wash": random.uniform(1, 3),
                "HVAC_Filter": random.uniform(3, 6),
                "Window_Polish": random.uniform(2, 4)
            }[cleaning_type]
            
            # Assign bay and crew
            if cleaning_type == "Interior_Deep_Clean":
                assigned_bay = random.choice(STABLING_BAYS["Cleaning_Bays"])
                crew = random.choice(["Interior_Team_A", "Interior_Team_B"])
            else:
                assigned_bay = random.choice(STABLING_BAYS["Standard_Stabling"][:5])
                crew = random.choice(["Exterior_Team_A", "HVAC_Specialist"])
            
            # Priority based on last cleaning date
            last_cleaned_days = random.randint(1, 14)
            if last_cleaned_days > 10:
                priority = "High"
            elif last_cleaned_days > 7:
                priority = "Medium"
            else:
                priority = "Low"
            
            cleaning_data.append({
                "Schedule_ID": f"CLN-{schedule_date.strftime('%Y%m%d')}-{train_id}",
                "Train_ID": train_id,
                "Date": schedule_date.strftime("%Y-%m-%d"),
                "Cleaning_Type": cleaning_type,
                "Assigned_Bay": assigned_bay,
                "Assigned_Crew": crew,
                "Estimated_Duration_Hours": round(duration_hours, 1),
                "Priority": priority,
                "Status": random.choice(["Scheduled", "In_Progress", "Completed", "Delayed"]),
                "Last_Cleaned_Days_Ago": last_cleaned_days,
                "Notes": f"{cleaning_type} scheduled for bay {assigned_bay}"
            })
    
    return pd.DataFrame(cleaning_data)

def generate_stabling_geometry_data():
    """
    Variable 6: Enhanced Stabling Geometry optimization with real depot pathfinding
    """
    if ADVANCED_DEPOT_AVAILABLE:
        return generate_advanced_stabling_geometry()
    else:
        return generate_basic_stabling_geometry()

def generate_advanced_stabling_geometry():
    """
    Advanced stabling geometry using real Muttom depot layout with pathfinding
    """
    depot_data = load_depot()
    tracks = depot_data.get('tracks', [])
    
    # Filter available operational tracks
    available_tracks = [t for t in tracks if t['status'] in ['OPERATIONAL']]
    stabling_tracks = [t for t in available_tracks if 'Stabling' in t['type']]
    
    stabling_data = []
    assigned_tracks = random.sample(stabling_tracks, min(NUM_TRAINS, len(stabling_tracks)))
    
    for i, train_id in enumerate(FLEET_IDS):
        if i < len(assigned_tracks):
            track = assigned_tracks[i]
            track_id = track['trackId']
            
            # Calculate optimal path to mainline
            path_result = find_efficient_path(depot_data, track_id, 'MAINLINE_IN')
            
            if path_result:
                path_distance = path_result['total_cost_metres']
                path_switches = len([x for x in path_result['path'] if 'SW-' in x])
                shunting_time = max(5, path_switches * 3 + path_distance // 50)  # Realistic timing
                energy_cost = path_distance * 2 + path_switches * 50  # Distance + switch costs
            else:
                path_distance = 500  # Default for unreachable tracks
                path_switches = 0   # No switches if no path found
                shunting_time = 30
                energy_cost = 1000
            
            # Determine tomorrow's optimal track based on service prediction
            tomorrow_status = random.choice(["Service", "Maintenance", "Standby", "Cleaning"])
            
            # Find optimal track for tomorrow's status
            if tomorrow_status == "Service":
                optimal_tracks = [t for t in available_tracks if t['trackId'] == 'MAINLINE_IN']
            elif tomorrow_status == "Maintenance":
                optimal_tracks = [t for t in available_tracks if 'IBL' in t['trackId'] or 'WB' in t['trackId']]
            elif tomorrow_status == "Cleaning":
                optimal_tracks = [t for t in available_tracks if 'WPL' in t['trackId']]
            else:
                optimal_tracks = stabling_tracks
            
            needs_reallocation = len(optimal_tracks) > 0 and track not in optimal_tracks
            
            stabling_data.append({
                "Train_ID": train_id,
                "Current_Track_ID": track_id,
                "Current_Track_Type": track['type'],
                "Track_Capacity_Cars": track['capacityCars'],
                "Distance_To_Mainline_M": path_distance,
                "Path_To_Mainline": str(path_result['path']) if path_result else 'No path',
                "Switches_Required": path_switches if path_result else 0,
                "Shunting_Time_Minutes": shunting_time,
                "Energy_Cost_INR": energy_cost,
                "Tomorrow_Status": tomorrow_status,
                "Needs_Reallocation": needs_reallocation,
                "Reallocation_Priority": "High" if energy_cost > 800 else "Medium" if needs_reallocation else "Low",
                "Track_Status": track['status'],
                "Connected_Switches": str(track.get('connectedSwitches', [])),
                "Accessibility_Score": 5 - min(4, path_switches),  # Fewer switches = better access
                "Notes": f"Real depot track {track_id} with {path_switches} switch movements"
            })
        else:
            # Handle excess trains (more trains than stabling tracks)
            stabling_data.append({
                "Train_ID": train_id,
                "Current_Track_ID": "OVERFLOW",
                "Current_Track_Type": "Temporary",
                "Track_Capacity_Cars": 0,
                "Distance_To_Mainline_M": 1000,
                "Path_To_Mainline": "Requires special handling",
                "Switches_Required": 5,
                "Shunting_Time_Minutes": 45,
                "Energy_Cost_INR": 2000,
                "Tomorrow_Status": "Standby",
                "Needs_Reallocation": True,
                "Reallocation_Priority": "Critical",
                "Track_Status": "OVERFLOW",
                "Connected_Switches": "[]",
                "Accessibility_Score": 1,
                "Notes": f"Overflow train {train_id} - requires immediate reallocation"
            })
    
    return pd.DataFrame(stabling_data)

def generate_basic_stabling_geometry():
    """
    Basic stabling geometry (fallback if advanced depot not available)
    """
    # Current stabling positions (as of last night)
    current_positions = {}
    all_bays = []
    for bay_type, bays in STABLING_BAYS.items():
        all_bays.extend(bays)
    
    # Assign current positions
    assigned_bays = random.sample(all_bays, NUM_TRAINS)
    for i, train_id in enumerate(FLEET_IDS):
        current_positions[train_id] = assigned_bays[i]
    
    stabling_data = []
    
    for train_id in FLEET_IDS:
        current_bay = current_positions[train_id]
        
        # Determine bay type and accessibility
        bay_type = None
        for bt, bays in STABLING_BAYS.items():
            if current_bay in bays:
                bay_type = bt
                break
        
        # Calculate accessibility metrics
        if "IBL" in current_bay:
            accessibility_score = 3  # Easy for maintenance
            exit_time_minutes = random.randint(15, 25)
        elif "CB" in current_bay:
            accessibility_score = 4  # Good for cleaning
            exit_time_minutes = random.randint(10, 20)
        elif "RB" in current_bay:
            accessibility_score = 5  # Best for quick deployment
            exit_time_minutes = random.randint(5, 15)
        else:  # Standard stabling
            accessibility_score = 2  # Requires shunting
            exit_time_minutes = random.randint(20, 35)
        
        # Shunting requirements for tomorrow's operation
        shunting_moves = 0
        shunting_time = 0
        
        # If train needs to exit but is blocked
        if bay_type == "Standard_Stabling" and random.random() < 0.3:
            shunting_moves = random.randint(1, 4)
            shunting_time = shunting_moves * random.randint(8, 15)
        
        # Optimal bay recommendation based on tomorrow's plan
        tomorrow_status = random.choice(["Service", "Maintenance", "Standby", "Cleaning"])
        
        if tomorrow_status == "Service":
            optimal_bay_type = "Standby_Ready"
        elif tomorrow_status == "Maintenance":
            optimal_bay_type = "IBL_Maintenance"
        elif tomorrow_status == "Cleaning":
            optimal_bay_type = "Cleaning_Bays"
        else:
            optimal_bay_type = "Standard_Stabling"
        
        # Check if reallocation is needed
        needs_reallocation = bay_type != optimal_bay_type.replace("_", "_")
        
        stabling_data.append({
            "Train_ID": train_id,
            "Current_Bay": current_bay,
            "Current_Bay_Type": bay_type,
            "Accessibility_Score": accessibility_score,
            "Exit_Time_Minutes": exit_time_minutes,
            "Shunting_Moves_Required": shunting_moves,
            "Shunting_Time_Minutes": shunting_time,
            "Tomorrow_Status": tomorrow_status,
            "Optimal_Bay_Type": optimal_bay_type,
            "Needs_Reallocation": needs_reallocation,
            "Reallocation_Priority": "High" if shunting_moves > 2 else "Medium" if needs_reallocation else "Low",
            "Energy_Cost_Estimate": shunting_time * 15,  # INR per minute
            "Notes": f"Currently in {current_bay}, optimized for {tomorrow_status}"
        })
    
    return pd.DataFrame(stabling_data)

def generate_iot_telemetry_data():
    """
    Additional: Real-time IoT sensor data for fitness monitoring
    """
    telemetry_data = []
    
    for train_id in FLEET_IDS:
        # Generate recent telemetry readings
        for hours_ago in range(24):  # Last 24 hours
            timestamp = datetime.now() - timedelta(hours=hours_ago)
            
            # Simulate various sensor readings
            base_temp = 25 + random.uniform(-5, 15)  # Ambient variation
            base_current = 180 + random.uniform(-30, 50)  # Motor current
            
            telemetry_data.append({
                "Train_ID": train_id,
                "Timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Motor_Temperature_C": round(base_temp + random.uniform(15, 45), 1),
                "Motor_Current_A": round(base_current + random.uniform(-20, 30), 1),
                "Brake_Pressure_Bar": round(random.uniform(4.5, 6.2), 2),
                "HVAC_Power_kW": round(random.uniform(8, 25), 1),
                "Door_Cycles": random.randint(180, 320),
                "Vibration_Level": round(random.uniform(0.8, 2.5), 2),
                "Oil_Temperature_C": round(base_temp + random.uniform(20, 60), 1),
                "Battery_Voltage_V": round(random.uniform(72, 78), 1),
                "Compressor_Status": random.choice(["Normal", "High_Load", "Maintenance_Alert"]),
                "GPS_Speed_kmh": random.randint(0, 80),
                "Health_Score": round(random.uniform(0.75, 0.98), 3)
            })
    
    return pd.DataFrame(telemetry_data)

def generate_comprehensive_kmrl_data():
    """
    Main function to generate all KMRL operational data
    """
    print("🚆 Generating Comprehensive KMRL Fleet Management Data...")
    print(f"📊 Simulating {NUM_TRAINS} trainsets for {SIMULATION_DAYS} days")
    print(f"📅 Current Decision Date: {CURRENT_DATE}")
    print("="*60)
    
    try:
        # Generate all 6 key variables
        print("1️⃣  Generating Fitness Certificates...")
        fitness_certs = generate_fitness_certificates()
        fitness_certs.to_csv("fitness_certificates.csv", index=False)
        print(f"   ✅ {len(fitness_certs)} certificates generated")
        
        print("2️⃣  Generating Maximo Job Cards...")
        job_cards = generate_maximo_job_cards()
        job_cards.to_csv("maximo_job_cards.csv", index=False)
        print(f"   ✅ {len(job_cards)} job cards generated")
        
        print("3️⃣  Generating Branding Contract Data...")
        branding_data = generate_enhanced_branding_data()
        branding_data.to_csv("branding_priorities.csv", index=False)
        print(f"   ✅ {len(branding_data)} branding records generated")
        
        print("4️⃣  Generating Mileage Balancing Data...")
        mileage_data = generate_mileage_balancing_data()
        mileage_data.to_csv("mileage_balancing.csv", index=False)
        print(f"   ✅ {len(mileage_data)} mileage records generated")
        
        print("5️⃣  Generating Cleaning & Detailing Schedule...")
        cleaning_data = generate_cleaning_detailing_schedule()
        cleaning_data.to_csv("cleaning_detailing_schedule.csv", index=False)
        print(f"   ✅ {len(cleaning_data)} cleaning schedules generated")
        
        print("6️⃣  Generating Stabling Geometry Data...")
        stabling_data = generate_stabling_geometry_data()
        stabling_data.to_csv("stabling_geometry.csv", index=False)
        print(f"   ✅ {len(stabling_data)} stabling positions generated")
        
        print("🔧  Generating IoT Telemetry Data...")
        telemetry_data = generate_iot_telemetry_data()
        telemetry_data.to_csv("iot_telemetry_data.csv", index=False)
        print(f"   ✅ {len(telemetry_data)} telemetry records generated")
        
        # Generate updated depot layout
        print("🏗️  Generating Enhanced Depot Layout...")
        with open('enhanced_depot_layout.json', 'w') as f:
            json.dump(STABLING_BAYS, f, indent=4)
        print("   ✅ Enhanced depot layout generated")
        
        # Create summary report
        print("📋  Generating Data Summary...")
        summary = {
            "Generation_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Simulation_Period": f"{START_DATE} to {START_DATE + timedelta(days=SIMULATION_DAYS)}",
            "Decision_Date": CURRENT_DATE.strftime("%Y-%m-%d"),
            "Fleet_Size": NUM_TRAINS,
            "Data_Files_Generated": {
                "fitness_certificates.csv": len(fitness_certs),
                "maximo_job_cards.csv": len(job_cards),
                "branding_priorities.csv": len(branding_data),
                "mileage_balancing.csv": len(mileage_data),
                "cleaning_detailing_schedule.csv": len(cleaning_data),
                "stabling_geometry.csv": len(stabling_data),
                "iot_telemetry_data.csv": len(telemetry_data)
            },
            "Key_Statistics": {
                "Expired_Certificates": len(fitness_certs[fitness_certs['Status'] == 'Expired']),
                "Open_Job_Cards": len(job_cards[job_cards['Status'] == 'Open']),
                "Critical_Branding_Contracts": len(branding_data[branding_data['Priority'] == 'Critical']),
                "High_Wear_Trains": len(mileage_data[mileage_data['Priority'] == 'Critical']),
                "Cleaning_Backlog": len(cleaning_data[cleaning_data['Status'] == 'Delayed']),
                "Trains_Needing_Reallocation": len(stabling_data[stabling_data['Needs_Reallocation'] == True])
            }
        }
        
        with open('data_generation_summary.json', 'w') as f:
            json.dump(summary, f, indent=4)
        
        print("="*60)
        print("🎉 KMRL Data Generation Complete!")
        print(f"📈 Total Records Generated: {sum(summary['Data_Files_Generated'].values())}")
        print("🚨 Key Issues Identified:")
        for issue, count in summary['Key_Statistics'].items():
            if count > 0:
                print(f"   • {issue.replace('_', ' ')}: {count}")
        
        print("\n📁 Files Generated:")
        for filename in summary['Data_Files_Generated'].keys():
            print(f"   • {filename}")
        print("   • enhanced_depot_layout.json")
        print("   • data_generation_summary.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating data: {str(e)}")
        return False

if __name__ == "__main__":
    success = generate_comprehensive_kmrl_data()
    if success:
        print("\n✨ Ready for KMRL Induction Planning Optimization!")
    else:
        print("\n💥 Data generation failed. Please check the errors above.")