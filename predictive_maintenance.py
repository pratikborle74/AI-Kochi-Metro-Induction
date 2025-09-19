import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_model():
    """
    Trains a predictive maintenance model on the historical fleet data and saves it.
    """
    print("Training Predictive Maintenance model...")
    
    try:
        df = pd.read_csv("fleet_health_log.csv")
    except FileNotFoundError:
        print("Error: fleet_health_log.csv not found. Please run data_generator_partial.py first.")
        return

    # --- Feature Engineering ---
    # Create simple features like rolling averages to capture trends over time.
    df['motor_current_avg_3d'] = df.groupby('Train_ID')['motor_current'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df['oil_temp_avg_3d'] = df.groupby('Train_ID')['oil_temperature'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df['dv_pressure_avg_3d'] = df.groupby('Train_ID')['dv_pressure'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df.dropna(inplace=True)

    # --- Model Training ---
    # Define the features (inputs) and the target (what we want to predict)
    features = [
        'motor_current_avg_3d', 
        'oil_temp_avg_3d', 
        'dv_pressure_avg_3d',
        'mileage'
    ]
    target = 'failure_imminent'

    X = df[features]
    y = df[target]

    # Split data into training and testing sets to evaluate the model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Use a RandomForestClassifier, which is good for this type of problem
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)

    # --- Evaluate the model ---
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model trained with Test Accuracy: {accuracy:.2f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # --- Save the trained model for the dashboard to use ---
    joblib.dump(model, 'pdm_model.pkl')
    print("\n✅ Predictive Maintenance model saved as 'pdm_model.pkl'.")

if __name__ == "__main__":
    train_model()

