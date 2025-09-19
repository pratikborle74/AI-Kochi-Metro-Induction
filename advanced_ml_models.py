import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, mean_squared_error, accuracy_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Data processing
import json

class KMRLAdvancedMLModels:
    """
    Advanced Machine Learning models for KMRL fleet optimization
    """
    
    def __init__(self):
        self.rf_failure_model = None
        self.rf_optimization_model = None
        self.lstm_demand_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_all_data(self):
        """Load all generated KMRL data for ML training"""
        try:
            # Load all datasets
            fitness_certs = pd.read_csv("fitness_certificates.csv")
            job_cards = pd.read_csv("maximo_job_cards.csv")
            branding = pd.read_csv("branding_priorities.csv")
            mileage = pd.read_csv("mileage_balancing.csv")
            cleaning = pd.read_csv("cleaning_detailing_schedule.csv")
            stabling = pd.read_csv("stabling_geometry.csv")
            telemetry = pd.read_csv("iot_telemetry_data.csv")
            
            print("✅ All datasets loaded successfully")
            return fitness_certs, job_cards, branding, mileage, cleaning, stabling, telemetry
            
        except FileNotFoundError as e:
            print(f"❌ Error loading data: {e}")
            print("Please run enhanced_data_generator.py first")
            return None
    
    def prepare_failure_prediction_data(self, fitness_certs, job_cards, mileage, telemetry):
        """
        Prepare data for Random Forest failure prediction model
        """
        print("🔧 Preparing failure prediction dataset...")
        
        # Aggregate telemetry by train (ignore dates for now since they don't match)
        telemetry_agg = telemetry.groupby(['Train_ID']).agg({
            'Motor_Temperature_C': ['mean', 'max', 'std'],
            'Motor_Current_A': ['mean', 'max', 'std'],
            'Brake_Pressure_Bar': ['mean', 'min'],
            'HVAC_Power_kW': ['mean', 'max'],
            'Vibration_Level': ['mean', 'max', 'std'],
            'Oil_Temperature_C': ['mean', 'max'],
            'Health_Score': ['mean', 'min']
        }).reset_index()
        
        # Flatten column names
        telemetry_agg.columns = ['Train_ID'] + [
            f"{col[0]}_{col[1]}" if col[1] != '' else col[0] 
            for col in telemetry_agg.columns[1:]
        ]
        
        # Merge with mileage data by Train_ID only
        failure_data = mileage.merge(telemetry_agg, on='Train_ID', how='inner')
        
        # Add certificate expiry information
        cert_summary = fitness_certs.groupby('Train_ID').agg({
            'Status': lambda x: (x == 'Expired').sum(),  # Count of expired certs
            'Department': 'count'  # Total certificates
        }).reset_index()
        cert_summary.columns = ['Train_ID', 'Expired_Certs', 'Total_Certs']
        cert_summary['Cert_Compliance_Rate'] = (cert_summary['Total_Certs'] - cert_summary['Expired_Certs']) / cert_summary['Total_Certs']
        
        failure_data = failure_data.merge(cert_summary, on='Train_ID', how='left')
        
        # Add job card information
        job_summary = job_cards.groupby('Train_ID').agg({
            'Priority': lambda x: (x == 'Critical').sum(),  # Critical jobs
            'Status': lambda x: (x == 'Open').sum(),  # Open jobs
            'Work_Order_ID': 'count'  # Total jobs
        }).reset_index()
        job_summary.columns = ['Train_ID', 'Critical_Jobs', 'Open_Jobs', 'Total_Jobs']
        
        failure_data = failure_data.merge(job_summary, on='Train_ID', how='left')
        
        # Create failure target variable (composite risk score)
        failure_data['Failure_Risk_Score'] = (
            (failure_data['Average_Usage_Pct'] / 100) * 0.3 +  # Component wear
            (failure_data['Expired_Certs'] / failure_data['Total_Certs'].fillna(1)) * 0.2 +  # Cert compliance
            (failure_data['Critical_Jobs'] / failure_data['Total_Jobs'].fillna(1)) * 0.2 +  # Job urgency
            (1 - failure_data['Health_Score_mean'].fillna(0.8)) * 0.3  # IoT health
        )
        
        # Create binary failure prediction target with more realistic thresholds
        # Lower the threshold to create more positive cases for training
        failure_data['Will_Fail_Soon'] = (failure_data['Failure_Risk_Score'] > 0.4).astype(int)
        
        # Ensure we have both classes by forcing some high-risk trains to be failure cases
        high_risk_trains = failure_data.nlargest(8, 'Failure_Risk_Score').index
        failure_data.loc[high_risk_trains, 'Will_Fail_Soon'] = 1
        
        # Fill missing values
        failure_data = failure_data.fillna(0)
        
        print(f"✅ Prepared {len(failure_data)} records for failure prediction")
        return failure_data
    
    def train_failure_prediction_model(self, failure_data):
        """
        Train Random Forest model for failure prediction
        """
        print("🌲 Training Random Forest failure prediction model...")
        
        # Select features for prediction
        feature_cols = [
            'Bogie_Usage_Pct', 'BrakePad_Usage_Pct', 'HVAC_Usage_Pct', 'Motor_Usage_Pct',
            'Motor_Temperature_C_mean', 'Motor_Temperature_C_max',
            'Motor_Current_A_mean', 'Motor_Current_A_max',
            'Brake_Pressure_Bar_mean', 'HVAC_Power_kW_mean',
            'Vibration_Level_mean', 'Vibration_Level_max',
            'Oil_Temperature_C_mean', 'Health_Score_mean',
            'Cert_Compliance_Rate', 'Critical_Jobs', 'Open_Jobs'
        ]
        
        X = failure_data[feature_cols].fillna(0)
        y = failure_data['Will_Fail_Soon']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest
        self.rf_failure_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.rf_failure_model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.rf_failure_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Failure Prediction Model Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': self.rf_failure_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        print("\n🔝 Top 5 Most Important Features:")
        print(feature_importance.head().to_string(index=False))
        
        # Save model
        joblib.dump(self.rf_failure_model, 'rf_failure_prediction_model.pkl')
        print("💾 Model saved as 'rf_failure_prediction_model.pkl'")
        
        return feature_importance
    
    def prepare_optimization_data(self, fitness_certs, job_cards, branding, mileage, stabling):
        """
        Prepare data for Random Forest optimization model
        """
        print("⚙️ Preparing optimization dataset...")
        
        # Create master dataset by train
        trains = mileage[['Train_ID']].copy()
        
        # Add mileage/wear information
        trains = trains.merge(mileage, on='Train_ID', how='left')
        
        # Add certificate status
        cert_status = fitness_certs.groupby('Train_ID').agg({
            'Status': lambda x: (x == 'Valid').sum() / len(x),  # % valid certs
            'Department': 'count'
        }).reset_index()
        cert_status.columns = ['Train_ID', 'Cert_Valid_Rate', 'Total_Certs']
        trains = trains.merge(cert_status, on='Train_ID', how='left')
        
        # Add job card status
        job_status = job_cards.groupby('Train_ID').agg({
            'Status': lambda x: (x == 'Open').sum(),
            'Priority': lambda x: (x == 'Critical').sum(),
            'Estimated_Hours': 'sum'
        }).reset_index()
        job_status.columns = ['Train_ID', 'Open_Jobs', 'Critical_Jobs', 'Maintenance_Hours_Needed']
        trains = trains.merge(job_status, on='Train_ID', how='left')
        
        # Add branding requirements
        branding_latest = branding.sort_values('Date').groupby('Train_ID').last().reset_index()
        branding_info = branding_latest[['Train_ID', 'Required_Hours', 'Compliance_Percentage']].copy()
        branding_info.columns = ['Train_ID', 'Branding_Hours_Required', 'Branding_Compliance']
        trains = trains.merge(branding_info, on='Train_ID', how='left')
        
        # Add stabling information
        stabling_info = stabling[['Train_ID', 'Accessibility_Score', 'Shunting_Time_Minutes']].copy()
        trains = trains.merge(stabling_info, on='Train_ID', how='left')
        
        # Create optimal decision target
        trains['Optimal_Decision'] = 'Standby'  # Default
        
        # Decision rules (simplified for training)
        trains.loc[trains['Critical_Components'].str.len() > 0, 'Optimal_Decision'] = 'Maintenance'
        trains.loc[trains['Branding_Hours_Required'].notna(), 'Optimal_Decision'] = 'Service'
        trains.loc[(trains['Average_Usage_Pct'] < 30) & (trains['Cert_Valid_Rate'] > 0.8), 'Optimal_Decision'] = 'Service'
        trains.loc[trains['Open_Jobs'] > 2, 'Optimal_Decision'] = 'Maintenance'
        
        # Fill missing values
        trains = trains.fillna(0)
        
        print(f"✅ Prepared {len(trains)} records for optimization")
        return trains
    
    def train_optimization_model(self, optimization_data):
        """
        Train Random Forest model for optimal decision making
        """
        print("🎯 Training Random Forest optimization model...")
        
        # Prepare features
        feature_cols = [
            'Average_Usage_Pct', 'Cert_Valid_Rate', 'Open_Jobs', 'Critical_Jobs',
            'Maintenance_Hours_Needed', 'Branding_Hours_Required', 'Branding_Compliance',
            'Accessibility_Score', 'Shunting_Time_Minutes'
        ]
        
        X = optimization_data[feature_cols].fillna(0)
        y = optimization_data['Optimal_Decision']
        
        # Encode target variable
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        self.label_encoders['decision'] = le
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Train model
        self.rf_optimization_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight='balanced'
        )
        
        self.rf_optimization_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.rf_optimization_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Optimization Model Accuracy: {accuracy:.3f}")
        
        # Feature importance
        opt_feature_importance = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': self.rf_optimization_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        print("\n🎯 Top 5 Decision-Making Features:")
        print(opt_feature_importance.head().to_string(index=False))
        
        # Save model
        joblib.dump(self.rf_optimization_model, 'rf_optimization_model.pkl')
        joblib.dump(self.label_encoders, 'label_encoders.pkl')
        print("💾 Optimization model saved")
        
        return opt_feature_importance
    
    def prepare_demand_forecasting_data(self, telemetry, branding):
        """
        Prepare time series data for LSTM demand forecasting
        """
        print("📈 Preparing demand forecasting dataset...")
        
        # Convert timestamp to datetime
        telemetry['Timestamp'] = pd.to_datetime(telemetry['Timestamp'])
        telemetry['Hour'] = telemetry['Timestamp'].dt.hour
        telemetry['Day'] = telemetry['Timestamp'].dt.day
        
        # Aggregate by hour to create demand patterns
        hourly_demand = telemetry.groupby(['Hour']).agg({
            'Train_ID': 'count',  # Number of active trains
            'GPS_Speed_kmh': 'mean',  # Average system utilization
            'HVAC_Power_kW': 'mean',  # Energy consumption
            'Door_Cycles': 'sum'  # Passenger activity indicator
        }).reset_index()
        
        hourly_demand.columns = ['Hour', 'Active_Trains', 'Avg_Speed', 'Avg_HVAC_Power', 'Total_Door_Cycles']
        
        # Create demand score (simplified)
        hourly_demand['Demand_Score'] = (
            hourly_demand['Active_Trains'] / hourly_demand['Active_Trains'].max() * 0.4 +
            hourly_demand['Avg_Speed'] / hourly_demand['Avg_Speed'].max() * 0.3 +
            hourly_demand['Total_Door_Cycles'] / hourly_demand['Total_Door_Cycles'].max() * 0.3
        ) * 100
        
        # Add typical metro demand patterns
        peak_hours = [7, 8, 9, 17, 18, 19]  # Morning and evening peaks
        hourly_demand['Demand_Score'] = hourly_demand.apply(
            lambda row: row['Demand_Score'] * 1.5 if row['Hour'] in peak_hours else row['Demand_Score'], 
            axis=1
        )
        
        print(f"✅ Prepared {len(hourly_demand)} hourly demand records")
        return hourly_demand
    
    def train_lstm_demand_model(self, demand_data):
        """
        Train LSTM model for demand forecasting
        """
        print("🧠 Training LSTM demand forecasting model...")
        
        # Prepare time series data
        demand_values = demand_data['Demand_Score'].values
        
        # Create sequences for LSTM
        def create_sequences(data, seq_length):
            X, y = [], []
            for i in range(len(data) - seq_length):
                X.append(data[i:i+seq_length])
                y.append(data[i+seq_length])
            return np.array(X), np.array(y)
        
        seq_length = 6  # Use 6 hours to predict next hour
        X, y = create_sequences(demand_values, seq_length)
        
        # Reshape for LSTM
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Split data
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Build LSTM model
        self.lstm_demand_model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(seq_length, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        self.lstm_demand_model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train model
        history = self.lstm_demand_model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, y_test),
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Evaluate
        train_predictions = self.lstm_demand_model.predict(X_train)
        test_predictions = self.lstm_demand_model.predict(X_test)
        
        train_mse = mean_squared_error(y_train, train_predictions)
        test_mse = mean_squared_error(y_test, test_predictions)
        
        print(f"✅ LSTM Demand Model - Train MSE: {train_mse:.3f}, Test MSE: {test_mse:.3f}")
        
        # Save model
        self.lstm_demand_model.save('lstm_demand_model.h5')
        print("💾 LSTM model saved as 'lstm_demand_model.h5'")
        
        return history
    
    def predict_failures(self, train_data):
        """
        Use trained Random Forest model to predict failures
        """
        if self.rf_failure_model is None:
            print("❌ Failure prediction model not trained yet")
            return None
        
        feature_cols = [
            'Bogie_Usage_Pct', 'BrakePad_Usage_Pct', 'HVAC_Usage_Pct', 'Motor_Usage_Pct',
            'Motor_Temperature_C_mean', 'Motor_Temperature_C_max',
            'Motor_Current_A_mean', 'Motor_Current_A_max',
            'Brake_Pressure_Bar_mean', 'HVAC_Power_kW_mean',
            'Vibration_Level_mean', 'Vibration_Level_max',
            'Oil_Temperature_C_mean', 'Health_Score_mean',
            'Cert_Compliance_Rate', 'Critical_Jobs', 'Open_Jobs'
        ]
        
        X = train_data[feature_cols].fillna(0)
        predictions = self.rf_failure_model.predict_proba(X)[:, 1]  # Probability of failure
        
        return predictions
    
    def optimize_decisions(self, train_data):
        """
        Use trained Random Forest model for optimal decisions
        """
        if self.rf_optimization_model is None:
            print("❌ Optimization model not trained yet")
            return None
        
        feature_cols = [
            'Average_Usage_Pct', 'Cert_Valid_Rate', 'Open_Jobs', 'Critical_Jobs',
            'Maintenance_Hours_Needed', 'Branding_Hours_Required', 'Branding_Compliance',
            'Accessibility_Score', 'Shunting_Time_Minutes'
        ]
        
        X = train_data[feature_cols].fillna(0)
        predictions = self.rf_optimization_model.predict(X)
        
        # Decode predictions
        decision_labels = self.label_encoders['decision'].inverse_transform(predictions)
        
        return decision_labels
    
    def forecast_demand(self, recent_demand_data, hours_ahead=24):
        """
        Use trained LSTM model to forecast demand
        """
        if self.lstm_demand_model is None:
            print("❌ LSTM demand model not trained yet")
            return None
        
        # Use last 6 hours to predict future
        if len(recent_demand_data) < 6:
            print("❌ Need at least 6 hours of recent data")
            return None
        
        last_sequence = recent_demand_data[-6:].reshape(1, 6, 1)
        forecasts = []
        
        for _ in range(hours_ahead):
            next_pred = self.lstm_demand_model.predict(last_sequence, verbose=0)[0][0]
            forecasts.append(next_pred)
            
            # Update sequence for next prediction
            last_sequence = np.roll(last_sequence, -1, axis=1)
            last_sequence[0, -1, 0] = next_pred
        
        return np.array(forecasts)

def train_all_models():
    """
    Main function to train all advanced ML models
    """
    print("🚀 KMRL Advanced ML Models Training Pipeline")
    print("=" * 60)
    
    # Initialize ML system
    ml_system = KMRLAdvancedMLModels()
    
    # Load data
    data = ml_system.load_all_data()
    if data is None:
        return False
    
    fitness_certs, job_cards, branding, mileage, cleaning, stabling, telemetry = data
    
    try:
        # 1. Train Failure Prediction Model (Random Forest)
        print("\n" + "="*60)
        print("1️⃣ FAILURE PREDICTION MODEL")
        print("="*60)
        
        failure_data = ml_system.prepare_failure_prediction_data(
            fitness_certs, job_cards, mileage, telemetry
        )
        failure_importance = ml_system.train_failure_prediction_model(failure_data)
        
        # 2. Train Optimization Model (Random Forest)
        print("\n" + "="*60)
        print("2️⃣ OPTIMIZATION DECISION MODEL")
        print("="*60)
        
        optimization_data = ml_system.prepare_optimization_data(
            fitness_certs, job_cards, branding, mileage, stabling
        )
        opt_importance = ml_system.train_optimization_model(optimization_data)
        
        # 3. Train Demand Forecasting Model (LSTM)
        print("\n" + "="*60)
        print("3️⃣ DEMAND FORECASTING MODEL")
        print("="*60)
        
        demand_data = ml_system.prepare_demand_forecasting_data(telemetry, branding)
        lstm_history = ml_system.train_lstm_demand_model(demand_data)
        
        # Save summary
        model_summary = {
            "training_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "models_trained": {
                "random_forest_failure_prediction": {
                    "model_file": "rf_failure_prediction_model.pkl",
                    "training_records": len(failure_data),
                    "top_features": failure_importance.head(5).to_dict('records')
                },
                "random_forest_optimization": {
                    "model_file": "rf_optimization_model.pkl",
                    "training_records": len(optimization_data),
                    "top_features": opt_importance.head(5).to_dict('records')
                },
                "lstm_demand_forecasting": {
                    "model_file": "lstm_demand_model.h5",
                    "training_records": len(demand_data),
                    "sequence_length": 6
                }
            }
        }
        
        with open('ml_models_summary.json', 'w') as f:
            json.dump(model_summary, f, indent=4)
        
        print("\n" + "="*60)
        print("🎉 ALL MODELS TRAINED SUCCESSFULLY!")
        print("="*60)
        print("📁 Files Generated:")
        print("   • rf_failure_prediction_model.pkl")
        print("   • rf_optimization_model.pkl")
        print("   • lstm_demand_model.h5")
        print("   • label_encoders.pkl")
        print("   • ml_models_summary.json")
        
        print("\n🚀 Your KMRL system now has:")
        print("   🔮 Predictive failure detection")
        print("   🎯 AI-driven optimization decisions")
        print("   📈 Demand forecasting capabilities")
        print("\n✨ Ready for hackathon demo!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during training: {e}")
        return False

if __name__ == "__main__":
    success = train_all_models()
    if not success:
        print("💥 Model training failed. Please check the errors above.")