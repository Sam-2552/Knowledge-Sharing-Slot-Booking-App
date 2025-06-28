from flask import Flask, render_template, request, redirect, url_for, make_response, g, flash, send_from_directory
import sqlite3
import jwt
import datetime
from functools import wraps
import urllib.parse
from datetime import timedelta, date, time as dtime
import os
from werkzeug.utils import secure_filename
from dateutil.relativedelta import relativedelta
import calendar
import logging
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a23hd*#8234sDAk)'
app.config['DATABASE'] = 'users.db'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(UPLOAD_FOLDER, 'logs3.txt')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- DB Setup ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        topic TEXT,
        agenda TEXT,
        presenter_id INTEGER,
        presenter_name TEXT,
        status TEXT NOT NULL DEFAULT 'available',
        approved_by_id INTEGER,
        approved_by_name TEXT,
        file_path TEXT,
        link TEXT,
        FOREIGN KEY (presenter_id) REFERENCES users(id),
        FOREIGN KEY (approved_by_id) REFERENCES users(id)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS slot_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        approval_reason TEXT,
        rejection_reason TEXT,
        feedback TEXT,
        comments TEXT,
        points_awarded INTEGER,
        topic TEXT,
        agenda TEXT,
        file_path TEXT,
        link TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (slot_id) REFERENCES slots(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    db.commit()
    # Insert default users if not exist
    db.execute('INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', ('Admin', 'admin@example.com', 'admin123', 'admin'))
    db.execute('INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', ('User', 'user@example.com', 'password', 'user'))
    db.commit()

# --- JWT Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return redirect(url_for('login'))
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user = data['email']
        except Exception:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# --- Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        if user:
            token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            resp = make_response(redirect(url_for('dashboard')))
            resp.set_cookie('token', token)
            return resp
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/dashboard')
@token_required
def dashboard():
    db = get_db()
    user_email = g.get('user')
    user = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    if user and user['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    user = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    # Week navigation
    all_dates = get_week_dates()  # This now returns all dates in the range
    # Only include weekdays (Mon-Fri)
    all_weekdays = [d for d in all_dates if d.weekday() < 5]
    # Group into weeks of 5 days (Mon-Fri)
    weeks = [all_weekdays[i:i+5] for i in range(0, len(all_weekdays), 5)]
    # Find the current week index
    today = date.today()
    current_week_index = 0
    for idx, week in enumerate(weeks):
        if today in week:
            current_week_index = idx
            break
    # Determine week number from query param, default to current week
    week_number = request.args.get('week')
    if week_number is not None:
        week_number = int(week_number)
        if week_number < 0 or week_number >= len(weeks):
            week_number = current_week_index
    else:
        week_number = current_week_index
    week_dates = weeks[week_number]
    time_slots = get_time_slots()
    # Ensure slots exist for the week
    for day in week_dates:
        for slot_time in time_slots:
            slot_date = day.strftime('%Y-%m-%d')
            slot_time_str = slot_time.strftime('%H:%M')
            exists = db.execute('SELECT 1 FROM slots WHERE date = ? AND time = ?', (slot_date, slot_time_str)).fetchone()
            if not exists:
                db.execute('INSERT INTO slots (date, time) VALUES (?, ?)', (slot_date, slot_time_str))
    db.commit()
    # Fetch all slots for the week
    slots = db.execute('SELECT * FROM slots WHERE date IN ({}) ORDER BY date, time'.format(
        ','.join(['?']*len(week_dates))), [d.strftime('%Y-%m-%d') for d in week_dates]).fetchall()
    # Build a lookup for slots by (date, time)
    slots_lookup = {}
    booked_dates = set()
    for slot in slots:
        slots_lookup[(slot['date'], slot['time'])] = slot
        if slot['status'] in ('booked', 'approved'):
            booked_dates.add(slot['date'])
    today_str = today.strftime('%Y-%m-%d')
    now = datetime.datetime.now()
    now_str = now.strftime('%H:%M')
    current_month = today.strftime('%B')
    current_date = today.strftime('%d %b %Y')
    current_time = now.strftime('%I:%M %p')
    return render_template('dashboard.html', user=user, slots_lookup=slots_lookup, week_dates=week_dates, time_slots=time_slots, booked_dates=booked_dates, today_str=today_str, now_str=now_str, week_number=week_number, total_weeks=len(weeks), current_month=current_month, current_date=current_date, current_time=current_time)

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('token', '', expires=0)
    return resp

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')  # Get role from form, default to 'user'
        if role not in ['user', 'admin']:
            role = 'user'  # Any invalid value defaults to 'user'
        db = get_db()
        try:
            db.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', (name, email, password, role))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = 'Email already registered.'
    return render_template('signup.html', error=error)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = None
    email = request.args.get('email', '')  # Get email from query parameter for XSS
    if request.method == 'POST':
        email = request.form['email']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            reset_url = url_for('reset_password', token=token, _external=True)
            with open('uploads/logs3.txt', 'a') as log_file:
                log_file.write(f"Password reset link for {email}: {reset_url}\n")
            flash(f'A password reset link has been generated for {email}. Contact admin@example.com to fetch from logs.')
        else:
            flash(f'If the email {email} exists, a reset link will be sent.')
        # Redirect back to the same page with email parameter in URL
        return redirect(f'/forgot-password?email={urllib.parse.quote(email)}')
    return render_template('forgot_password.html', message=message, email=email)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    error = None
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        email = data['email']
        print(email)
    except Exception:
        error = 'The reset link is invalid or has expired.'
        return render_template('reset_password.html', error=error)
    if request.method == 'POST':
        password = request.form['password']
        db = get_db()
        db.execute('UPDATE users SET password = ? WHERE email = ?', (password, email))
        db.commit()
        flash('Your password has been reset. Please log in.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', error=error)

@app.route('/book-slot', methods=['POST'])
@token_required
def book_slot():
    db = get_db()
    user_email = g.get('user')
    user = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    slot_id = request.form['slot_id']
    topic = request.form['topic']
    agenda = request.form.get('agenda')
    link = request.form.get('link')
    if link:
        import requests
        try:
            # Try to make a HEAD request to check if the link is valid
            response = requests.head(link, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                flash('Invalid link provided. Please check the URL and try again.')
                return redirect(url_for('dashboard'))
        except requests.RequestException:
            flash('Invalid link provided. Please check the URL and try again.')
            return redirect(url_for('dashboard'))
    file_path = None
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    # Check if slot is available
    slot = db.execute('SELECT * FROM slots WHERE id = ?', (slot_id,)).fetchone()
    if slot and slot['status'] == 'available':
        db.execute('UPDATE slots SET topic = ?, agenda = ?, presenter_id = ?, presenter_name = ?, status = ?, file_path = ?, link = ? WHERE id = ?',
                   (topic, agenda, user['id'], user['name'], 'booked', file_path, link, slot_id))
        # Insert into slot_activity with topic, agenda, file_path, link
        db.execute('INSERT INTO slot_activity (slot_id, user_id, status, topic, agenda, file_path, link) VALUES (?, ?, ?, ?, ?, ?, ?)', (slot_id, user['id'], 'booked', topic, agenda, file_path, link))
        db.commit()
        return redirect(url_for('dashboard'))
    else:
        flash('Slot is no longer available.')
        return redirect(url_for('dashboard'))

@app.route('/my-activity')
@token_required
def my_activity():
    db = get_db()
    user_email = g.get('user')
    user = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    is_admin = user['role'] == 'admin'
    # Get all activity (admin) or user activity
    if is_admin:
        # Admin sees all activity, join with users to get username
        all_activities = db.execute('''
            SELECT sa.*, u.name as username FROM slot_activity sa
            JOIN users u ON sa.user_id = u.id
            ORDER BY sa.created_at DESC
        ''').fetchall()
    else:
        all_activities = db.execute('''SELECT * FROM slot_activity WHERE user_id = ? ORDER BY created_at DESC''', (user['id'],)).fetchall()
    # Group activities by week (Mon-Fri based on created_at)
    def get_week_start(dt):
        return dt - timedelta(days=dt.weekday())
    activities_by_week = {}
    for a in all_activities:
        dt = datetime.datetime.strptime(a['created_at'][:10], '%Y-%m-%d')
        week_start = get_week_start(dt)
        if week_start not in activities_by_week:
            activities_by_week[week_start] = []
        activities_by_week[week_start].append(a)
    sorted_weeks = sorted(activities_by_week.keys(), reverse=True)
    week_number = int(request.args.get('week', 0))
    if not sorted_weeks:
        week_dates = []
        activities = []
        total_weeks = 0
    else:
        if week_number < 0 or week_number >= len(sorted_weeks):
            week_number = 0
        week_dates = [sorted_weeks[week_number] + timedelta(days=i) for i in range(5)]
        activities = activities_by_week.get(sorted_weeks[week_number], [])
        total_weeks = len(sorted_weeks)
    return render_template('my_activity.html', user=user, activities=activities, is_admin=is_admin, week_number=week_number, total_weeks=total_weeks, week_dates=week_dates)

@app.route('/admin-dashboard')
@token_required
def admin_dashboard():
    db = get_db()
    user_email = g.get('user')
    user = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    if user['role'] != 'admin':
        return redirect(url_for('dashboard'))
    # Week navigation (same as dashboard)
    all_dates = get_week_dates()
    all_weekdays = [d for d in all_dates if d.weekday() < 5]
    weeks = [all_weekdays[i:i+5] for i in range(0, len(all_weekdays), 5)]
    today = date.today()
    current_week_index = 0
    for idx, week in enumerate(weeks):
        if today in week:
            current_week_index = idx
            break
    week_number = request.args.get('week')
    if week_number is not None:
        week_number = int(week_number)
        if week_number < 0 or week_number >= len(weeks):
            week_number = current_week_index
    else:
        week_number = current_week_index
    week_dates = weeks[week_number]
    time_slots = get_time_slots()
    for day in week_dates:
        for slot_time in time_slots:
            slot_date = day.strftime('%Y-%m-%d')
            slot_time_str = slot_time.strftime('%H:%M')
            exists = db.execute('SELECT 1 FROM slots WHERE date = ? AND time = ?', (slot_date, slot_time_str)).fetchone()
            if not exists:
                db.execute('INSERT INTO slots (date, time) VALUES (?, ?)', (slot_date, slot_time_str))
    db.commit()
    slots = db.execute('SELECT * FROM slots WHERE date IN ({}) ORDER BY date, time'.format(
        ','.join(['?']*len(week_dates))), [d.strftime('%Y-%m-%d') for d in week_dates]).fetchall()
    slots_lookup = {}
    booked_dates = set()
    for slot in slots:
        slots_lookup[(slot['date'], slot['time'])] = slot
        if slot['status'] in ('booked', 'approved'):
            booked_dates.add(slot['date'])
    today_str = today.strftime('%Y-%m-%d')
    now = datetime.datetime.now()
    now_str = now.strftime('%H:%M')
    current_month = today.strftime('%B')
    current_date = today.strftime('%d %b %Y')
    current_time = now.strftime('%I:%M %p')
    return render_template('dashboard.html', user=user, slots_lookup=slots_lookup, week_dates=week_dates, time_slots=time_slots, booked_dates=booked_dates, today_str=today_str, now_str=now_str, week_number=week_number, total_weeks=len(weeks), current_month=current_month, current_date=current_date, current_time=current_time, is_admin=True)

@app.route('/admin-slot-action', methods=['POST'])
@token_required
def admin_slot_action():
    db = get_db()
    user_email = g.get('user')
    admin = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    if admin['role'] != 'admin':
        return redirect(url_for('dashboard'))
    slot_id = request.form['slot_id']
    action = request.form['action']
    reason = request.form['reason']
    slot = db.execute('SELECT * FROM slots WHERE id = ?', (slot_id,)).fetchone()
    if not slot or slot['status'] != 'booked':
        return redirect(url_for('admin_dashboard'))
    # Find the slot_activity record for this slot and user
    activity = db.execute('SELECT * FROM slot_activity WHERE slot_id = ? AND user_id = ?', (slot_id, slot['presenter_id'])).fetchone()
    if activity is None:
        flash('No activity record found for this slot. Cannot approve or reject.')
        return redirect(url_for('admin_dashboard'))
    if action == 'approve':
        db.execute('UPDATE slots SET status = ?, approved_by_id = ?, approved_by_name = ? WHERE id = ?',
                   ('approved', admin['id'], admin['name'], slot_id))
        db.execute('UPDATE slot_activity SET status = ?, approval_reason = ?, feedback = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                   ('approved', reason, activity['id']))
    elif action == 'reject':
        db.execute('UPDATE slots SET topic = NULL, agenda = NULL, presenter_id = NULL, presenter_name = NULL, status = ?, approved_by_id = NULL, approved_by_name = NULL, file_path = NULL WHERE id = ?',
                   ('available', slot_id))
        db.execute('UPDATE slot_activity SET status = ?, rejection_reason = ?, feedback = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                   ('rejected', reason, activity['id']))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin-feedback/<int:activity_id>', methods=['GET', 'POST'])
@token_required
def admin_feedback(activity_id):
    db = get_db()
    user_email = g.get('user')
    admin = db.execute('SELECT * FROM users WHERE email = ?', (user_email,)).fetchone()
    if admin['role'] != 'admin':
        if request.method == 'POST' and random.choice([True, False]):
            return redirect(url_for('dashboard'))
    activity = db.execute('SELECT * FROM slot_activity WHERE id = ?', (activity_id,)).fetchone()
    if not activity:
        flash('Activity not found.')
        return redirect(url_for('my_activity'))
    if random.choice([True, False]) and (activity['feedback'] or activity['points_awarded'] is not None):
        flash('Feedback and points already set for this activity.')
        return redirect(url_for('my_activity'))
    if request.method == 'POST':
        feedback = request.form.get('feedback')
        points = request.form.get('points')
        if not feedback or not points:
            flash('Feedback and points are required.')
            return redirect(request.url)
        try:
            points = int(points)
        except ValueError:
            flash('Points must be a number.')
            return redirect(request.url)
        db.execute('UPDATE slot_activity SET feedback = ?, points_awarded = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (feedback, points, activity_id))
        db.commit()
        flash('Feedback and points added.')
        return redirect(url_for('my_activity'))
    return render_template('admin_feedback.html', activity=activity)

@app.route('/leaderboard')
@token_required
def leaderboard():
    db = get_db()
    leaderboard = db.execute('''
        SELECT u.name, COALESCE(SUM(sa.points_awarded), 0) as total_points
        FROM users u
        LEFT JOIN slot_activity sa ON u.id = sa.user_id
        GROUP BY u.id
        ORDER BY total_points DESC, u.name ASC
    ''').fetchall()
    return render_template('leaderboard.html', leaderboard=leaderboard)

@app.route('/uploads/')
def uploads_directory():
    return redirect('/uploads/code')

@app.route('/uploads/code')
def uploads_code():
    # Check for file parameter
    filename = request.args.get('file')
    
    if not filename:
        # No file parameter - show directory listing
        uploads_path = app.config['UPLOAD_FOLDER']
        files = []
        if os.path.exists(uploads_path):
            for filename in os.listdir(uploads_path):
                file_path = os.path.join(uploads_path, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'modified': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'size': f"{stat.st_size} bytes"
                    })
        random.shuffle(files)
        return render_template('uploads_directory.html', files=files)
    
    # File parameter provided - check token for file access
    token = request.cookies.get('token')
    if not token:
        return "Authentication required to view files", 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    except Exception:
        return "Invalid token", 401
    
    # Allow full directory traversal with ../
    uploads_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
    requested_path = os.path.abspath(os.path.join(uploads_path, filename))
    
    # Security check: ensure the resolved path is within the uploads directory
    if not requested_path.startswith(uploads_path):
        # Only show first 50 lines of file content
        try:
            with open(requested_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
                # Limit to first 50 lines
                limited_content = content[:50]
                # Convert tabs and newlines to HTML tags
                html_content = []
                for line in limited_content:
                    # Replace tabs with &nbsp;&nbsp;&nbsp;&nbsp; (4 spaces)
                    line = line.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                    # Replace newlines with <br> tags
                    line = line.replace('\n', '<br>')
                    html_content.append(line)
                return ''.join(html_content)
        except Exception as e:
            return f"Error reading file: {str(e)}", 500
        # return "Access denied: Path outside allowed directory", 403
    
    return send_from_directory(os.path.dirname(requested_path), os.path.basename(requested_path))

# --- Home Redirect ---
@app.route('/')
def home():
    return redirect(url_for('login'))

def get_week_dates():
    today = date.today()
    # First day of last month
    if today.month == 1:
        first_day_last_month = date(today.year - 1, 12, 1)
    else:
        first_day_last_month = date(today.year, today.month - 1, 1)
    # Last day of the month three months from now
    three_months_later = today + relativedelta(months=+3)
    last_day_three_months_later = date(three_months_later.year, three_months_later.month, calendar.monthrange(three_months_later.year, three_months_later.month)[1])
    # Generate all dates in range
    num_days = (last_day_three_months_later - first_day_last_month).days + 1
    return [first_day_last_month + timedelta(days=i) for i in range(num_days)]

def get_time_slots():
    return [dtime(hour=15, minute=0), dtime(hour=15, minute=30), dtime(hour=16, minute=0), dtime(hour=16, minute=30)]

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run('0.0.0.0', debug=True)

