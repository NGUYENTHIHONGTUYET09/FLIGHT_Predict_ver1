# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from flask import Flask, render_template, request
# import pandas as pd
# from services.predictor import predict_delay

# app = Flask(__name__)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     prediction = None
#     if request.method == "POST":
#         model_name = request.form['model']
#         input_data = {
#             "scheduled_elapsed_time": int(request.form["elapsed_time"]),
#             "scheduled_departure_dt": request.form["departure_time"],
#             "arrival_delay": 0,
#             "tail_number": request.form["tail_number"],
#             "carrier_code": request.form["carrier_code"],
#             "origin_airport": request.form["origin_airport"],
#             "destination_airport": request.form["destination_airport"],
#             "HourlyDryBulbTemperature_x": float(request.form["temp_x"]),
#             "HourlyPrecipitation_x": float(request.form["precip_x"]),
#             "HourlyWindSpeed_x": float(request.form["wind_x"]),
#             "HourlyDryBulbTemperature_y": float(request.form["temp_y"]),
#             "HourlyPrecipitation_y": float(request.form["precip_y"]),
#             "HourlyWindSpeed_y": float(request.form["wind_y"])
#         }
#         user_df = pd.DataFrame([input_data])
#         prediction = predict_delay(model_name, user_df)

#     return render_template("index.html", prediction=prediction)

# if __name__ == "__main__":
#     app.run(debug=True)

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request
import pandas as pd
from services.predictor import predict_delay
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    error = None
    arrival_time_str = None
    form_data = {}
    prev_delay = None
    if request.method == "POST":
        form_data = request.form.to_dict()
        mode = request.form.get("mode", "normal")
        input_data = {
            "scheduled_elapsed_time": int(request.form["elapsed_time"]),
            "scheduled_departure_dt": request.form["departure_time"],
            "arrival_delay": 0,
            "tail_number": request.form["tail_number"],
            "carrier_code": request.form["carrier_code"],
            "origin_airport": request.form["origin_airport"],
            "destination_airport": request.form["destination_airport"],
            "HourlyDryBulbTemperature_x": float(request.form["temp_x"]),
            "HourlyPrecipitation_x": float(request.form["precip_x"]),
            "HourlyWindSpeed_x": float(request.form["wind_x"]),
            "HourlyDryBulbTemperature_y": float(request.form["temp_y"]),
            "HourlyPrecipitation_y": float(request.form["precip_y"]),
            "HourlyWindSpeed_y": float(request.form["wind_y"])
        }
        # Nếu chọn chế độ chuyến bay trước, lấy thêm thông tin
        if mode == "prev_flight":
            prev_departure = request.form.get("prev_departure_time")
            prev_arrival = request.form.get("prev_arrival_time")
            if prev_departure and prev_arrival:
                prev_departure_dt = datetime.strptime(prev_departure, "%Y-%m-%dT%H:%M")
                prev_arrival_dt = datetime.strptime(prev_arrival, "%Y-%m-%dT%H:%M")
                scheduled_elapsed = int(request.form["elapsed_time"])
                prev_delay = (prev_arrival_dt - prev_departure_dt).total_seconds() / 60 - scheduled_elapsed
                # Nếu muốn đưa prev_delay vào mô hình, thêm dòng sau:
                input_data["prev_delay"] = prev_delay
        user_df = pd.DataFrame([input_data])
        try:
            prediction = predict_delay(request.form['model'], user_df)
            departure_time = datetime.strptime(request.form["departure_time"], "%Y-%m-%dT%H:%M")
            total_minutes = int(request.form["elapsed_time"]) + float(prediction)
            arrival_time = departure_time + timedelta(minutes=total_minutes)
            arrival_time_str = arrival_time.strftime("%H:%M, %d/%m/%Y")
        except Exception as e:
            error = f"Lỗi khi dự đoán: {e}"

    return render_template("index.html", prediction=prediction, error=error, arrival_time_str=arrival_time_str, form_data=form_data, prev_delay=prev_delay)
if __name__ == "__main__":
    app.run(debug=True)