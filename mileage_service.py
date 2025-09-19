# ment.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
from io import StringIO
from typing import List, Dict

# --- Configuration (Could be moved to a config.py file) ---
# This makes it easier to update service life values without changing the logic.
SERVICE_LIFE_CONFIG = {
    "Bogie_Mileage": 100000,
    "BrakePad_Mileage": 70000,
    "HVAC_Hours": 25000
}

# Thresholds for status categorization
THRESHOLDS = {
    "overused": 70.0,
    "underused": 40.0
}
# -------------------------------------------------------------


# --- Pydantic Models for Data Validation and Schema ---
# Defines the structure for a single part's analysis result
class PartAnalysis(BaseModel):
    UsagePercent: float
    Status: str
    RemainingLife: float

# Defines the structure for a single train's overall analysis
class TrainResult(BaseModel):
    Train_ID: str
    Parts: Dict[str, PartAnalysis]
    OverallStatus: str

# Defines the final response model
class AnalysisResponse(BaseModel):
    AnalysisResults: List[TrainResult]
# -----------------------------------------------------------


# --- Core Logic (Could be moved to an analyzer.py module) ---
def analyze_train_data(df: pd.DataFrame) -> List[TrainResult]:
    """
    Analyzes a DataFrame of train data against service life configurations.
    """
    results = []
    
    # Check for required columns
    required_columns = ["Train_ID"] + list(SERVICE_LIFE_CONFIG.keys())
    if not all(col in df.columns for col in required_columns):
        raise ValueError("CSV is missing one or more required columns.")

    for _, row in df.iterrows():
        parts_data = {}
        is_any_part_overused = False

        for part, max_life in SERVICE_LIFE_CONFIG.items():
            current_usage = row[part]
            usage_percent = (current_usage / max_life) * 100
            
            if usage_percent > THRESHOLDS["overused"]:
                status = "Overused"
                is_any_part_overused = True
            elif usage_percent < THRESHOLDS["underused"]:
                status = "Underused"
            else:
                status = "Balanced"
            
            parts_data[part] = PartAnalysis(
                UsagePercent=round(usage_percent, 2),
                Status=status,
                RemainingLife=max(0, max_life - current_usage) # Ensure it doesn't go below zero
            )

        # Determine an overall status for the train
        overall_status = "Action Required" if is_any_part_overused else "Nominal"

        train_result = TrainResult(
            Train_ID=str(row["Train_ID"]),
            Parts=parts_data,
            OverallStatus=overall_status
        )
        results.append(train_result)
        
    return results
# -------------------------------------------------------------


# --- API Application ---
app = FastAPI(
    title="Train Health Assessment API",
    description="Analyzes train part usage and provides a detailed health status.",
    version="2.0"
)

@app.post("/analyze-fleet/", response_model=AnalysisResponse)
async def analyze_fleet_from_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file with train data to get a detailed health analysis.
    
    **Required CSV Columns:**
    - `Train_ID`
    - `Bogie_Mileage`
    - `BrakePad_Mileage`
    - `HVAC_Hours`
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode("utf-8")))
        analysis = analyze_train_data(df)
        return {"AnalysisResults": analysis}
    except ValueError as e:
        # Catches missing columns error from our logic
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Catches general pandas or decoding errors
        raise HTTPException(status_code=500, detail="Error processing the CSV file.")