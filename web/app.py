import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
from services.predictor import predict_delay
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'flightdelay_secret_key_2025'

def get_current_user():
    return session.get('user')

def load_stats():
    """Load system statistics from admin data"""
    try:
        if os.path.exists('admin_data.json'):
            with open('admin_data.json', 'r', encoding='utf-8') as f:
                admin_data = json.load(f)
            return admin_data.get('stats', {
                'total_predictions': 0,
                'accuracy': 0.85,
                'total_users': 0
            })
        else:
            return {
                'total_predictions': 0,
                'accuracy': 0.85,
                'total_users': 0
            }
    except:
        return {
            'total_predictions': 0,
            'accuracy': 0.85,
            'total_users': 0
        }

# Trang chủ (giới thiệu)
@app.route("/")
def index():
    user = get_current_user()
    stats = load_stats()
    return render_template("about.html", user=user, stats=stats)

# Trang dự đoán
@app.route("/predict", methods=["GET", "POST"])
def predict():
    prediction = None
    error = None
    arrival_time_str = None
    form_data = {}
    prev_delay = None
    user = get_current_user()
    
    # Bắt buộc đăng nhập mới được dự đoán
    if not user:
        flash("Bạn cần đăng nhập để sử dụng chức năng dự đoán.")
        return redirect(url_for("signin"))
    
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
            "HourlyWindSpeed_y": float(request.form["wind_y"]),
            "name": user["name"],
            "email": user["email"],
            "model": request.form["model"]
        }
        
        if mode == "prev_flight":
            prev_departure = request.form.get("prev_departure_time")
            prev_arrival = request.form.get("prev_arrival_time")
            if prev_departure and prev_arrival:
                prev_departure_dt = datetime.strptime(prev_departure, "%Y-%m-%dT%H:%M")
                prev_arrival_dt = datetime.strptime(prev_arrival, "%Y-%m-%dT%H:%M")
                scheduled_elapsed = int(request.form["elapsed_time"])
                prev_delay = (prev_arrival_dt - prev_departure_dt).total_seconds() / 60 - scheduled_elapsed
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
    
    return render_template("predict.html", prediction=prediction, error=error, arrival_time_str=arrival_time_str, form_data=form_data, prev_delay=prev_delay, user=user)

# Trang chat hỗ trợ
def get_bot_response(message):
    """Chatbot tự động trả lời theo keyword"""
    message = message.lower().strip()
    
    # Từ khóa về dự đoán
    if any(keyword in message for keyword in ['dự đoán', 'du doan', 'predict', 'dự báo', 'du bao']):
        return "🛫 Để dự đoán chậm chuyến bay, bạn cần đăng nhập và truy cập mục 'Dự đoán'. Hệ thống sẽ yêu cầu thông tin chuyến bay và thời tiết để đưa ra kết quả chính xác nhất!"
    
    # Từ khóa về đăng nhập
    elif any(keyword in message for keyword in ['đăng nhập', 'dang nhap', 'login', 'đăng ký', 'dang ky', 'register']):
        return "🔐 Bạn có thể đăng nhập/đăng ký bằng cách click vào nút 'Đăng nhập / Đăng ký' ở góc phải trên cùng. Nếu chưa có tài khoản, hãy chọn 'Đăng ký' trong modal popup!"
    
    # Từ khóa về thuật toán
    elif any(keyword in message for keyword in ['thuật toán', 'thuat toan', 'algorithm', 'model', 'mô hình', 'mo hinh']):
        return "🤖 Hệ thống sử dụng 4 thuật toán Machine Learning: RandomForest, XGBoost, LightGBM và Linear Regression. Bạn có thể chọn thuật toán phù hợp trong trang dự đoán!"
    
    # Từ khóa về độ chính xác
    elif any(keyword in message for keyword in ['độ chính xác', 'do chinh xac', 'accuracy', 'chính xác', 'chinh xac']):
        return "🎯 Độ chính xác của hệ thống lên đến 85% dựa trên dữ liệu thời tiết và thông tin chuyến bay thực tế. Kết quả sẽ càng chính xác hơn khi bạn cung cấp đủ thông tin!"
    
    # Từ khóa về thời tiết
    elif any(keyword in message for keyword in ['thời tiết', 'thoi tiet', 'weather', 'nhiệt độ', 'nhiet do', 'mưa', 'gió', 'gio']):
        return "🌤️ Thời tiết là yếu tố quan trọng ảnh hưởng đến chuyến bay. Hệ thống cần thông tin: nhiệt độ, lượng mưa, tốc độ gió tại sân bay xuất phát và đích đến!"
    
    # Từ khóa về admin
    elif any(keyword in message for keyword in ['admin', 'quản trị', 'quan tri', 'administrator']):
        return "👑 Tính năng quản trị chỉ dành cho admin. Admin có thể xem thống kê chi tiết, quản lý dữ liệu và các báo cáo về hệ thống dự đoán!"
    
    # Từ khóa về hỗ trợ
    elif any(keyword in message for keyword in ['hỗ trợ', 'ho tro', 'help', 'giúp', 'giup', 'support']):
        return "💬 Tôi có thể giúp bạn về:\n- Cách sử dụng dự đoán\n- Đăng nhập/đăng ký\n- Thông tin thuật toán\n- Các tính năng của hệ thống\nHãy hỏi tôi bất cứ điều gì!"
    
    # Từ khóa chào hỏi
    elif any(keyword in message for keyword in ['xin chào', 'chào', 'hello', 'hi', 'hey']):
        return "👋 Xin chào! Tôi là chatbot hỗ trợ hệ thống dự đoán chậm chuyến bay. Bạn cần hỗ trợ gì ạ?"
    
    # Từ khóa cảm ơn
    elif any(keyword in message for keyword in ['cảm ơn', 'cam on', 'thank', 'thanks']):
        return "😊 Không có gì! Tôi luôn sẵn sàng giúp đỡ bạn. Nếu có thêm câu hỏi, đừng ngần ngại hỏi nhé!"
    
    # Từ khóa về dữ liệu
    elif any(keyword in message for keyword in ['dữ liệu', 'du lieu', 'data', 'thông tin', 'thong tin']):
        return "📊 Hệ thống sử dụng dữ liệu thời tiết thực tế và thông tin chuyến bay để dự đoán. Tất cả dữ liệu được bảo mật và chỉ dùng cho mục đích dự đoán!"
    
    # Từ khóa về bảo mật
    elif any(keyword in message for keyword in ['bảo mật', 'bao mat', 'security', 'an toàn', 'an toan']):
        return "🔒 Hệ thống đảm bảo bảo mật tuyệt đối! Dữ liệu cá nhân được mã hóa và chỉ sử dụng cho việc dự đoán. Bạn cần đăng nhập để đảm bảo an toàn thông tin!"
    
    # Default response
    else:
        return f"🤔 Tôi chưa hiểu câu hỏi '{message}' của bạn. Bạn có thể hỏi về: dự đoán, đăng nhập, thuật toán, độ chính xác, thời tiết, hỗ trợ. Hoặc gõ 'help' để xem hướng dẫn!"

@app.route("/chat", methods=["GET", "POST"])
def chat():
    user = get_current_user()
    chat_history = []
    
    if request.method == "POST":
        message = request.form.get("message")
        if message:
            # Lưu tin nhắn user
            if 'chat_history' not in session:
                session['chat_history'] = []
            
            # Thêm tin nhắn của user
            session['chat_history'].append({
                'sender': 'user',
                'name': user['name'] if user else 'Khách',
                'text': message,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            
            # Tự động trả lời bằng bot
            bot_response = get_bot_response(message)
            session['chat_history'].append({
                'sender': 'bot',
                'name': 'FlightBot',
                'text': bot_response,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            })
            
            chat_history = session['chat_history']
    else:
        chat_history = session.get('chat_history', [])
    
    return render_template("chat.html", user=user, chat_history=chat_history)

# Đăng nhập/đăng ký
@app.route("/signin", methods=["GET", "POST"])
def signin():
    error = None
    if request.method == "POST":
        action = request.form.get("action")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        name = request.form.get("name", "")
        
        users_path = os.path.join(os.path.dirname(__file__), "users.json")
        if os.path.exists(users_path):
            with open(users_path, "r", encoding="utf-8") as f:
                users = json.load(f)
        else:
            users = []
        
        if action == "login":
            user = next((u for u in users if u["email"] == email and u["password"] == password), None)
            if user:
                session["user"] = {"email": user["email"], "role": user.get("role", "user"), "name": user.get("name", user["email"])}
                return redirect(url_for("index"))
            else:
                error = "Sai email hoặc mật khẩu."
        elif action == "register":
            if any(u["email"] == email for u in users):
                error = "Email đã tồn tại."
            elif not name:
                error = "Vui lòng nhập tên."
            elif not email or not password:
                error = "Vui lòng nhập đầy đủ thông tin."
            else:
                new_user = {"email": email, "password": password, "role": "user", "name": name}
                users.append(new_user)
                with open(users_path, "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
                session["user"] = {"email": email, "role": "user", "name": name}
                return redirect(url_for("index"))
    
    # Nếu có lỗi, render trang chủ với modal mở
    if error:
        stats = load_stats()
        return render_template("about.html", error=error, user=get_current_user(), stats=stats)
    
    return render_template("signin.html", error=error, user=get_current_user())

# Đăng xuất
@app.route("/signout")
def signout():
    session.pop("user", None)
    session.pop("chat_history", None)
    return redirect(url_for("index"))

# Trang quản trị admin
@app.route("/admin")
def admin_dashboard():
    user = get_current_user()
    # Chỉ cho admin truy cập
    if not user or user["role"] != "admin":
        flash("Bạn không có quyền truy cập trang này.")
        return redirect(url_for("index"))
    
    # Đọc dữ liệu thống kê
    data_path = os.path.join(os.path.dirname(__file__), "admin_data.json")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = []
    
    # Phân loại theo chế độ
    normal_list = [d for d in all_data if d.get("mode") == "normal"]
    prev_flight_list = [d for d in all_data if d.get("mode") == "prev_flight"]
    return render_template("admin.html", user=user, normal_list=normal_list, prev_flight_list=prev_flight_list)
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

#     return {"message": "Logged out successfully"}

if __name__ == "__main__":
    app.run(debug=True)

# if __name__ == "__main__":
#     app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)