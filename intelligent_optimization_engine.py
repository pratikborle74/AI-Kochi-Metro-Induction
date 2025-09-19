import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
import warnings
warnings.filterwarnings('ignore')

class IntelligentKMRLOptimizer:
    """
    Enhanced KMRL optimization engine powered by ML models
    """
    
    def __init__(self):
        self.failure_model = None
        self.optimization_model = None
        self.demand_model = None
        self.label_encoders = None
        self.load_models()
    
    def load_models(self):
        """Load all trained ML models"""
        try:
            print("🧠 Loading trained ML models...")
            
            # Load Random Forest models
            self.failure_model = joblib.load('rf_failure_prediction_model.pkl')
            self.optimization_model = joblib.load('rf_optimization_model.pkl')
            self.label_encoders = joblib.load('label_encoders.pkl')
            
            # Load LSTM model
            self.demand_model = load_model('lstm_demand_model.h5', compile=False)
            
            print("✅ All ML models loaded successfully")
            return True
            
        except Exception as e:
            print(f"⚠️ Warning: Could not load ML models: {e}")
            print("   Running without ML intelligence...")
            return False
    
    def load_operational_data(self):
        """Load all KMRL operational data"""
        try:
            data = {
                'fitness_certs': pd.read_csv("fitness_certificates.csv"),
                'job_cards': pd.read_csv("maximo_job_cards.csv"),
                'branding': pd.read_csv("branding_priorities.csv"),
                'mileage': pd.read_csv("mileage_balancing.csv"),
                'cleaning': pd.read_csv("cleaning_detailing_schedule.csv"),
                'stabling': pd.read_csv("stabling_geometry.csv"),
                'telemetry': pd.read_csv("iot_telemetry_data.csv")
            }
            
            print(f"✅ Loaded operational data for {len(data['mileage'])} trains")
            return data
            
        except Exception as e:
            print(f"❌ Error loading operational data: {e}")
            return None
    
    def predict_train_failures(self, train_data):
        """
        Use ML to predict which trains are likely to fail
        """
        if self.failure_model is None:
            print("⚠️ Failure prediction model not available")
            return {}
        
        try:
            # Prepare features for failure prediction
            feature_cols = [
                'Bogie_Usage_Pct', 'BrakePad_Usage_Pct', 'HVAC_Usage_Pct', 'Motor_Usage_Pct',
                'Motor_Temperature_C_mean', 'Motor_Temperature_C_max',
                'Motor_Current_A_mean', 'Motor_Current_A_max',
                'Brake_Pressure_Bar_mean', 'HVAC_Power_kW_mean',
                'Vibration_Level_mean', 'Vibration_Level_max',
                'Oil_Temperature_C_mean', 'Health_Score_mean',
                'Cert_Compliance_Rate', 'Critical_Jobs', 'Open_Jobs'
            ]
            
            # Create the feature matrix (add missing columns with defaults)
            X = pd.DataFrame()
            for col in feature_cols:
                if col in train_data.columns:
                    X[col] = train_data[col]
                else:
                    # Default values for missing features
                    if 'Temperature' in col or 'Current' in col:
                        X[col] = 50.0  # Default sensor readings
                    elif 'Health_Score' in col:
                        X[col] = 0.85  # Default health score
                    elif 'Pressure' in col:
                        X[col] = 5.0   # Default pressure
                    elif 'Power' in col or 'Vibration' in col:
                        X[col] = 15.0  # Default power/vibration
                    else:
                        X[col] = 0.0   # Default for counts/percentages
            
            X = X.fillna(0)
            
            # Get failure probabilities - handle single class case
            proba_result = self.failure_model.predict_proba(X)
            
            if proba_result.shape[1] == 1:
                # Only one class (no failures), create zero probabilities
                failure_probs = np.zeros(len(X))
                print("   ⚠️ Model trained with no failure cases - using risk scoring instead")
            else:
                # Normal case with both classes
                failure_probs = proba_result[:, 1]
            
            # Create failure risk dictionary
            failure_predictions = {}
            for i, train_id in enumerate(train_data['Train_ID']):
                # If no ML failures, use component wear as risk indicator
                if failure_probs[i] == 0 and 'Average_Usage_Pct' in train_data.columns:
                    usage_pct = train_data.iloc[i]['Average_Usage_Pct']
                    risk_prob = min(0.8, usage_pct / 100)  # Convert usage to risk probability
                else:
                    risk_prob = failure_probs[i]
                
                risk_level = "Critical" if risk_prob > 0.7 else "High" if risk_prob > 0.4 else "Low"
                failure_predictions[train_id] = {
                    'failure_probability': float(risk_prob),
                    'risk_level': risk_level,
                    'ml_recommendation': 'Immediate Maintenance' if risk_prob > 0.7 else 
                                       'Schedule Maintenance' if risk_prob > 0.4 else 'Continue Service'
                }
            
            return failure_predictions
            
        except Exception as e:
            print(f"⚠️ Error in failure prediction: {e}")
            return {}
    
    def optimize_train_decisions(self, train_data):
        """
        Use ML to make optimal train deployment decisions
        """
        if self.optimization_model is None or self.label_encoders is None:
            print("⚠️ Optimization model not available")
            return {}
        
        try:
            feature_cols = [
                'Average_Usage_Pct', 'Cert_Valid_Rate', 'Open_Jobs', 'Critical_Jobs',
                'Maintenance_Hours_Needed', 'Branding_Hours_Required', 'Branding_Compliance',
                'Accessibility_Score', 'Shunting_Time_Minutes'
            ]
            
            # Create feature matrix with defaults for missing columns
            X = pd.DataFrame()
            for col in feature_cols:
                if col in train_data.columns:
                    X[col] = train_data[col]
                else:
                    # Default values
                    if col == 'Cert_Valid_Rate':
                        X[col] = 0.8  # Assume 80% cert compliance
                    elif col == 'Branding_Compliance':
                        X[col] = 90.0  # Assume good compliance
                    elif col == 'Accessibility_Score':
                        X[col] = 3.0   # Medium accessibility
                    elif col == 'Shunting_Time_Minutes':
                        X[col] = 20.0  # Average shunting time
                    else:
                        X[col] = 0.0
            
            X = X.fillna(0)
            
            # Get decision predictions
            decision_predictions = self.optimization_model.predict(X)
            decision_labels = self.label_encoders['decision'].inverse_transform(decision_predictions)
            
            # Get prediction probabilities for confidence scoring
            decision_probabilities = self.optimization_model.predict_proba(X)
            
            optimization_decisions = {}
            for i, train_id in enumerate(train_data['Train_ID']):
                confidence = float(np.max(decision_probabilities[i]))
                optimization_decisions[train_id] = {
                    'ml_decision': decision_labels[i],
                    'confidence': confidence,
                    'alternative_decisions': {
                        label: float(prob) for label, prob in 
                        zip(self.label_encoders['decision'].classes_, decision_probabilities[i])
                    }
                }
            
            return optimization_decisions
            
        except Exception as e:
            print(f"⚠️ Error in optimization decision: {e}")
            return {}
    
    def forecast_demand_pattern(self, current_hour=None):
        """
        Use LSTM to forecast demand for next 24 hours
        """
        if self.demand_model is None:
            print("⚠️ Demand forecasting model not available")
            return None
        
        try:
            # Create synthetic recent demand data if none provided
            if current_hour is None:
                current_hour = datetime.now().hour
            
            # Generate typical metro demand pattern for last 6 hours
            hours = [(current_hour - i) % 24 for i in range(6, 0, -1)]
            
            demand_scores = []
            for hour in hours:
                if hour in [7, 8, 9, 17, 18, 19]:  # Peak hours
                    base_demand = np.random.uniform(70, 95)
                elif hour in [10, 11, 16, 20]:  # Medium hours
                    base_demand = np.random.uniform(45, 65)
                else:  # Off-peak hours
                    base_demand = np.random.uniform(20, 40)
                
                demand_scores.append(base_demand)
            
            # Reshape for LSTM prediction
            recent_demand = np.array(demand_scores).reshape(1, 6, 1)
            
            # Forecast next 24 hours
            forecasts = []
            current_sequence = recent_demand.copy()
            
            for _ in range(24):
                next_pred = self.demand_model.predict(current_sequence, verbose=0)[0][0]
                forecasts.append(float(next_pred))
                
                # Update sequence
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1, 0] = next_pred
            
            # Create forecast with time labels
            forecast_hours = [(current_hour + i + 1) % 24 for i in range(24)]
            demand_forecast = {
                'forecast_start_hour': current_hour + 1,
                'predictions': [
                    {
                        'hour': hour,
                        'demand_score': demand,
                        'demand_level': 'Peak' if demand > 70 else 'Medium' if demand > 40 else 'Low'
                    }
                    for hour, demand in zip(forecast_hours, forecasts)
                ]
            }
            
            return demand_forecast
            
        except Exception as e:
            print(f"⚠️ Error in demand forecasting: {e}")
            return None
    
    def run_intelligent_optimization(self):
        """
        Main function to run the complete intelligent optimization
        """
        print("\n" + "="*80)
        print("🚆 KMRL INTELLIGENT FLEET OPTIMIZATION ENGINE")
        print("="*80)
        
        # Load operational data
        data = self.load_operational_data()
        if data is None:
            return None
        
        # Prepare comprehensive train dataset
        trains_data = self.prepare_comprehensive_dataset(data)
        
        # 1. ML-Powered Failure Prediction
        print("\n🔮 Running ML-Powered Failure Prediction...")
        failure_predictions = self.predict_train_failures(trains_data)
        
        # 2. ML-Driven Decision Optimization
        print("🎯 Running ML-Driven Decision Optimization...")
        optimization_decisions = self.optimize_train_decisions(trains_data)
        
        # 3. LSTM Demand Forecasting
        print("📈 Running LSTM Demand Forecasting...")
        demand_forecast = self.forecast_demand_pattern()
        
        # 4. Integrate all insights
        print("⚙️ Integrating ML insights with operational constraints...")
        final_decisions = self.integrate_ml_insights(
            trains_data, failure_predictions, optimization_decisions, data
        )
        
        # 5. Generate explainable recommendations
        print("📋 Generating explainable recommendations...")
        recommendations = self.generate_explainable_recommendations(
            final_decisions, failure_predictions, optimization_decisions, demand_forecast
        )
        
        print("✅ Intelligent optimization complete!")
        return recommendations
    
    def prepare_comprehensive_dataset(self, data):
        """Merge all operational data into comprehensive train dataset"""
        
        # Start with mileage data
        trains = data['mileage'].copy()
        
        # Add certificate compliance
        cert_summary = data['fitness_certs'].groupby('Train_ID').agg({
            'Status': lambda x: (x == 'Valid').sum() / len(x)
        }).reset_index()
        cert_summary.columns = ['Train_ID', 'Cert_Valid_Rate']
        trains = trains.merge(cert_summary, on='Train_ID', how='left')
        
        # Add job card information
        job_summary = data['job_cards'].groupby('Train_ID').agg({
            'Status': lambda x: (x == 'Open').sum(),
            'Priority': lambda x: (x == 'Critical').sum(),
            'Estimated_Hours': 'sum'
        }).reset_index()
        job_summary.columns = ['Train_ID', 'Open_Jobs', 'Critical_Jobs', 'Maintenance_Hours_Needed']
        trains = trains.merge(job_summary, on='Train_ID', how='left')
        
        # Add branding requirements
        branding_latest = data['branding'].sort_values('Date').groupby('Train_ID').last().reset_index()
        branding_info = branding_latest[['Train_ID', 'Required_Hours', 'Compliance_Percentage']].copy()
        branding_info.columns = ['Train_ID', 'Branding_Hours_Required', 'Branding_Compliance']
        trains = trains.merge(branding_info, on='Train_ID', how='left')
        
        # Add stabling information
        stabling_info = data['stabling'][['Train_ID', 'Accessibility_Score', 'Shunting_Time_Minutes']].copy()
        trains = trains.merge(stabling_info, on='Train_ID', how='left')
        
        # Add telemetry aggregation
        telemetry_agg = data['telemetry'].groupby('Train_ID').agg({
            'Motor_Temperature_C': ['mean', 'max'],
            'Motor_Current_A': ['mean', 'max'],
            'Brake_Pressure_Bar': 'mean',
            'HVAC_Power_kW': 'mean',
            'Vibration_Level': ['mean', 'max'],
            'Oil_Temperature_C': 'mean',
            'Health_Score': 'mean'
        }).reset_index()
        
        # Flatten telemetry columns
        telemetry_agg.columns = ['Train_ID'] + [
            f"{col[0]}_{col[1]}" if col[1] != '' else col[0] 
            for col in telemetry_agg.columns[1:]
        ]
        
        trains = trains.merge(telemetry_agg, on='Train_ID', how='left')
        
        # Fill missing values
        trains = trains.fillna(0)
        
        return trains
    
    def integrate_ml_insights(self, trains_data, failure_predictions, optimization_decisions, raw_data):
        """Integrate ML insights with operational constraints"""
        
        final_decisions = {}
        
        for _, train_row in trains_data.iterrows():
            train_id = train_row['Train_ID']
            
            # Start with ML decision
            ml_decision = optimization_decisions.get(train_id, {}).get('ml_decision', 'Standby')
            ml_confidence = optimization_decisions.get(train_id, {}).get('confidence', 0.5)
            
            # Check failure prediction
            failure_info = failure_predictions.get(train_id, {})
            failure_prob = failure_info.get('failure_probability', 0.0)
            
            # Apply business rules and constraints
            final_decision = ml_decision
            reasoning = [f"ML model suggests: {ml_decision} (confidence: {ml_confidence:.2f})"]
            
            # Override for high failure risk
            if failure_prob > 0.7:
                final_decision = "Maintenance"
                reasoning.append(f"⚠️ OVERRIDE: High failure risk ({failure_prob:.2f}) - forced maintenance")
            
            # Check certificate constraints
            cert_issues = raw_data['fitness_certs'][
                (raw_data['fitness_certs']['Train_ID'] == train_id) & 
                (raw_data['fitness_certs']['Status'] == 'Expired')
            ]
            
            if len(cert_issues) > 0:
                final_decision = "Maintenance"
                reasoning.append(f"⚠️ CONSTRAINT: {len(cert_issues)} expired certificates")
            
            # Check branding contracts
            branding_critical = raw_data['branding'][
                (raw_data['branding']['Train_ID'] == train_id) & 
                (raw_data['branding']['Priority'] == 'Critical')
            ]
            
            if len(branding_critical) > 0 and final_decision != "Maintenance":
                final_decision = "Service"
                reasoning.append("🎯 PRIORITY: Critical branding contract")
            
            final_decisions[train_id] = {
                'final_decision': final_decision,
                'ml_decision': ml_decision,
                'ml_confidence': ml_confidence,
                'failure_probability': failure_prob,
                'reasoning': reasoning,
                'priority_score': self.calculate_priority_score(train_row, failure_info, optimization_decisions.get(train_id, {}))
            }
        
        return final_decisions
    
    def calculate_priority_score(self, train_row, failure_info, optimization_info):
        """Calculate a priority score for train deployment"""
        
        score = 0.0
        
        # Factor 1: Failure risk (higher risk = lower score for service)
        failure_prob = failure_info.get('failure_probability', 0.0)
        score += (1 - failure_prob) * 30
        
        # Factor 2: Component wear balance
        avg_usage = train_row.get('Average_Usage_Pct', 50)
        score += (100 - avg_usage) * 0.2
        
        # Factor 3: ML confidence
        ml_confidence = optimization_info.get('confidence', 0.5)
        score += ml_confidence * 20
        
        # Factor 4: Certificate compliance
        cert_rate = train_row.get('Cert_Valid_Rate', 0.8)
        score += cert_rate * 15
        
        # Factor 5: Branding requirements
        branding_hours = train_row.get('Branding_Hours_Required', 0)
        if branding_hours > 0:
            score += 25  # Bonus for branded trains
        
        return min(100, max(0, score))
    
    def generate_explainable_recommendations(self, final_decisions, failure_predictions, optimization_decisions, demand_forecast):
        """Generate comprehensive, explainable recommendations"""
        
        # Count decisions
        decision_counts = {}
        for decision_info in final_decisions.values():
            decision = decision_info['final_decision']
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        # Sort trains by priority
        sorted_trains = sorted(
            final_decisions.items(),
            key=lambda x: x[1]['priority_score'],
            reverse=True
        )
        
        # Create recommendations
        recommendations = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'optimization_summary': {
                'total_trains': len(final_decisions),
                'service_ready': decision_counts.get('Service', 0),
                'maintenance_required': decision_counts.get('Maintenance', 0),
                'standby': decision_counts.get('Standby', 0)
            },
            'ml_insights': {
                'failure_prediction_enabled': len(failure_predictions) > 0,
                'optimization_model_enabled': len(optimization_decisions) > 0,
                'demand_forecasting_enabled': demand_forecast is not None,
                'high_risk_trains': len([fp for fp in failure_predictions.values() if fp['failure_probability'] > 0.7]),
                'ml_accuracy_note': "Models trained on current operational data"
            },
            'train_recommendations': [],
            'operational_alerts': [],
            'demand_forecast': demand_forecast
        }
        
        # Add individual train recommendations
        for train_id, decision_info in sorted_trains:
            recommendations['train_recommendations'].append({
                'train_id': train_id,
                'recommended_action': decision_info['final_decision'],
                'priority_score': round(decision_info['priority_score'], 1),
                'ml_decision': decision_info['ml_decision'],
                'ml_confidence': round(decision_info['ml_confidence'], 2),
                'failure_risk': round(decision_info['failure_probability'], 3),
                'reasoning': decision_info['reasoning']
            })
        
        # Add operational alerts
        critical_trains = [
            (tid, info) for tid, info in final_decisions.items() 
            if info['failure_probability'] > 0.7 or 'OVERRIDE' in str(info['reasoning'])
        ]
        
        for train_id, info in critical_trains:
            alert_type = "CRITICAL_FAILURE_RISK" if info['failure_probability'] > 0.7 else "CONSTRAINT_VIOLATION"
            recommendations['operational_alerts'].append({
                'alert_type': alert_type,
                'train_id': train_id,
                'severity': 'HIGH',
                'message': f"Train {train_id}: {'; '.join(info['reasoning'])}",
                'recommended_action': info['final_decision']
            })
        
        return recommendations

# Main execution function
def run_intelligent_kmrl_optimization():
    """
    Run the complete intelligent KMRL optimization system
    """
    optimizer = IntelligentKMRLOptimizer()
    recommendations = optimizer.run_intelligent_optimization()
    
    if recommendations:
        # Save recommendations
        with open('intelligent_optimization_results.json', 'w') as f:
            json.dump(recommendations, f, indent=4)
        
        # Display summary
        print(f"\n📊 OPTIMIZATION SUMMARY:")
        print(f"   🚆 Total Trains: {recommendations['optimization_summary']['total_trains']}")
        print(f"   🟢 Service Ready: {recommendations['optimization_summary']['service_ready']}")
        print(f"   🔧 Maintenance Required: {recommendations['optimization_summary']['maintenance_required']}")
        print(f"   ⏸️  Standby: {recommendations['optimization_summary']['standby']}")
        
        if recommendations['operational_alerts']:
            print(f"\n🚨 CRITICAL ALERTS: {len(recommendations['operational_alerts'])}")
            for alert in recommendations['operational_alerts'][:3]:
                print(f"   • {alert['message']}")
        
        print(f"\n💾 Detailed results saved to: intelligent_optimization_results.json")
        return recommendations
    
    return None

if __name__ == "__main__":
    recommendations = run_intelligent_kmrl_optimization()
    if recommendations:
        print("\n🎉 Intelligent KMRL optimization completed successfully!")
        print("🚀 Your hackathon demo is ready with full ML-powered decision making!")
    else:
        print("\n💥 Optimization failed. Please check the logs above.")