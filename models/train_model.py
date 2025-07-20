import os
import sys
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler

# 🧭 Setup base directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "flight_delay_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# 🔧 Ensure sub-package imports work
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..')))
from services.utils import preprocess_data

# 📥 Read and preprocess data
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    print(f"❌ Không tìm thấy file dữ liệu tại: {DATA_PATH}")
    sys.exit(1)

# (Tùy chọn) Loại bỏ outlier nếu muốn
# df = df[(df['arrival_delay'] >= -60) & (df['arrival_delay'] <= 300)]
# Loại bỏ outlier cho Linear Regression (và các model khác cũng sẽ tốt hơn)
df = df[(df['arrival_delay'] >= -60) & (df['arrival_delay'] <= 180)]


X, y = preprocess_data(df)
X = X.select_dtypes(include=["number"]).fillna(0)
y = y.fillna(0)

# 📊 Display some info
print("✅ Các cột đặc trưng:", list(X.columns))
print("✅ Kiểu dữ liệu X:\n", X.dtypes)
print("✅ Tổng số NaN trong X:", X.isnull().sum().sum())
print("✅ Kiểu dữ liệu y:", y.dtype)
print("✅ Tổng số NaN trong y:", y.isnull().sum())

# 📈 Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Chuẩn hóa dữ liệu cho Linear Regression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
# Lưu scaler để dùng khi dự đoán
joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))

# 🤖 Define models
models = {
    "LinearRegression_model": LinearRegression(),
    "RandomForest_model": RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost_model": XGBRegressor(n_estimators=100, random_state=42),
    "LightGBM_model": LGBMRegressor(n_estimators=100, random_state=42)
}

# 🏁 Train and save models with basic evaluation
for name, model in models.items():
    if name == "LinearRegression_model":
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    print(f"📉 {name} MSE: {mse:.2f}")
    model_path = os.path.join(MODEL_DIR, f"{name}.pkl")
    joblib.dump(model, model_path)

print("✅ Huấn luyện xong và lưu mô hình thành công.")

# 🧾 Save feature columns
feature_path = os.path.join(MODEL_DIR, "feature_columns.pkl")
joblib.dump(list(X.columns), feature_path)
print(f"📦 Cột đặc trưng đã được lưu tại: {feature_path}")