#!/usr/bin/env python3
"""
🚆 KMRL Interactive Fleet Optimization Dashboard
=====================================================
Comprehensive Streamlit dashboard integrating all KMRL system components:
- Fleet optimization results
- ML model predictions  
- Fitness certificate tracking
- Depot pathfinding visualization
- Real-time system monitoring
- What-if scenario analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
from datetime import datetime, timedelta
import os
import subprocess
import sys

# Configure Streamlit page
st.set_page_config(
    page_title="KMRL Fleet Optimization Dashboard",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-critical {
        color: #dc3545;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">🚆 KMRL Intelligent Fleet Optimization Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for system controls
st.sidebar.title("🎛️ System Controls")
st.sidebar.markdown("---")

# System status check
@st.cache_data(ttl=60)
def check_system_status():
    """Check if all required data files exist"""
    required_files = [
        'fitness_certificates.csv',
        'maximo_job_cards.csv',
        'stabling_geometry.csv',
        'mileage_balancing.csv',
        'intelligent_optimization_results.json'
    ]
    
    status = {}
    for file in required_files:
        status[file] = os.path.exists(file)
    
    return status, all(status.values())

def run_system_component(component):
    """Run a system component and return success status"""
    try:
        if component == "data_generation":
            result = subprocess.run([sys.executable, "enhanced_data_generator.py"], 
                                  capture_output=True, text=True, timeout=120)
        elif component == "ml_training":
            result = subprocess.run([sys.executable, "advanced_ml_models.py"], 
                                  capture_output=True, text=True, timeout=300)
        elif component == "optimization":
            result = subprocess.run([sys.executable, "intelligent_optimization_engine_simple.py"], 
                                  capture_output=True, text=True, timeout=120)
        elif component == "health_check":
            result = subprocess.run([sys.executable, "ml_models_sanity_check.py"], 
                                  capture_output=True, text=True, timeout=120)
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Process timed out"
    except Exception as e:
        return False, "", str(e)

# System status display
system_files, system_healthy = check_system_status()

st.sidebar.subheader("📊 System Status")
if system_healthy:
    st.sidebar.success("✅ All systems operational")
else:
    st.sidebar.error("❌ Missing data files")
    for file, exists in system_files.items():
        if not exists:
            st.sidebar.warning(f"❌ {file}")

st.sidebar.markdown("---")

# System control buttons
st.sidebar.subheader("🚀 System Operations")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔄 Regenerate Data", key="regen_data"):
        with st.spinner("Generating data..."):
            success, stdout, stderr = run_system_component("data_generation")
            if success:
                st.success("✅ Data regenerated!")
                st.rerun()
            else:
                st.error(f"❌ Error: {stderr}")

with col2:
    if st.button("🧠 Retrain Models", key="retrain_ml"):
        with st.spinner("Training ML models..."):
            success, stdout, stderr = run_system_component("ml_training")
            if success:
                st.success("✅ Models retrained!")
                st.rerun()
            else:
                st.error(f"❌ Error: {stderr}")

if st.sidebar.button("🎯 Run Optimization", key="run_opt"):
    with st.spinner("Running optimization..."):
        success, stdout, stderr = run_system_component("optimization")
        if success:
            st.success("✅ Optimization complete!")
            st.rerun()
        else:
            st.error(f"❌ Error: {stderr}")

if st.sidebar.button("🏥 Health Check", key="health_check"):
    with st.spinner("Running health check..."):
        success, stdout, stderr = run_system_component("health_check")
        if success:
            st.success("✅ System healthy!")
        else:
            st.error(f"❌ Health check failed: {stderr}")

st.sidebar.markdown("---")

# Load data functions
@st.cache_data(ttl=300)
def load_optimization_results():
    """Load optimization results"""
    try:
        with open('intelligent_optimization_results.json', 'r') as f:
            return json.load(f)
    except:
        return None

@st.cache_data(ttl=300)
def load_csv_data(filename):
    """Load CSV data with error handling"""
    try:
        return pd.read_csv(filename)
    except:
        return None

# Main dashboard tabs
if system_healthy:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Fleet Overview", 
        "🏥 Fitness Certificates", 
        "🛠️ Maintenance & Jobs", 
        "🗺️ Depot Pathfinding", 
        "🧠 ML Insights", 
        "🎭 Scenario Analysis"
    ])
    
    # TAB 1: Fleet Overview
    with tab1:
        st.header("📊 Fleet Optimization Overview")
        
        # Load optimization results
        opt_results = load_optimization_results()
        
        if opt_results:
            # Fleet summary metrics
            summary = opt_results['optimization_summary']
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="🚆 Total Trains",
                    value=summary['total_trains']
                )
            
            with col2:
                service_pct = (summary['service_ready'] / summary['total_trains']) * 100
                st.metric(
                    label="🟢 Service Ready",
                    value=f"{summary['service_ready']} ({service_pct:.1f}%)"
                )
            
            with col3:
                maint_pct = (summary['maintenance_required'] / summary['total_trains']) * 100
                st.metric(
                    label="🔧 Maintenance Required",
                    value=f"{summary['maintenance_required']} ({maint_pct:.1f}%)"
                )
            
            with col4:
                standby_pct = (summary['standby'] / summary['total_trains']) * 100
                st.metric(
                    label="⏸️ Standby",
                    value=f"{summary['standby']} ({standby_pct:.1f}%)"
                )
            
            # Fleet allocation pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Fleet Allocation")
                fig = px.pie(
                    values=[summary['service_ready'], summary['maintenance_required'], summary['standby']],
                    names=['Service Ready', 'Maintenance Required', 'Standby'],
                    color_discrete_sequence=['#28a745', '#dc3545', '#ffc107']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("ML Insights")
                ml_insights = opt_results['ml_insights']
                
                st.markdown(f"""
                **🔮 Failure Prediction**: {'✅ Enabled' if ml_insights['failure_prediction_enabled'] else '❌ Disabled'}  
                **🎯 Decision Optimization**: {'✅ Enabled' if ml_insights['optimization_model_enabled'] else '❌ Disabled'}  
                **📈 Demand Forecasting**: {'✅ Enabled' if ml_insights['demand_forecasting_enabled'] else '❌ Disabled'}  
                **🚨 High Risk Trains**: {ml_insights['high_risk_trains']}
                """)
            
            # Train recommendations table
            st.subheader("🚂 Train Recommendations")
            
            # Convert recommendations to DataFrame
            recommendations = pd.DataFrame(opt_results['train_recommendations'])
            
            
            # Display styled dataframe (simplified for Streamlit compatibility)
            display_df = recommendations[['train_id', 'recommended_action', 'priority_score', 
                                        'ml_confidence', 'failure_risk']].copy()
            
            # Add color coding using emojis
            display_df['status_icon'] = display_df['recommended_action'].apply(
                lambda x: '🟢 Service' if x == 'Service' else 
                         ('🔧 Maintenance' if x == 'Maintenance' else '⏸️ Standby')
            )
            
            # Reorder columns
            display_df = display_df[['train_id', 'status_icon', 'priority_score', 'ml_confidence', 'failure_risk']]
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Critical alerts
            if opt_results.get('train_recommendations'):
                critical_alerts = [
                    train for train in opt_results['train_recommendations'] 
                    if any('OVERRIDE' in str(reason) for reason in train.get('reasoning', []))
                ]
                
                if critical_alerts:
                    st.subheader("🚨 Critical Alerts")
                    for alert in critical_alerts:
                        st.warning(f"**{alert['train_id']}**: ML suggested {alert['ml_decision']} → Forced {alert['recommended_action']} (Risk: {alert['failure_risk']:.2f})")
        
        else:
            st.warning("⚠️ No optimization results available. Please run the optimization engine.")
    
    # TAB 2: Fitness Certificates
    with tab2:
        st.header("🏥 Fitness Certificate Management")
        
        fitness_df = load_csv_data('fitness_certificates.csv')
        
        if fitness_df is not None:
            # Certificate status overview
            col1, col2, col3, col4 = st.columns(4)
            
            status_counts = fitness_df['Status'].value_counts()
            
            with col1:
                st.metric("📋 Total Certificates", len(fitness_df))
            with col2:
                valid_count = status_counts.get('Valid', 0)
                st.metric("✅ Valid", f"{valid_count} ({valid_count/len(fitness_df)*100:.1f}%)")
            with col3:
                expired_count = status_counts.get('Expired', 0)
                st.metric("❌ Expired", f"{expired_count} ({expired_count/len(fitness_df)*100:.1f}%)")
            with col4:
                pending_count = status_counts.get('Pending', 0) + status_counts.get('Renewal_In_Progress', 0)
                st.metric("🔄 Pending/Renewal", f"{pending_count} ({pending_count/len(fitness_df)*100:.1f}%)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Certificate status by department
                st.subheader("Certificate Status by Department")
                status_dept = pd.crosstab(fitness_df['Department'], fitness_df['Status'])
                
                # Get available status columns and match them with colors
                available_statuses = status_dept.columns.tolist()
                status_colors = []
                for status in available_statuses:
                    if status == 'Valid':
                        status_colors.append('#28a745')
                    elif status == 'Expired':
                        status_colors.append('#dc3545')
                    elif status in ['Renewal_In_Progress', 'Pending']:
                        status_colors.append('#ffc107')
                    else:
                        status_colors.append('#6c757d')
                
                fig = px.bar(
                    status_dept.reset_index(),
                    x='Department',
                    y=available_statuses,
                    title="Certificate Status Distribution",
                    color_discrete_sequence=status_colors
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Validity periods by department
                st.subheader("Validity Periods by Department")
                validity_df = fitness_df[['Department', 'Validity_Days']].drop_duplicates()
                fig = px.bar(
                    validity_df,
                    x='Department',
                    y='Validity_Days',
                    title="Standard Validity Periods (Days)",
                    color='Validity_Days',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Certificate details table
            st.subheader("📋 Certificate Details")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                dept_filter = st.selectbox("Department", ['All'] + list(fitness_df['Department'].unique()))
            with col2:
                status_filter = st.selectbox("Status", ['All'] + list(fitness_df['Status'].unique()))
            with col3:
                priority_filter = st.selectbox("Priority", ['All'] + list(fitness_df['Priority'].unique()))
            
            # Apply filters
            filtered_df = fitness_df.copy()
            if dept_filter != 'All':
                filtered_df = filtered_df[filtered_df['Department'] == dept_filter]
            if status_filter != 'All':
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            if priority_filter != 'All':
                filtered_df = filtered_df[filtered_df['Priority'] == priority_filter]
            
            # Display filtered data
            st.dataframe(filtered_df, use_container_width=True, height=400)
            
            # Certificate expiry timeline
            st.subheader("📅 Certificate Expiry Timeline")
            
            # Parse dates and create timeline
            fitness_df_timeline = fitness_df[fitness_df['Expiry_Date'].notna()].copy()
            fitness_df_timeline['Expiry_Date'] = pd.to_datetime(fitness_df_timeline['Expiry_Date'])
            fitness_df_timeline['Days_To_Expiry'] = (fitness_df_timeline['Expiry_Date'] - pd.Timestamp.now()).dt.days
            
            # Group by expiry status
            current_date = pd.Timestamp.now()
            fitness_df_timeline['Expiry_Category'] = pd.cut(
                fitness_df_timeline['Days_To_Expiry'],
                bins=[-float('inf'), -1, 30, 90, float('inf')],
                labels=['Expired', 'Expiring Soon (30d)', 'Due (90d)', 'Valid']
            )
            
            fig = px.scatter(
                fitness_df_timeline,
                x='Days_To_Expiry',
                y='Department',
                color='Expiry_Category',
                size='Validity_Days',
                hover_data=['Train_ID', 'Certificate_ID'],
                title="Certificate Expiry Timeline",
                color_discrete_map={
                    'Expired': '#dc3545',
                    'Expiring Soon (30d)': '#fd7e14',
                    'Due (90d)': '#ffc107',
                    'Valid': '#28a745'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ Fitness certificate data not available.")
    
    # TAB 3: Maintenance & Jobs
    with tab3:
        st.header("🛠️ Maintenance & Job Management")
        
        jobs_df = load_csv_data('maximo_job_cards.csv')
        mileage_df = load_csv_data('mileage_balancing.csv')
        
        if jobs_df is not None:
            # Job card metrics
            col1, col2, col3, col4 = st.columns(4)
            
            status_counts = jobs_df['Status'].value_counts()
            priority_counts = jobs_df['Priority'].value_counts()
            
            with col1:
                st.metric("📋 Total Job Cards", len(jobs_df))
            with col2:
                open_jobs = status_counts.get('Open', 0)
                st.metric("🔓 Open Jobs", open_jobs)
            with col3:
                critical_jobs = priority_counts.get('Critical', 0)
                st.metric("🚨 Critical Jobs", critical_jobs)
            with col4:
                avg_hours = jobs_df['Estimated_Hours'].mean()
                st.metric("⏱️ Avg. Est. Hours", f"{avg_hours:.1f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Job status distribution
                st.subheader("Job Status Distribution")
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Work Order Status"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Priority distribution
                st.subheader("Priority Distribution")
                fig = px.bar(
                    x=priority_counts.index,
                    y=priority_counts.values,
                    title="Work Order Priorities",
                    color=priority_counts.index,
                    color_discrete_map={
                        'Critical': '#dc3545',
                        'High': '#fd7e14',
                        'Medium': '#ffc107',
                        'Low': '#28a745'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent job cards
            st.subheader("📋 Recent Job Cards")
            
            # Parse dates for sorting
            jobs_df['Created_Date'] = pd.to_datetime(jobs_df['Created_Date'])
            recent_jobs = jobs_df.sort_values('Created_Date', ascending=False).head(10)
            
            st.dataframe(recent_jobs[['Work_Order_ID', 'Train_ID', 'Work_Type', 'Priority', 
                                    'Status', 'Estimated_Hours', 'Created_Date']], 
                        use_container_width=True)
        
        if mileage_df is not None:
            st.subheader("⚖️ Component Mileage Analysis")
            
            # Component usage visualization
            component_cols = ['Bogie_Usage_Pct', 'BrakePad_Usage_Pct', 'HVAC_Usage_Pct', 
                            'Motor_Usage_Pct']
            
            # Melt the dataframe for visualization
            usage_df = pd.melt(
                mileage_df,
                id_vars=['Train_ID'],
                value_vars=component_cols,
                var_name='Component',
                value_name='Usage_Percentage'
            )
            
            fig = px.box(
                usage_df,
                x='Component',
                y='Usage_Percentage',
                title="Component Usage Distribution Across Fleet",
                color='Component'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # High wear trains
            st.subheader("🔥 High Wear Trains")
            high_wear = mileage_df[mileage_df['Average_Usage_Pct'] > 70].sort_values('Average_Usage_Pct', ascending=False)
            
            if not high_wear.empty:
                st.dataframe(high_wear[['Train_ID', 'Average_Usage_Pct', 'Priority', 
                                      'Critical_Components', 'Recommendation']], 
                           use_container_width=True)
            else:
                st.success("✅ No trains with high component wear detected.")
    
    # TAB 4: Depot Pathfinding
    with tab4:
        st.header("🗺️ Depot Pathfinding & Stabling Optimization")
        
        stabling_df = load_csv_data('stabling_geometry.csv')
        
        if stabling_df is not None:
            # Depot overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                operational_tracks = len(stabling_df[stabling_df['Track_Status'] == 'OPERATIONAL'])
                st.metric("🛤️ Operational Tracks", operational_tracks)
            
            with col2:
                overflow_trains = len(stabling_df[stabling_df['Current_Track_ID'] == 'OVERFLOW'])
                st.metric("🚨 Overflow Trains", overflow_trains)
            
            with col3:
                avg_energy_cost = stabling_df[stabling_df['Energy_Cost_INR'] < 1500]['Energy_Cost_INR'].mean()
                st.metric("⚡ Avg. Energy Cost", f"₹{avg_energy_cost:.0f}")
            
            with col4:
                reallocation_needed = len(stabling_df[stabling_df['Needs_Reallocation'] == True])
                st.metric("🔄 Reallocation Needed", reallocation_needed)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Energy cost distribution
                st.subheader("Energy Cost Distribution")
                operational_df = stabling_df[stabling_df['Track_Status'] == 'OPERATIONAL']
                
                fig = px.histogram(
                    operational_df,
                    x='Energy_Cost_INR',
                    nbins=10,
                    title="Energy Cost Distribution (₹)",
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Track utilization
                st.subheader("Track Utilization")
                track_status = stabling_df['Track_Status'].value_counts()
                
                fig = px.pie(
                    values=track_status.values,
                    names=track_status.index,
                    title="Track Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Depot layout visualization
            st.subheader("🏗️ Depot Layout & Pathfinding")
            
            # Create depot visualization
            operational_trains = stabling_df[stabling_df['Track_Status'] == 'OPERATIONAL']
            
            fig = px.scatter(
                operational_trains,
                x='Distance_To_Mainline_M',
                y='Switches_Required',
                size='Energy_Cost_INR',
                color='Tomorrow_Status',
                hover_data=['Train_ID', 'Current_Track_ID', 'Shunting_Time_Minutes'],
                title="Train Positions vs. Energy Cost",
                labels={
                    'Distance_To_Mainline_M': 'Distance to Mainline (m)',
                    'Switches_Required': 'Switches Required',
                    'Energy_Cost_INR': 'Energy Cost (₹)'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Optimal pathfinding examples
            st.subheader("🎯 Optimal Pathfinding Examples")
            
            # Show trains with defined paths
            path_trains = operational_trains[operational_trains['Path_To_Mainline'] != 'No path']
            
            if not path_trains.empty:
                for _, train in path_trains.head(5).iterrows():
                    with st.expander(f"🚂 {train['Train_ID']} - {train['Current_Track_ID']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Path**: {train['Path_To_Mainline']}")
                            st.write(f"**Distance**: {train['Distance_To_Mainline_M']}m")
                            st.write(f"**Switches**: {train['Switches_Required']}")
                        with col2:
                            st.write(f"**Energy Cost**: ₹{train['Energy_Cost_INR']}")
                            st.write(f"**Shunting Time**: {train['Shunting_Time_Minutes']} min")
                            st.write(f"**Tomorrow's Status**: {train['Tomorrow_Status']}")
            
            # Stabling optimization table
            st.subheader("📋 Current Stabling Assignments")
            
            display_cols = ['Train_ID', 'Current_Track_ID', 'Track_Status', 'Distance_To_Mainline_M', 
                          'Energy_Cost_INR', 'Tomorrow_Status', 'Needs_Reallocation', 'Reallocation_Priority']
            
            st.dataframe(stabling_df[display_cols], use_container_width=True, height=400)
        
        else:
            st.warning("⚠️ Stabling geometry data not available.")
    
    # TAB 5: ML Insights
    with tab5:
        st.header("🧠 Machine Learning Model Insights")
        
        # Load ML summary
        try:
            with open('ml_models_summary.json', 'r') as f:
                ml_summary = json.load(f)
        except:
            ml_summary = None
        
        if ml_summary:
            st.subheader("🏆 Model Performance Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="🔮 Failure Prediction Accuracy",
                    value=f"{ml_summary.get('failure_prediction_accuracy', 0)*100:.1f}%"
                )
            
            with col2:
                st.metric(
                    label="🎯 Decision Optimization Accuracy", 
                    value=f"{ml_summary.get('optimization_accuracy', 0)*100:.1f}%"
                )
            
            with col3:
                st.metric(
                    label="📈 LSTM Demand MSE",
                    value=f"{ml_summary.get('lstm_test_mse', 0):.0f}"
                )
        
        # Feature importance visualization
        if ml_summary and 'feature_importance' in ml_summary:
            st.subheader("🔍 Feature Importance Analysis")
            
            feature_df = pd.DataFrame(ml_summary['feature_importance'])
            
            fig = px.bar(
                feature_df.head(10),
                x='importance',
                y='feature',
                orientation='h',
                title="Top 10 Most Important Features",
                color='importance',
                color_continuous_scale='viridis'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Model prediction examples
        if opt_results:
            st.subheader("🎲 Live Model Predictions")
            
            predictions_df = pd.DataFrame(opt_results['train_recommendations'])
            
            # Failure risk distribution
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(
                    predictions_df,
                    x='failure_risk',
                    nbins=20,
                    title="Failure Risk Distribution",
                    color_discrete_sequence=['#ff7f0e']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.histogram(
                    predictions_df,
                    x='ml_confidence',
                    nbins=20,
                    title="ML Confidence Distribution",
                    color_discrete_sequence=['#2ca02c']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # ML decision accuracy
            st.subheader("🎯 ML Decision Accuracy")
            
            # Compare ML decisions vs final recommendations
            decision_comparison = predictions_df.groupby(['ml_decision', 'recommended_action']).size().reset_index(name='count')
            
            fig = px.bar(
                decision_comparison,
                x='ml_decision',
                y='count',
                color='recommended_action',
                title="ML Decision vs Final Recommendation",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 6: Scenario Analysis
    with tab6:
        st.header("🎭 What-If Scenario Analysis")
        
        # Try to load what-if scenarios
        try:
            with open('what_if_scenarios_analysis.json', 'r') as f:
                scenarios = json.load(f)
        except:
            scenarios = None
        
        if scenarios and 'scenarios' in scenarios:
            st.subheader("🎬 Available Scenarios")
            
            for scenario_name, scenario_data in scenarios['scenarios'].items():
                with st.expander(f"📋 {scenario_name}"):
                    st.write(f"**Description**: {scenario_data.get('description', 'N/A')}")
                    
                    if 'results' in scenario_data:
                        results = scenario_data['results']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Service Ready", results.get('service_ready', 0))
                        with col2:
                            st.metric("Maintenance Required", results.get('maintenance_required', 0))
                        with col3:
                            st.metric("Standby", results.get('standby', 0))
                        
                        if 'impact_analysis' in results:
                            st.write("**Impact Analysis**:")
                            st.write(results['impact_analysis'])
        
        # Interactive scenario builder
        st.subheader("🔧 Custom Scenario Builder")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Modify Parameters:**")
            cert_expiry_rate = st.slider("Certificate Expiry Rate (%)", 0, 50, 15)
            failure_risk_multiplier = st.slider("Failure Risk Multiplier", 0.5, 3.0, 1.0)
            maintenance_capacity = st.slider("Maintenance Capacity", 5, 20, 10)
        
        with col2:
            st.write("**Scenario Impact:**")
            if cert_expiry_rate > 20:
                st.warning("⚠️ High certificate expiry rate will reduce service availability")
            if failure_risk_multiplier > 1.5:
                st.warning("⚠️ Increased failure risk will force more maintenance")
            if maintenance_capacity < 8:
                st.warning("⚠️ Low maintenance capacity may create bottlenecks")
        
        if st.button("🚀 Run Custom Scenario"):
            st.success("✅ Custom scenario configured! (Simulation would run here)")
            
            # Simulate scenario results
            estimated_service = max(0, 8 - int(cert_expiry_rate/5) - int(failure_risk_multiplier))
            estimated_maintenance = min(20, 5 + int(cert_expiry_rate/3) + int(failure_risk_multiplier*3))
            estimated_standby = 25 - estimated_service - estimated_maintenance
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Estimated Service Ready", estimated_service, delta=estimated_service-4)
            with col2:
                st.metric("Estimated Maintenance", estimated_maintenance, delta=estimated_maintenance-13)
            with col3:
                st.metric("Estimated Standby", estimated_standby, delta=estimated_standby-8)

else:
    st.error("❌ System data files missing. Please run the data generation pipeline first.")
    
    if st.button("🔄 Generate System Data"):
        with st.spinner("Generating complete system data..."):
            success, stdout, stderr = run_system_component("data_generation")
            if success:
                st.success("✅ Data generated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Error generating data: {stderr}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🚆 KMRL Intelligent Fleet Optimization Dashboard | Built with Streamlit & AI | Production Ready ✨</p>
    <p>System Status: <span style='color: green;'>●</span> Operational | Last Updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)