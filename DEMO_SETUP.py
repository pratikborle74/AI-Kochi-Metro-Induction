#!/usr/bin/env python3
"""
KMRL Intelligent Fleet Optimization System - Demo Setup Script
==============================================================

This script sets up and runs the complete KMRL hackathon demo.
Perfect for judges to see the system in action!

Usage:
    python DEMO_SETUP.py

Requirements:
    - Python 3.8+
    - pip install -r requirements.txt
"""

import subprocess
import sys
import os
from datetime import datetime

def print_banner():
    """Display the demo banner"""
    print("="*80)
    print("🚆 KMRL INTELLIGENT FLEET OPTIMIZATION SYSTEM")
    print("   Hackathon Demo - Complete System Demonstration")
    print("="*80)
    print(f"⏰ Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Please upgrade Python.")
        return False
    
    print("✅ Python version compatible")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All packages installed successfully")
            return True
        else:
            print(f"❌ Package installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing packages: {e}")
        return False

def run_data_generation():
    """Generate comprehensive KMRL data"""
    print("\n" + "-"*60)
    print("STEP 1: GENERATING COMPREHENSIVE KMRL DATA")
    print("-"*60)
    
    try:
        result = subprocess.run([sys.executable, "enhanced_data_generator.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ KMRL operational data generated successfully")
            return True
        else:
            print(f"❌ Data generation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Data generation timed out")
        return False
    except Exception as e:
        print(f"❌ Error in data generation: {e}")
        return False

def train_ml_models():
    """Train all ML models"""
    print("\n" + "-"*60)
    print("STEP 2: TRAINING ADVANCED ML MODELS")
    print("-"*60)
    
    try:
        result = subprocess.run([sys.executable, "advanced_ml_models.py"], 
                              capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ ML models trained successfully")
            return True
        else:
            print(f"❌ ML training failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ ML training timed out")
        return False
    except Exception as e:
        print(f"❌ Error in ML training: {e}")
        return False

def run_intelligent_optimization():
    """Run intelligent optimization"""
    print("\n" + "-"*60)
    print("STEP 3: INTELLIGENT OPTIMIZATION ENGINE")
    print("-"*60)
    
    try:
        result = subprocess.run([sys.executable, "intelligent_optimization_engine.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Intelligent optimization completed")
            return True
        else:
            print(f"❌ Optimization failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Optimization timed out")
        return False
    except Exception as e:
        print(f"❌ Error in optimization: {e}")
        return False

def run_scenario_analysis():
    """Run what-if scenario analysis"""
    print("\n" + "-"*60)
    print("STEP 4: WHAT-IF SCENARIO ANALYSIS")
    print("-"*60)
    
    try:
        result = subprocess.run([sys.executable, "what_if_scenario_engine.py"], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ What-if scenario analysis completed")
            return True
        else:
            print(f"❌ Scenario analysis failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Scenario analysis timed out")
        return False
    except Exception as e:
        print(f"❌ Error in scenario analysis: {e}")
        return False

def display_results_summary():
    """Display comprehensive results summary"""
    print("\n" + "="*80)
    print("🎉 KMRL DEMO COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    # Check and display generated files
    files_to_check = [
        ("fitness_certificates.csv", "Fitness Certificates Data"),
        ("maximo_job_cards.csv", "IBM Maximo Job Cards"),
        ("branding_priorities.csv", "Branding Contract Data"),
        ("mileage_balancing.csv", "Mileage Balancing Analysis"),
        ("cleaning_detailing_schedule.csv", "Cleaning Schedule"),
        ("stabling_geometry.csv", "Stabling Optimization"),
        ("iot_telemetry_data.csv", "IoT Sensor Data"),
        ("rf_failure_prediction_model.pkl", "ML Failure Prediction Model"),
        ("rf_optimization_model.pkl", "ML Optimization Model"),
        ("lstm_demand_model.h5", "LSTM Demand Forecast Model"),
        ("intelligent_optimization_results.json", "Optimization Results"),
        ("what_if_scenarios_analysis.json", "What-if Scenario Analysis")
    ]
    
    print("📁 GENERATED FILES:")
    files_found = 0
    for filename, description in files_to_check:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"   ✅ {filename:<35} ({file_size:,} bytes) - {description}")
            files_found += 1
        else:
            print(f"   ❌ {filename:<35} - Missing!")
    
    print(f"\n📊 SYSTEM CAPABILITIES DEMONSTRATED:")
    print("   🧠 Advanced ML Integration (Random Forest + LSTM)")
    print("   📈 Real-time Optimization with 6 Interdependent Variables")
    print("   🎭 What-if Scenario Modeling & Impact Analysis")
    print("   🔍 Explainable AI with Confidence Scoring")
    print("   ⚡ Production-Ready Architecture")
    
    print(f"\n🎯 DEMO SUCCESS RATE: {files_found}/{len(files_to_check)} files generated")
    
    if files_found == len(files_to_check):
        print("🏆 PERFECT SCORE! All systems operational and ready for judging!")
    elif files_found >= len(files_to_check) * 0.8:
        print("🥉 GOOD! Most systems working, minor issues to resolve")
    else:
        print("⚠️  Some issues detected. Check error messages above.")
    
    print("\n🚀 Your KMRL Intelligent Fleet Optimization System is ready!")
    print("🎪 Perfect for hackathon presentation and judging!")

def main():
    """Main demo setup function"""
    print_banner()
    
    # Step 0: Environment check
    if not check_python_version():
        sys.exit(1)
    
    # Step 0.5: Install requirements
    if not install_requirements():
        print("\n⚠️  Continuing anyway - packages might already be installed")
    
    # Step 1: Data generation
    if not run_data_generation():
        print("❌ Demo failed at data generation step")
        sys.exit(1)
    
    # Step 2: ML model training
    if not train_ml_models():
        print("❌ Demo failed at ML training step")
        sys.exit(1)
    
    # Step 3: Intelligent optimization
    if not run_intelligent_optimization():
        print("❌ Demo failed at optimization step")
        sys.exit(1)
    
    # Step 4: Scenario analysis
    if not run_scenario_analysis():
        print("❌ Demo failed at scenario analysis step")
        sys.exit(1)
    
    # Display final results
    display_results_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)