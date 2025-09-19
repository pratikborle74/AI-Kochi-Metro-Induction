import streamlit as st
import pandas as pd
import requests
import os
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="KMRL Health & Mileage Dashboard",
    page_icon="🚆",
    layout="wide"
)

st.title("🚆 KMRL Health & Mileage Dashboard")
st.markdown("This module analyzes component usage across the fleet to balance mileage and identify overused assets.")

# --- Configuration ---
MILEAGE_SERVICE_URL = "http://127.0.0.1:8000/analyze-fleet/"
DATA_FILE_PATH = "fleet_usage_log.csv"

# --- Main Application Logic ---
st.sidebar.header("Evaluation Control")

if st.sidebar.button("▶️ Run Fleet Analysis"):
    # Check if the required data file exists
    if not os.path.exists(DATA_FILE_PATH):
        st.error(f"Error: Data file not found at '{DATA_FILE_PATH}'.")
        st.info("Please run the `data_generator.py` script first to create the necessary files.")
    else:
        # Prepare the file to be sent to the API
        files = {'file': (os.path.basename(DATA_FILE_PATH), open(DATA_FILE_PATH, 'rb'), 'text/csv')}
        
        try:
            with st.spinner('Contacting Health API and analyzing fleet data...'):
                response = requests.post(MILEAGE_SERVICE_URL, files=files)
            
            if response.status_code == 200:
                st.success("✅ Analysis Complete!")
                analysis_data = response.json()["AnalysisResults"]
                
                # --- Display Results ---
                st.subheader("Fleet Component Health Summary")
                
                # Convert the nested JSON from the API into a flat DataFrame for display
                display_list = []
                for train in analysis_data:
                    flat_data = {"Train_ID": train["Train_ID"], "Overall Status": train["OverallStatus"]}
                    for part, details in train["Parts"].items():
                        flat_data[f"{part} Usage (%)"] = details["UsagePercent"]
                        flat_data[f"{part} Status"] = details["Status"]
                    display_list.append(flat_data)
                
                results_df = pd.DataFrame(display_list)

                # Style the dataframe to highlight trains that need attention
                def highlight_status(row):
                    color = 'background-color: #ffcccc' if 'Required' in row['Overall Status'] else ''
                    return [color] * len(row)

                st.dataframe(results_df.style.apply(highlight_status, axis=1), use_container_width=True)

                # --- Add a Visual Chart ---
                st.subheader("Fleet Usage Distribution")
                fig = px.bar(results_df, x="Train_ID", y="Bogie_Mileage Usage (%)", color="Overall Status",
                             title="Bogie Mileage Usage Across Fleet",
                             color_discrete_map={"Action Required": "#E74C3C", "Nominal": "#2ECC71"})
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.error(f"Error from API: {response.status_code} - {response.text}")

        except requests.exceptions.ConnectionError:
            st.error(f"Connection Error: Could not connect to the Mileage Service API at {MILEAGE_SERVICE_URL}.")
            st.info("Please make sure the `mileage_service.py` is running in a separate terminal.")
else:
    st.info("Click 'Run Fleet Analysis' to fetch and display the latest health assessment.")

