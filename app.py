from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
from datetime import datetime
import pandas as pd
import openpyxl

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# إعدادات ملفات البيانات
DB_PATH = r"C:\Users\Ali-00\Desktop\expenses.xlsx"
LOG_PATH = r"C:\Users\Ali-00\Desktop\activity_log.xlsx"

# تحديث أعمدة المصروفات لتشمل الحقول الجديدة
EXPENSE_COLUMNS = [
    "ID", "MilitaryNumber", "Rank", "FullName", "SubUnit", "MainUnit",
    "NationalID", "Degree", "Salary", "ShoeSize", "SuitSize", "Height",
    "PhoneNumber", "RelativeName", "RelativePhone", "Medals", "Courses",
    "ExpenseDate", "ReportTitle", "ProfileImage"
]
LOG_COLUMNS = ["Username", "Action", "Timestamp", "Details"]

# إنشاء ملفات البيانات إذا لم تكن موجودة
def create_excel_file(path, columns):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_excel(path, index=False, engine='openpyxl')

create_excel_file(DB_PATH, EXPENSE_COLUMNS)
create_excel_file(LOG_PATH, LOG_COLUMNS)

# قاعدة بيانات المستخدمين (مثال مبسط)
users = [
    {"id": 1, "username": "altargi", "password": "altargi", "role": "admin"}
]

def log_activity(username, action, details=""):
    df = pd.read_excel(LOG_PATH, engine='openpyxl')
    new_entry = pd.DataFrame([{
        "Username": username,
        "Action": action,
        "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Details": details
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_excel(LOG_PATH, index=False, engine='openpyxl')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                log_activity(username, "Login")
                return redirect(url_for('dashboard'))
        error = "اسم المستخدم أو كلمة المرور غير صحيحة!"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(session['username'], "Logout")
        session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            username = session.get('username')
            # التقاط الحقول الجديدة من النموذج
            military_number = request.form['military_number']
            rank = request.form['rank']
            fullname = request.form['fullname']
            sub_unit = request.form.get('sub_unit', '')
            main_unit = request.form.get('main_unit', '')
            national_id = request.form.get('national_id', '')
            degree = request.form.get('degree', '')
            salary = float(request.form['salary']) if request.form['salary'] else 0
            shoe_size = request.form.get('shoe_size', '')
            suit_size = request.form.get('suit_size', '')
            height = request.form.get('height', '')
            phone_number = request.form.get('phone_number', '')
            relative_name = request.form.get('relative_name', '')
            relative_phone = request.form.get('relative_phone', '')
            medals = request.form.get('medals', '')
            courses = request.form.get('courses', '')
            date_str = request.form['date']
            reportTitle = request.form.get('reportTitle', '')
            expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # معالجة رفع الصورة الشخصية
            profile_image = request.files.get('profile_image')
            saved_filename = ""
            if profile_image:
                upload_folder = os.path.join(app.root_path, 'static/uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{profile_image.filename}"
                filepath = os.path.join(upload_folder, filename)
                profile_image.save(filepath)
                saved_filename = f"uploads/{filename}"  # مسار نسبي من مجلد static

            df = pd.read_excel(DB_PATH, engine='openpyxl')
            new_id = 1 if df.empty else int(df['ID'].max()) + 1

            new_row = pd.DataFrame([{
                "ID": new_id,
                "MilitaryNumber": military_number,
                "Rank": rank,
                "FullName": fullname,
                "SubUnit": sub_unit,
                "MainUnit": main_unit,
                "NationalID": national_id,
                "Degree": degree,
                "Salary": salary,
                "ShoeSize": shoe_size,
                "SuitSize": suit_size,
                "Height": height,
                "PhoneNumber": phone_number,
                "RelativeName": relative_name,
                "RelativePhone": relative_phone,
                "Medals": medals,
                "Courses": courses,
                "ExpenseDate": expense_date,
                "ReportTitle": reportTitle,
                "ProfileImage": saved_filename
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(DB_PATH, index=False, engine='openpyxl')

            log_activity(username, "Added Expense", f"{fullname} - {salary}")
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # قراءة البيانات للعرض في حال الطلب GET
    df = pd.read_excel(DB_PATH, engine='openpyxl')
    df['ExpenseDate'] = df['ExpenseDate'].astype(str)
    expenses_data = df.to_dict('records')
    return render_template('expenses.html', expenses_data=expenses_data)

@app.route('/activity_log')
def activity_log():
    if 'username' not in session:
        return redirect(url_for('login'))
    df = pd.read_excel(LOG_PATH, engine='openpyxl')
    logs = df.to_dict('records')
    return render_template('activity_log.html', logs=logs)

@app.route('/control_panel')
def control_panel():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('control_panel.html', username=session['username'])

@app.route('/user_management')
def user_management():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('user_management.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    new_id = max(user['id'] for user in users) + 1 if users else 1
    new_user = {
        "id": new_id,
        "username": username,
        "password": password,
        "role": role
    }
    users.append(new_user)
    log_activity(session['username'], "User Added", f"Username: {username}")
    return redirect(url_for('user_management'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    global users
    users = [user for user in users if user['id'] != user_id]
    log_activity(session['username'], "User Deleted", f"User ID: {user_id}")
    return redirect(url_for('user_management'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5454, debug=True)
