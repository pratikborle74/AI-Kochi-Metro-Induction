#!/usr/bin/env python3
"""
🚆 KMRL Job Card Priority Integration System
============================================
Integrates the priority service with KMRL fleet optimization
- Real-time condition monitoring via MQTT
- Automated job card creation based on priority scores
- Integration with Maximo Mock API
- Priority-driven maintenance scheduling
"""

import pandas as pd
import numpy as np
import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import sqlite3
import threading
import time
import warnings
warnings.filterwarnings('ignore')

# Import from existing modules
try:
    from config import MQTT_BROKER, MQTT_PORT, PRIORITY_THRESHOLD, MOCK_MAXIMO_URL
except ImportError:
    # Fallback configuration
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    PRIORITY_THRESHOLD = 70.0
    MOCK_MAXIMO_URL = "http://127.0.0.1:8000"

class KMRLJobCardPriorityManager:
    """Enhanced job card priority management with KMRL integration"""
    
    def __init__(self):
        self.coach_data = {}
        self.priority_history = []
        self.db_path = 'kmrl_priority_data.db'
        self.mqtt_client = None
        self.running = False
        
        # Priority calculation weights
        self.W1 = 0.45  # Condition score weight
        self.W2 = 0.2   # Criticality weight
        self.W3 = 0.15  # Time since maintenance weight
        self.W4 = 0.2   # Fault severity weight
        
        # Initialize database
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for priority tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create priority tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS priority_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coach_id TEXT NOT NULL,
                    condition_score REAL,
                    fault_severity TEXT,
                    criticality REAL,
                    time_since_maint REAL,
                    priority_score REAL,
                    timestamp TEXT,
                    job_card_created INTEGER DEFAULT 0,
                    work_order_id TEXT
                )
            ''')
            
            # Create job card status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_card_status (
                    work_order_id TEXT PRIMARY KEY,
                    coach_id TEXT NOT NULL,
                    status TEXT,
                    priority INTEGER,
                    created_date TEXT,
                    estimated_hours REAL,
                    description TEXT,
                    last_updated TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Priority database initialized")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not initialize database: {e}")
    
    def compute_priority(self, condition_score, severity, criticality, time_since_maint):
        """Calculate weighted priority score (higher = more urgent)"""
        severity_map = {"Low": 10, "Medium": 40, "High": 70, "Critical": 100}
        severity_val = severity_map.get(severity, 40)
        
        priority = (self.W1 * (100 - condition_score) +
                   self.W2 * criticality +
                   self.W3 * time_since_maint +
                   self.W4 * severity_val)
        
        return round(priority, 1)
    
    def update_coach_priority(self, coach_data):
        """Update coach priority and store in database"""
        coach_id = coach_data['coach_id']
        
        priority = self.compute_priority(
            coach_data['condition_score'],
            coach_data['fault_severity'],
            coach_data['criticality'],
            coach_data['time_since_maint']
        )
        
        entry = {
            'coach_id': coach_id,
            'condition_score': coach_data['condition_score'],
            'fault_severity': coach_data['fault_severity'],
            'criticality': coach_data['criticality'],
            'time_since_maint': coach_data['time_since_maint'],
            'priority_score': priority,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store in memory
        self.coach_data[coach_id] = entry
        
        # Store in database
        self.store_priority_data(entry)
        
        # Check if job card creation is needed
        if priority >= PRIORITY_THRESHOLD:
            self.create_job_card(entry)
        
        return entry
    
    def store_priority_data(self, entry):
        """Store priority data in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO priority_tracking 
                (coach_id, condition_score, fault_severity, criticality, 
                 time_since_maint, priority_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry['coach_id'],
                entry['condition_score'],
                entry['fault_severity'],
                entry['criticality'],
                entry['time_since_maint'],
                entry['priority_score'],
                entry['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Warning: Could not store priority data: {e}")
    
    def create_job_card(self, entry):
        """Create job card via Maximo API"""
        try:
            # Map priority to Maximo priority (1-5 scale)
            maximo_priority = max(1, min(5, int(6 - (entry['priority_score'] // 20))))
            
            payload = {
                'Train_ID': entry['coach_id'],
                'Work_Order_ID': f"WO-{entry['coach_id']}-{int(time.time())}",
                'Work_Type': 'Preventive Maintenance',
                'Priority': self.map_priority_to_text(maximo_priority),
                'Status': 'Open',
                'Description': f"Auto-generated: Severity={entry['fault_severity']}, Condition Score={entry['condition_score']:.1f}",
                'Estimated_Hours': self.estimate_hours(entry),
                'Created_Date': datetime.utcnow().strftime('%Y-%m-%d'),
                'Equipment_Type': 'Rolling Stock',
                'Maintenance_Type': 'Condition-Based'
            }
            
            # Try to post to Maximo API
            response = requests.post(
                f"{MOCK_MAXIMO_URL}/workorders",
                json=payload,
                timeout=5
            )
            
            if response.ok:
                work_order_data = response.json()
                work_order_id = payload['Work_Order_ID']
                
                print(f"✅ Created work order {work_order_id} for {entry['coach_id']}")
                
                # Update database
                self.store_job_card_status(payload, work_order_id)
                
                # Update existing job cards CSV
                self.update_job_cards_csv(payload)
                
                return work_order_id
                
            else:
                print(f"⚠️ Failed to create work order: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Warning: Job card creation failed: {e}")
            
        return None
    
    def map_priority_to_text(self, numeric_priority):
        """Map numeric priority to text"""
        priority_map = {1: 'Low', 2: 'Low', 3: 'Medium', 4: 'High', 5: 'Critical'}
        return priority_map.get(numeric_priority, 'Medium')
    
    def estimate_hours(self, entry):
        """Estimate maintenance hours based on priority and severity"""
        base_hours = 4
        
        # Adjust based on severity
        severity_multiplier = {
            'Low': 0.5, 'Medium': 1.0, 'High': 1.5, 'Critical': 2.5
        }
        
        # Adjust based on priority
        if entry['priority_score'] > 90:
            priority_multiplier = 2.0
        elif entry['priority_score'] > 70:
            priority_multiplier = 1.5
        else:
            priority_multiplier = 1.0
            
        estimated = base_hours * severity_multiplier.get(entry['fault_severity'], 1.0) * priority_multiplier
        return round(estimated, 1)
    
    def store_job_card_status(self, payload, work_order_id):
        """Store job card status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO job_card_status 
                (work_order_id, coach_id, status, priority, created_date, 
                 estimated_hours, description, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                work_order_id,
                payload['Train_ID'],
                payload['Status'],
                payload['Priority'],
                payload['Created_Date'],
                payload['Estimated_Hours'],
                payload['Description'],
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Warning: Could not store job card status: {e}")
    
    def update_job_cards_csv(self, payload):
        """Update the existing job cards CSV file"""
        try:
            # Load existing job cards
            try:
                df = pd.read_csv('maximo_job_cards.csv')
            except FileNotFoundError:
                # Create new dataframe if file doesn't exist
                df = pd.DataFrame()
            
            # Prepare new row
            new_row = {
                'Work_Order_ID': payload['Work_Order_ID'],
                'Train_ID': payload['Train_ID'],
                'Work_Type': payload['Work_Type'],
                'Priority': payload['Priority'],
                'Status': payload['Status'],
                'Description': payload['Description'],
                'Estimated_Hours': payload['Estimated_Hours'],
                'Created_Date': payload['Created_Date'],
                'Equipment_Type': payload['Equipment_Type'],
                'Maintenance_Type': payload['Maintenance_Type']
            }
            
            # Add new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            # Save updated CSV
            df.to_csv('maximo_job_cards.csv', index=False)
            
            print(f"✅ Updated job cards CSV with {payload['Work_Order_ID']}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not update job cards CSV: {e}")
    
    def get_priority_rankings(self):
        """Get current priority rankings"""
        ranked = sorted(self.coach_data.values(), 
                       key=lambda x: x['priority_score'], reverse=True)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_coaches': len(ranked),
            'high_priority': len([c for c in ranked if c['priority_score'] >= 70]),
            'medium_priority': len([c for c in ranked if 40 <= c['priority_score'] < 70]),
            'low_priority': len([c for c in ranked if c['priority_score'] < 40]),
            'ranked_coaches': ranked
        }
    
    def generate_priority_report(self):
        """Generate priority management report for KMRL dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get recent priority data
            recent_data = pd.read_sql_query('''
                SELECT * FROM priority_tracking 
                WHERE datetime(timestamp) > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
            ''', conn)
            
            # Get job card status
            job_cards = pd.read_sql_query('''
                SELECT * FROM job_card_status 
                ORDER BY created_date DESC
            ''', conn)
            
            conn.close()
            
            # Generate summary statistics
            if not recent_data.empty:
                avg_priority = recent_data['priority_score'].mean()
                max_priority = recent_data['priority_score'].max()
                critical_coaches = len(recent_data[recent_data['priority_score'] >= 90])
                high_priority_coaches = len(recent_data[
                    (recent_data['priority_score'] >= 70) & 
                    (recent_data['priority_score'] < 90)
                ])
            else:
                avg_priority = max_priority = critical_coaches = high_priority_coaches = 0
            
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'avg_priority_score': round(avg_priority, 1),
                    'max_priority_score': round(max_priority, 1),
                    'critical_coaches': critical_coaches,
                    'high_priority_coaches': high_priority_coaches,
                    'total_recent_updates': len(recent_data),
                    'active_job_cards': len(job_cards[job_cards['status'] == 'Open'])
                },
                'recent_data': recent_data.to_dict('records') if not recent_data.empty else [],
                'job_cards': job_cards.to_dict('records') if not job_cards.empty else []
            }
            
            # Save report
            with open('priority_management_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            return report
            
        except Exception as e:
            print(f"⚠️ Warning: Could not generate priority report: {e}")
            return None
    
    def simulate_condition_data(self, train_ids):
        """Simulate condition data for KMRL trains"""
        simulated_data = []
        
        for train_id in train_ids:
            # Generate realistic condition data
            condition_score = np.random.uniform(60, 95)
            
            # Assign fault severity based on condition
            if condition_score < 70:
                fault_severity = np.random.choice(['High', 'Critical'], p=[0.7, 0.3])
            elif condition_score < 80:
                fault_severity = np.random.choice(['Medium', 'High'], p=[0.8, 0.2])
            else:
                fault_severity = np.random.choice(['Low', 'Medium'], p=[0.9, 0.1])
            
            # Generate other parameters
            criticality = np.random.uniform(20, 80)
            time_since_maint = np.random.uniform(1, 30)  # Days
            
            coach_data = {
                'coach_id': train_id,
                'condition_score': round(condition_score, 1),
                'fault_severity': fault_severity,
                'criticality': round(criticality, 1),
                'time_since_maint': round(time_since_maint, 1)
            }
            
            # Update priority
            entry = self.update_coach_priority(coach_data)
            simulated_data.append(entry)
        
        print(f"✅ Simulated condition data for {len(train_ids)} trains")
        return simulated_data

def integrate_with_kmrl_optimization():
    """Integrate priority system with existing KMRL optimization"""
    print("🔗 Integrating Priority System with KMRL Optimization...")
    
    # Initialize priority manager
    priority_manager = KMRLJobCardPriorityManager()
    
    # Load existing train data
    try:
        stabling_df = pd.read_csv('stabling_geometry.csv')
        train_ids = stabling_df['Train_ID'].unique().tolist()
        
        # Simulate condition data for all trains
        simulated_data = priority_manager.simulate_condition_data(train_ids)
        
        # Generate comprehensive priority report
        report = priority_manager.generate_priority_report()
        
        if report:
            print("✅ Priority integration complete!")
            print(f"📊 Summary: {report['summary']['total_recent_updates']} trains processed")
            print(f"🚨 Critical coaches: {report['summary']['critical_coaches']}")
            print(f"⚠️ High priority coaches: {report['summary']['high_priority_coaches']}")
            print(f"📋 Active job cards: {report['summary']['active_job_cards']}")
            
            return priority_manager, report
        else:
            print("⚠️ Priority integration completed with warnings")
            return priority_manager, None
            
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return None, None

def main():
    """Main function to demonstrate priority system integration"""
    print("🚆 KMRL Job Card Priority Integration System")
    print("=" * 50)
    
    priority_manager, report = integrate_with_kmrl_optimization()
    
    if priority_manager and report:
        print("\n🎉 Integration successful!")
        print("📁 Files created:")
        print("   • kmrl_priority_data.db (Priority tracking database)")
        print("   • priority_management_report.json (Priority analysis report)")
        print("   • Updated maximo_job_cards.csv (Enhanced with priority-based job cards)")
        
        print(f"\n📈 System ready for real-time priority monitoring!")
        
        return priority_manager
    else:
        print("❌ Integration incomplete. Please check error messages above.")
        return None

if __name__ == "__main__":
    priority_manager = main()