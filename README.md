# Flight Delay Prediction System

Ứng dụng dự đoán độ trễ chuyến bay dựa trên dữ liệu lịch sử và thời tiết, sử dụng:
- Linear Regression
- Random Forest
- XGBoost
- LightGBM

## Hướng dẫn sử dụng
1. Đặt file `flight_delay_data.csv` vào thư mục `data/`
2. Cài thư viện:

pip install -r requirements.txt

3. Huấn luyện mô hình:
python models/train_model.py

4. Chạy Flask:
python web/app.py

5. Truy cập: `http://localhost:5000`

Opened Simple Browser at http://127.0.0.1:5000