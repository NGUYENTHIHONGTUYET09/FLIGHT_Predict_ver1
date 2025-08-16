import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
from services.predictor import predict_delay

# create a minimal sample matching expected columns after preprocess
sample = {
    'scheduled_elapsed_time': [60],
    'scheduled_departure_dt': ['2025-08-17T10:00'],
    'arrival_delay': [0],
    'tail_number': ['VN-A123'],
    'carrier_code': ['VN'],
    'origin_airport': ['SGN'],
    'destination_airport': ['HAN'],
    'HourlyDryBulbTemperature_x': [30.0],
    'HourlyPrecipitation_x': [0.0],
    'HourlyWindSpeed_x': [5.0],
    'HourlyDryBulbTemperature_y': [28.0],
    'HourlyPrecipitation_y': [0.0],
    'HourlyWindSpeed_y': [3.0]
}

df = pd.DataFrame(sample)

try:
    pred = predict_delay('Domino_model', df)
    print('PREDICTION_OK:', pred)
except Exception as e:
    print('PREDICTION_ERROR:', e)
    import traceback
    traceback.print_exc()
