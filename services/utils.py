import pandas as pd

def preprocess_data(df):
    # Nếu có cột 'departure_delay' thì loại bỏ các dòng thiếu giá trị này (chỉ dùng khi train)
    if 'departure_delay' in df.columns:
        df = df.dropna(subset=['departure_delay'])

    # Chuyển đổi cột thời gian thành datetime nếu có
    if 'scheduled_departure_dt' in df.columns:
        df['scheduled_departure_dt'] = pd.to_datetime(df['scheduled_departure_dt'])
        df['hour'] = df['scheduled_departure_dt'].dt.hour
        df['day_of_week'] = df['scheduled_departure_dt'].dt.dayofweek

    # Encode categorical features nếu có
    for col in ['carrier_code', 'origin_airport', 'destination_airport']:
        if col in df.columns:
            df = pd.get_dummies(df, columns=[col], drop_first=True)

    # Nếu có cột 'arrival_delay' thì tách ra làm y, còn lại là X
    if 'arrival_delay' in df.columns:
        y = df['arrival_delay']
        X = df.drop(columns=['arrival_delay'])
        return X, y
    else:
        return df, None