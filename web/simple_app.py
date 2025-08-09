from flask import Flask, request, session, redirect, url_for, flash
import json
import os

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

@app.route('/')
def home():
    user = get_current_user()
    admin_button = ""
    login_section = ""
    
    if user:
        if is_admin():
            admin_button = '''
            <a href="/admin" style="background:rgba(255,255,255,0.2); color:white; padding:15px 30px; text-decoration:none; border-radius:8px; margin:10px; display:inline-block; border:2px solid white;">
                👑 Trang Admin
            </a>
            '''
        login_section = f'''
        <div style="position:absolute; top:20px; right:20px; color:white;">
            Xin chào, {user.get('name', user.get('email'))} | 
            <a href="/logout" style="color:white; text-decoration:underline;">Đăng xuất</a>
        </div>
        '''
    else:
        login_section = '''
        <div style="position:absolute; top:20px; right:20px;">
            <a href="/login" style="background:rgba(255,255,255,0.2); color:white; padding:10px 20px; text-decoration:none; border-radius:5px; border:1px solid white;">
                Đăng nhập Admin
            </a>
        </div>
        '''
    
    return f'''
    <html>
    <head><title>Hệ thống dự đoán Delay chuyến bay</title></head>
    <body style="font-family:Arial; padding:40px; text-align:center; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; min-height:100vh; position:relative;">
        {login_section}
        <h1>🛩️ Hệ thống dự đoán Delay chuyến bay</h1>
        <p style="font-size:18px;">Dự đoán chính xác thời gian delay chuyến bay bằng AI</p>
        <div style="margin:30px;">
            <a href="/predict" style="background:rgba(255,255,255,0.2); color:white; padding:15px 30px; text-decoration:none; border-radius:8px; margin:10px; display:inline-block; border:2px solid white;">
                ✈️ Dự đoán Delay
            </a>
            <a href="/chat" style="background:rgba(255,255,255,0.2); color:white; padding:15px 30px; text-decoration:none; border-radius:8px; margin:10px; display:inline-block; border:2px solid white;">
                � Chatbot
            </a>
            <a href="/about" style="background:rgba(255,255,255,0.2); color:white; padding:15px 30px; text-decoration:none; border-radius:8px; margin:10px; display:inline-block; border:2px solid white;">
                📖 Giới thiệu
            </a>
            {admin_button}
        </div>
        <div style="margin-top:50px; font-size:14px; opacity:0.8;">
            <p>🤖 Sử dụng Machine Learning với độ chính xác cao</p>
            <p>🔍 Hỗ trợ nhiều thuật toán: Random Forest, XGBoost, LightGBM, Linear Regression</p>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            session['user'] = {
                'email': ADMIN_EMAIL,
                'name': 'Admin',
                'role': 'admin'
            }
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'error')
    
    return '''
    <html>
    <head><title>Đăng nhập Admin</title></head>
    <body style="font-family:Arial; padding:40px; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height:100vh;">
        <div style="max-width:400px; margin:0 auto; background:white; padding:40px; border-radius:16px; box-shadow:0 8px 32px rgba(0,0,0,0.3);">
            <h2 style="text-align:center; color:#333; margin-bottom:30px;">👑 Đăng nhập Admin</h2>
            <form method="POST">
                <div style="margin-bottom:20px;">
                    <label style="display:block; margin-bottom:8px; color:#555; font-weight:600;">Email:</label>
                    <input type="email" name="email" required 
                           style="width:100%; padding:12px; border:2px solid #ddd; border-radius:8px; font-size:16px; box-sizing:border-box;"
                           placeholder="nguyenthihongtuyet122022@gmail.com">
                </div>
                <div style="margin-bottom:30px;">
                    <label style="display:block; margin-bottom:8px; color:#555; font-weight:600;">Mật khẩu:</label>
                    <input type="password" name="password" required 
                           style="width:100%; padding:12px; border:2px solid #ddd; border-radius:8px; font-size:16px; box-sizing:border-box;"
                           placeholder="Nhập mật khẩu">
                </div>
                <button type="submit" 
                        style="width:100%; background:#667eea; color:white; padding:15px; border:none; border-radius:8px; font-size:16px; font-weight:600; cursor:pointer;">
                    🔐 Đăng nhập
                </button>
            </form>
            <div style="text-align:center; margin-top:20px;">
                <a href="/" style="color:#667eea; text-decoration:none;">← Về trang chủ</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Đã đăng xuất thành công!', 'info')
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not is_admin():
        flash('Bạn cần đăng nhập bằng tài khoản admin để truy cập trang này!', 'error')
        return redirect(url_for('login'))
    
    user = get_current_user()
    return f'''
    <html>
    <head><title>Admin Dashboard</title></head>
    <body style="font-family:Arial; padding:20px; background:#f5f7fa;">
        <div style="max-width:1200px; margin:0 auto;">
            <div style="text-align:center; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border-radius:16px; padding:40px; margin-bottom:32px;">
                <h1>👑 Trang quản trị Admin</h1>
                <p>Chào mừng {user.get('name')}, đây là bảng điều khiển quản trị</p>
            </div>

            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); gap:24px; margin-bottom:32px;">
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">📊</div>
                    <h3 style="color:#667eea; margin-bottom:8px;">Tổng dự đoán</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">127</div>
                </div>
                
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">✈️</div>
                    <h3 style="color:#667eea; margin-bottom:8px;">Chế độ thông thường</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">89</div>
                </div>
                
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">🔄</div>
                    <h3 style="color:#667eea; margin-bottom:8px;">Chế độ chuyến trước</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">38</div>
                </div>
                
                <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1); text-align:center;">
                    <div style="font-size:48px; margin-bottom:12px;">👥</div>
                    <h3 style="color:#667eea; margin-bottom:8px;">Người dùng</h3>
                    <div style="font-size:32px; font-weight:bold; color:#333;">45</div>
                </div>
            </div>

            <div style="background:white; padding:24px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.1);">
                <h3 style="color:#667eea; margin-bottom:16px;">📈 Dữ liệu dự đoán gần đây</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background:#f8f9fa;">
                            <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Thời gian</th>
                            <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Từ</th>
                            <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Đến</th>
                            <th style="padding:12px; text-align:left; border-bottom:2px solid #dee2e6;">Thuật toán</th>
                            <th style="padding:12px; text-align:right; border-bottom:2px solid #dee2e6;">Delay (phút)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding:12px; border-bottom:1px solid #eee;">2025-08-09 14:30</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">LAX</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">JFK</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">Random Forest</td>
                            <td style="padding:12px; border-bottom:1px solid #eee; text-align:right; color:#d32f2f; font-weight:bold;">25.3</td>
                        </tr>
                        <tr>
                            <td style="padding:12px; border-bottom:1px solid #eee;">2025-08-09 13:15</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">SFO</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">ORD</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">XGBoost</td>
                            <td style="padding:12px; border-bottom:1px solid #eee; text-align:right; color:#2e7d32; font-weight:bold;">8.7</td>
                        </tr>
                        <tr>
                            <td style="padding:12px; border-bottom:1px solid #eee;">2025-08-09 12:45</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">DFW</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">LAX</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">LightGBM</td>
                            <td style="padding:12px; border-bottom:1px solid #eee; text-align:right; color:#2e7d32; font-weight:bold;">12.1</td>
                        </tr>
                        <tr>
                            <td style="padding:12px; border-bottom:1px solid #eee;">2025-08-09 11:20</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">MIA</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">BOS</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">Linear Regression</td>
                            <td style="padding:12px; border-bottom:1px solid #eee; text-align:right; color:#d32f2f; font-weight:bold;">18.9</td>
                        </tr>
                        <tr>
                            <td style="padding:12px; border-bottom:1px solid #eee;">2025-08-09 10:55</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">SEA</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">DEN</td>
                            <td style="padding:12px; border-bottom:1px solid #eee;">XGBoost</td>
                            <td style="padding:12px; border-bottom:1px solid #eee; text-align:right; color:#2e7d32; font-weight:bold;">5.2</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div style="text-align:center; margin-top:30px;">
                <a href="/" style="background:#667eea; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; margin-right:10px;">← Về trang chủ</a>
                <a href="/logout" style="background:#dc3545; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">🚪 Đăng xuất</a>
            </div>
        </div>
    </body>
    </html>
    '''

# Thêm các route placeholder cho các trang khác
@app.route('/predict')
def predict():
    return '''
    <html>
    <head><title>Dự đoán Delay</title></head>
    <body style="font-family:Arial; padding:40px; text-align:center; background:#f0f8ff;">
        <h1>✈️ Trang dự đoán Delay</h1>
        <p>Tính năng đang được phát triển...</p>
        <a href="/" style="background:#667eea; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">← Về trang chủ</a>
    </body>
    </html>
    '''

@app.route('/chat')
def chat():
    return '''
    <html>
    <head><title>Chatbot</title></head>
    <body style="font-family:Arial; padding:40px; text-align:center; background:#f0f8ff;">
        <h1>💬 Chatbot AI</h1>
        <p>Tính năng đang được phát triển...</p>
        <a href="/" style="background:#667eea; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">← Về trang chủ</a>
    </body>
    </html>
    '''

@app.route('/about')
def about():
    return '''
    <html>
    <head><title>Giới thiệu</title></head>
    <body style="font-family:Arial; padding:40px; text-align:center; background:#f0f8ff;">
        <h1>📖 Giới thiệu hệ thống</h1>
        <p>Tính năng đang được phát triển...</p>
        <a href="/" style="background:#667eea; color:white; padding:12px 24px; text-decoration:none; border-radius:8px;">← Về trang chủ</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, port=5001)
