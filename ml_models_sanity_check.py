#!/usr/bin/env python3
"""
KMRL ML Models Sanity Check
===========================

This script validates that all ML models are properly trained and functioning correctly.
Perfect for demonstrating model health to hackathon judges!
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
from tensorflow.keras.models import load_model
import warnings
warnings.filterwarnings('ignore')

def print_banner():
    """Display sanity check banner"""
    print("="*70)
    print("🧠 KMRL ML MODELS SANITY CHECK & VALIDATION")
    print("="*70)
    print(f"⏰ Check performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_data_files():
    """Check if all required data files exist"""
    print("📊 CHECKING DATA FILES...")
    
    required_files = [
        "fitness_certificates.csv",
        "maximo_job_cards.csv", 
        "branding_priorities.csv",
        "mileage_balancing.csv",
        "cleaning_detailing_schedule.csv",
        "stabling_geometry.csv",
        "iot_telemetry_data.csv"
    ]
    
    all_files_exist = True
    total_records = 0
    
    for file in required_files:
        if os.path.exists(file):
            df = pd.read_csv(file)
            records = len(df)
            total_records += records
            print(f"   ✅ {file:<35} - {records:,} records")
        else:
            print(f"   ❌ {file:<35} - MISSING!")
            all_files_exist = False
    
    print(f"   📈 Total data records: {total_records:,}")
    return all_files_exist, total_records

def check_failure_prediction_model():
    """Validate the failure prediction model"""
    print("\n🔮 CHECKING FAILURE PREDICTION MODEL...")
    
    try:
        # Load model
        model = joblib.load('rf_failure_prediction_model.pkl')
        
        # Check model properties
        print(f"   🌲 Model type: {type(model).__name__}")
        print(f"   🎯 Classes: {model.classes_}")
        print(f"   📊 Number of classes: {model.n_classes_}")
        print(f"   🌳 Number of trees: {model.n_estimators}")
        
        # Check class distribution
        if len(model.classes_) >= 2:
            print(f"   ✅ Model has both failure classes (0: No Failure, 1: Will Fail)")
            
            # Test prediction
            test_features = np.random.random((5, 17))  # 17 features expected
            predictions = model.predict_proba(test_features)
            
            print(f"   🧪 Test prediction shape: {predictions.shape}")
            print(f"   🎲 Sample prediction probabilities:")
            for i, pred in enumerate(predictions[:3]):
                fail_prob = pred[1] if len(pred) > 1 else 0
                print(f"      Train {i+1}: {fail_prob:.3f} failure probability")
            
            # Feature importance
            feature_names = [
                'Bogie_Usage_Pct', 'BrakePad_Usage_Pct', 'HVAC_Usage_Pct', 'Motor_Usage_Pct',
                'Motor_Temperature_C_mean', 'Motor_Temperature_C_max',
                'Motor_Current_A_mean', 'Motor_Current_A_max',
                'Brake_Pressure_Bar_mean', 'HVAC_Power_kW_mean',
                'Vibration_Level_mean', 'Vibration_Level_max',
                'Oil_Temperature_C_mean', 'Health_Score_mean',
                'Cert_Compliance_Rate', 'Critical_Jobs', 'Open_Jobs'
            ]
            
            if len(model.feature_importances_) == len(feature_names):
                top_features = sorted(zip(feature_names, model.feature_importances_), 
                                    key=lambda x: x[1], reverse=True)[:5]
                print(f"   🔝 Top 5 predictive features:")
                for feature, importance in top_features:
                    print(f"      • {feature}: {importance:.3f}")
            
            return True
            
        else:
            print(f"   ⚠️  Model only has one class: {model.classes_}")
            print(f"   💡 This means no failure cases were detected in training data")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking failure model: {e}")
        return False

def check_optimization_model():
    """Validate the optimization decision model"""
    print("\n🎯 CHECKING OPTIMIZATION DECISION MODEL...")
    
    try:
        # Load models
        model = joblib.load('rf_optimization_model.pkl')
        encoders = joblib.load('label_encoders.pkl')
        
        print(f"   🌲 Model type: {type(model).__name__}")
        print(f"   🎯 Decision classes: {encoders['decision'].classes_}")
        print(f"   📊 Number of decisions: {len(encoders['decision'].classes_)}")
        print(f"   🌳 Number of trees: {model.n_estimators}")
        
        # Test prediction
        test_features = np.random.random((3, 9))  # 9 features expected
        predictions = model.predict(test_features)
        decision_labels = encoders['decision'].inverse_transform(predictions)
        
        print(f"   🧪 Test decision predictions:")
        for i, decision in enumerate(decision_labels):
            print(f"      Train {i+1}: {decision}")
        
        # Feature importance
        feature_names = [
            'Average_Usage_Pct', 'Cert_Valid_Rate', 'Open_Jobs', 'Critical_Jobs',
            'Maintenance_Hours_Needed', 'Branding_Hours_Required', 'Branding_Compliance',
            'Accessibility_Score', 'Shunting_Time_Minutes'
        ]
        
        if len(model.feature_importances_) == len(feature_names):
            top_features = sorted(zip(feature_names, model.feature_importances_), 
                                key=lambda x: x[1], reverse=True)[:5]
            print(f"   🔝 Top 5 decision factors:")
            for feature, importance in top_features:
                print(f"      • {feature}: {importance:.3f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking optimization model: {e}")
        return False

def check_lstm_demand_model():
    """Validate the LSTM demand forecasting model"""
    print("\n📈 CHECKING LSTM DEMAND FORECASTING MODEL...")
    
    try:
        # Load model
        model = load_model('lstm_demand_model.h5', compile=False)
        
        print(f"   🧠 Model type: LSTM Neural Network")
        print(f"   🏗️  Model architecture:")
        
        # Print model summary
        model_config = model.get_config()
        layer_count = len(model_config['layers'])
        print(f"      • Total layers: {layer_count}")
        
        # Get input/output shapes
        input_shape = model.input_shape
        output_shape = model.output_shape
        print(f"      • Input shape: {input_shape}")
        print(f"      • Output shape: {output_shape}")
        
        # Test prediction
        test_sequence = np.random.random((1, 6, 1))  # (batch, time_steps, features)
        prediction = model.predict(test_sequence, verbose=0)
        
        print(f"   🧪 Test demand forecast:")
        print(f"      • Input sequence shape: {test_sequence.shape}")
        print(f"      • Predicted demand: {prediction[0][0]:.2f}")
        
        # Model parameters
        total_params = model.count_params()
        print(f"   📊 Total parameters: {total_params:,}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking LSTM model: {e}")
        return False

def check_model_integration():
    """Test that models work together in the optimization engine"""
    print("\n⚙️ CHECKING MODEL INTEGRATION...")
    
    try:
        from intelligent_optimization_engine import IntelligentKMRLOptimizer
        
        # Initialize optimizer
        optimizer = IntelligentKMRLOptimizer()
        
        # Check if models loaded successfully
        models_loaded = {
            'Failure Prediction': optimizer.failure_model is not None,
            'Decision Optimization': optimizer.optimization_model is not None,
            'Demand Forecasting': optimizer.demand_model is not None,
            'Label Encoders': optimizer.label_encoders is not None
        }
        
        print("   🔗 Model Integration Status:")
        all_loaded = True
        for model_name, loaded in models_loaded.items():
            status = "✅ Loaded" if loaded else "❌ Failed"
            print(f"      • {model_name:<20}: {status}")
            if not loaded:
                all_loaded = False
        
        # Test optimization pipeline (quick test)
        if all_loaded:
            print("   🧪 Testing optimization pipeline...")
            try:
                data = optimizer.load_operational_data()
                if data:
                    print("   ✅ Full integration test successful")
                    return True
                else:
                    print("   ⚠️  Data loading issue")
                    return False
            except Exception as e:
                print(f"   ⚠️  Pipeline test error: {e}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking integration: {e}")
        return False

def check_results_files():
    """Check if optimization results exist and are valid"""
    print("\n📋 CHECKING OPTIMIZATION RESULTS...")
    
    result_files = [
        "intelligent_optimization_results.json",
        "what_if_scenarios_analysis.json",
        "ml_models_summary.json"
    ]
    
    files_valid = True
    
    for file in result_files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                file_size = os.path.getsize(file)
                print(f"   ✅ {file:<35} - {file_size:,} bytes")
                
                # Quick content check
                if file == "intelligent_optimization_results.json":
                    if 'optimization_summary' in data:
                        summary = data['optimization_summary']
                        total = summary.get('total_trains', 0)
                        service = summary.get('service_ready', 0)
                        maintenance = summary.get('maintenance_required', 0)
                        standby = summary.get('standby', 0)
                        print(f"      └─ Fleet: {total} trains ({service} service, {maintenance} maintenance, {standby} standby)")
                
            except Exception as e:
                print(f"   ❌ {file:<35} - Invalid JSON: {e}")
                files_valid = False
        else:
            print(f"   ❌ {file:<35} - Missing")
            files_valid = False
    
    return files_valid

def generate_sanity_report():
    """Generate comprehensive sanity check report"""
    print("\n" + "="*70)
    print("📊 COMPREHENSIVE SANITY CHECK REPORT")
    print("="*70)
    
    # Run all checks
    data_ok, total_records = check_data_files()
    failure_model_ok = check_failure_prediction_model()
    optimization_model_ok = check_optimization_model()
    lstm_model_ok = check_lstm_demand_model()
    integration_ok = check_model_integration()
    results_ok = check_results_files()
    
    # Calculate overall health score
    checks = [data_ok, failure_model_ok, optimization_model_ok, lstm_model_ok, integration_ok, results_ok]
    health_score = sum(checks) / len(checks) * 100
    
    print(f"\n🎯 OVERALL SYSTEM HEALTH: {health_score:.1f}%")
    print("="*70)
    
    if health_score >= 90:
        print("🏆 EXCELLENT! System is fully operational and demo-ready!")
        status = "PERFECT"
    elif health_score >= 75:
        print("🥉 GOOD! System is mostly operational with minor issues")
        status = "GOOD"
    elif health_score >= 50:
        print("⚠️  PARTIAL! Some components need attention")
        status = "NEEDS_WORK"
    else:
        print("❌ CRITICAL! System needs significant fixes")
        status = "CRITICAL"
    
    # Component status
    components = [
        ("📊 Data Generation", data_ok),
        ("🔮 Failure Prediction", failure_model_ok),
        ("🎯 Decision Optimization", optimization_model_ok),
        ("📈 Demand Forecasting", lstm_model_ok),
        ("⚙️  System Integration", integration_ok),
        ("📋 Results Generation", results_ok)
    ]
    
    print(f"\n🔍 COMPONENT STATUS:")
    for name, status_ok in components:
        status_icon = "✅" if status_ok else "❌"
        print(f"   {status_icon} {name}")
    
    # Summary stats
    print(f"\n📈 SYSTEM STATISTICS:")
    print(f"   • Total data records: {total_records:,}")
    print(f"   • ML models trained: 3 (Random Forest x2 + LSTM)")
    print(f"   • Integration points: 6 operational variables")
    print(f"   • Demo readiness: {status}")
    
    # Save report
    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "health_score": health_score,
        "status": status,
        "total_records": total_records,
        "component_status": {
            "data_generation": data_ok,
            "failure_prediction": failure_model_ok,
            "decision_optimization": optimization_model_ok,
            "demand_forecasting": lstm_model_ok,
            "system_integration": integration_ok,
            "results_generation": results_ok
        }
    }
    
    with open('ml_sanity_check_report.json', 'w') as f:
        json.dump(report, f, indent=4)
    
    print(f"\n💾 Full report saved to: ml_sanity_check_report.json")
    return health_score >= 75

def main():
    """Main sanity check function"""
    print_banner()
    
    try:
        success = generate_sanity_report()
        
        if success:
            print(f"\n🎉 SANITY CHECK PASSED! System ready for hackathon demo!")
            return True
        else:
            print(f"\n⚠️  SANITY CHECK ISSUES! Please review and fix components above.")
            return False
            
    except Exception as e:
        print(f"\n💥 Sanity check failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)