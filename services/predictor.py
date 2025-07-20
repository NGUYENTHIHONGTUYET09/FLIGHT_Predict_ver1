import joblib
from services.utils import preprocess_data
import pandas as pd
import os

def predict_delay(model_name, user_df):
    model = joblib.load(os.path.join("models", f"{model_name}.pkl"))
    feature_columns = joblib.load(os.path.join("models", "feature_columns.pkl"))
    X_user, _ = preprocess_data(user_df)
    X_user = X_user.select_dtypes(include=['number']).fillna(0)
    for col in feature_columns:
        if col not in X_user.columns:
            X_user[col] = 0
    X_user = X_user[feature_columns]

    # Nếu là Linear Regression thì scale dữ liệu
    if model_name == "LinearRegression_model":
        scaler = joblib.load(os.path.join("models", "scaler.pkl"))
        X_user = scaler.transform(X_user)

    prediction = model.predict(X_user)[0]
    return round(float(prediction), 2)