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

# Thông tin admin
ADMIN_EMAIL = "nguyenthihongtuyet122022@gmail.com"
ADMIN_PASSWORD = "entirety"

def get_current_user():
    return session.get('user')

def is_admin():
    user = get_current_user()
    return user and user.get('role') == 'admin'

def save_prediction_data(prediction_data):
    """Lưu dữ liệu dự đoán vào file JSON"""
    predictions_file = os.path.join(os.path.dirname(__file__), "predictions_data.json")
    
    # Đọc dữ liệu hiện tại
    if os.path.exists(predictions_file):
        with open(predictions_file, "r", encoding="utf-8") as f:
            predictions = json.load(f)
    else:
        predictions = []
    
    # Thêm dữ liệu mới
    predictions.append(prediction_data)
    
    # Lưu lại file
    with open(predictions_file, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)

def load_predictions_data():
    """Đọc dữ liệu dự đoán từ file JSON"""
    predictions_file = os.path.join(os.path.dirname(__file__), "predictions_data.json")
    
    if os.path.exists(predictions_file):
        with open(predictions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

# Route test để kiểm tra Flask hoạt động
@app.route("/test")
def test():
    return """
    <html>
    <head><title>Test Page</title></head>
    <body style="font-family:Arial; padding:20px; text-align:center; background:#f0f8ff;">
        <h1>✅ Flask đang hoạt động tốt!</h1>
        <p>Thời gian hiện tại: """ + str(datetime.now()) + """</p>
        <div style="margin:20px;">
            <a href="/" style="background:#007bff; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Về trang chủ</a>
        </div>
    </body>
    </html>
    """
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
    try:
        user = get_current_user()
        stats = load_stats()
        print(f"[DEBUG] Home page accessed by: {user}")
        print(f"[DEBUG] Stats loaded: {stats}")
        return render_template("about.html", user=user, stats=stats)
    except Exception as e:
        print(f"[ERROR] Home page error: {e}")
        return f"""
        <html>
        <head><title>Dự đoán Delay Chuyến Bay</title></head>
        <body style="font-family:Arial; padding:20px; text-align:center; background:#f0f0f0;">
            <h1>🛩️ Hệ thống dự đoán Delay chuyến bay</h1>
            <p>Trang web đang hoạt động!</p>
            <div style="margin:20px;">
                <a href="/predict" style="background:#007bff; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; margin:5px;">Dự đoán</a>
                <a href="/chat" style="background:#28a745; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; margin:5px;">Chat</a>
                <a href="/about" style="background:#17a2b8; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; margin:5px;">Giới thiệu</a>
                <a href="/admin" style="background:#dc3545; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; margin:5px;">Admin</a>
            </div>
            <p style="color:red;">Lỗi template: {e}</p>
        </body>
        </html>
        """

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
            
            # Lưu dữ liệu dự đoán
            prediction_record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_name": user["name"],
                "user_email": user["email"],
                "mode": mode,
                "origin_airport": request.form["origin_airport"],
                "destination_airport": request.form["destination_airport"],
                "departure_time": request.form["departure_time"],
                "elapsed_time": int(request.form["elapsed_time"]),
                "model": request.form["model"],
                "prediction": float(prediction),
                "arrival_time": arrival_time_str,
                "prev_delay": prev_delay if mode == "prev_flight" else None,
                "carrier_code": request.form["carrier_code"],
                "tail_number": request.form["tail_number"],
                "weather_origin": {
                    "temperature": float(request.form["temp_x"]),
                    "precipitation": float(request.form["precip_x"]),
                    "wind_speed": float(request.form["wind_x"])
                },
                "weather_destination": {
                    "temperature": float(request.form["temp_y"]),
                    "precipitation": float(request.form["precip_y"]),
                    "wind_speed": float(request.form["wind_y"])
                }
            }
            save_prediction_data(prediction_record)
            
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
            # Kiểm tra admin trước
            if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
                session["user"] = {"email": ADMIN_EMAIL, "role": "admin", "name": "Admin"}
                return redirect(url_for("index"))
            
            # Kiểm tra user thường
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
    print(f"[DEBUG] Admin access attempt by user: {user}")
    
    # Chỉ cho admin truy cập
    if not is_admin():
        print(f"[DEBUG] Access denied. User role: {user.get('role') if user else 'No user'}")
        return f"""
        <html>
        <head><title>Không có quyền truy cập</title></head>
        <body style="font-family:Arial; padding:20px; text-align:center; background:#f5f7fa;">
            <div style="max-width:600px; margin:100px auto; background:white; padding:40px; border-radius:16px; box-shadow:0 8px 32px rgba(0,0,0,0.1);">
                <h2 style="color:#dc3545; margin-bottom:20px;">🚫 Không có quyền truy cập</h2>
                <p style="color:#666; margin-bottom:15px;">Bạn cần đăng nhập bằng tài khoản admin để truy cập trang này.</p>
                <div style="background:#f8f9fa; padding:20px; border-radius:8px; margin:20px 0;">
                    <p style="margin:5px 0;"><strong>Email admin:</strong> nguyenthihongtuyet122022@gmail.com</p>
                    <p style="margin:5px 0;"><strong>Mật khẩu:</strong> entirety</p>
                </div>
                <div style="margin-top:30px;">
                    <a href="/" style="background:#667eea; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; margin-right:10px;">Về trang chủ</a>
                    <a href="/signin" style="background:#28a745; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">Đăng nhập</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    print(f"[DEBUG] Admin access granted for: {user['name']}")
    
    # Đọc dữ liệu dự đoán thật
    all_predictions = load_predictions_data()
    print(f"[DEBUG] Loaded {len(all_predictions)} prediction records")
    
    # Đọc dữ liệu người dùng
    users_path = os.path.join(os.path.dirname(__file__), "users.json")
    users_count = 1  # Admin
    if os.path.exists(users_path):
        with open(users_path, "r", encoding="utf-8") as f:
            users = json.load(f)
            users_count += len(users)
    
    # Phân loại theo chế độ
    normal_predictions = [p for p in all_predictions if p.get("mode") == "normal"]
    prev_flight_predictions = [p for p in all_predictions if p.get("mode") == "prev_flight"]
    
    # Sắp xếp theo thời gian mới nhất
    all_predictions_sorted = sorted(all_predictions, key=lambda x: x.get("timestamp", ""), reverse=True)
    recent_predictions = all_predictions_sorted[:10]  # 10 dự đoán gần nhất
    
    # Tạo bảng HTML cho dữ liệu gần đây
    recent_table_rows = ""
    for i, pred in enumerate(recent_predictions, 1):
        delay_color = "#d32f2f" if pred.get("prediction", 0) > 15 else "#2e7d32"
        mode_icon = "🔄" if pred.get("mode") == "prev_flight" else "✈️"
        recent_table_rows += f"""
        <tr>
            <td style="padding:12px; border-bottom:1px solid #eee; text-align:center;">{i}</td>
            <td style="padding:12px; border-bottom:1px solid #eee;">{pred.get('timestamp', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee;">{pred.get('user_name', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee;">{pred.get('user_email', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee; text-align:center;">{mode_icon} {pred.get('mode', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee;">{pred.get('origin_airport', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee;">{pred.get('destination_airport', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee;">{pred.get('model', 'N/A')}</td>
            <td style="padding:12px; border-bottom:1px solid #eee; text-align:right; color:{delay_color}; font-weight:bold;">{pred.get('prediction', 0):.1f}</td>
        </tr>
        """
    
    if not recent_table_rows:
        recent_table_rows = """
        <tr>
            <td colspan="9" style="padding:20px; text-align:center; color:#666;">
                📋 Chưa có dữ liệu dự đoán nào được ghi nhận
            </td>
        </tr>
        """
    
    # Tạo HTML trực tiếp cho trang admin
    return f"""
    <html>
    <head><title>Admin Dashboard</title></head>
    <body style="font-family:Arial; padding:20px; background:#f5f7fa;">
        <div style="max-width:1200px; margin:0 auto;">
            <div style="text-align:center; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border-radius:16px; padding:40px; margin-bottom:32px; position:relative;">
                <h1>👑 Trang quản trị Admin</h1>
                <p>Chào mừng {user.get('name')}, đây là bảng điều khiển quản trị</p>
                <div style="position:absolute; top:20px; right:20px;">
                    <a href="/signout" style="background:rgba(255,255,255,0.2); color:white; padding:8px 16px; text-decoration:none; border-radius:5px; border:1px solid rgba(255,255,255,0.3);">
                        🚪 Đăng xuất
                    </a>
                </div>
            </div>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:24px; margin-bottom:32px;">
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">📊</div>
                    <h3 style="color:#667eea; margin-bottom:8px; font-size:18px;">Tổng dự đoán</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">{len(all_predictions)}</div>
                </div>
                
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">✈️</div>
                    <h3 style="color:#667eea; margin-bottom:8px; font-size:18px;">Chế độ thông thường</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">{len(normal_predictions)}</div>
                </div>
                
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">🔄</div>
                    <h3 style="color:#667eea; margin-bottom:8px; font-size:18px;">Chế độ chuyến trước</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">{len(prev_flight_predictions)}</div>
                </div>
                
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">👥</div>
                    <h3 style="color:#667eea; margin-bottom:8px; font-size:18px;">Người dùng</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">{users_count}</div>
                </div>
            </div>

            <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); margin-bottom:24px;">
                <h3 style="color:#667eea; margin-bottom:16px; display:flex; align-items:center;">
                    <span style="margin-right:8px;">📈</span>
                    Dữ liệu dự đoán gần đây (Top 10)
                </h3>
                <div style="overflow-x:auto;">
                    <table style="width:100%; border-collapse:collapse; font-size:14px;">
                        <thead>
                            <tr style="background:#f8f9fa;">
                                <th style="padding:12px; text-align:center; border-bottom:2px solid #dee2e6;">STT</th>
                                <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Thời gian</th>
                                <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Tên người dùng</th>
                                <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Email</th>
                                <th style="padding:12px; text-align:center; border-bottom:2px solid #dee2e6;">Chế độ</th>
                                <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Từ</th>
                                <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Đến</th>
                                <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Thuật toán</th>
                                <th style="padding:12px; text-align:right; border-bottom:2px solid #dee2e6;">Delay (phút)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recent_table_rows}
                        </tbody>
                    </table>
                </div>
            </div>

            <div style="text-align:center; margin-top:30px;">
                <a href="/" style="background:#667eea; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; margin-right:10px;">← Về trang chủ</a>
                <a href="/predict" style="background:#28a745; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; margin-right:10px;">✈️ Dự đoán</a>
                <a href="/chat" style="background:#17a2b8; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">💬 Chatbot</a>
            </div>
        </div>
    </body>
    </html>
    """
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