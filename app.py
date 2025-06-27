from flask import Flask, render_template, request, redirect, url_for, make_response, g, flash
import sqlite3
import jwt
import datetime
from functools import wraps
import urllib.parse
from datetime import timedelta, date, time as dtime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['DATABASE'] = 'users.db'

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
        presenter TEXT,
        status TEXT NOT NULL DEFAULT 'available',
        approved_by TEXT
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
            resp.set_cookie('token', token, httponly=True, samesite='Lax')
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
    week_dates = get_week_dates()
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
    return render_template('dashboard.html', user=user, slots_lookup=slots_lookup, week_dates=week_dates, time_slots=time_slots, booked_dates=booked_dates)

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
        db = get_db()
        try:
            db.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)', (name, email, password, 'user'))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = 'Email already registered.'
    return render_template('signup.html', error=error)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    message = None
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
            with open('logs.txt', 'a') as log_file:
                log_file.write(f"Password reset link for {email}: {reset_url}\n")
            message = 'A password reset link has been sent to your email (simulated).'
        else:
            message = 'If the email exists, a reset link will be sent.'
    return render_template('forgot_password.html', message=message)

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
    # Check if slot is available
    slot = db.execute('SELECT * FROM slots WHERE id = ?', (slot_id,)).fetchone()
    if slot and slot['status'] == 'available':
        db.execute('UPDATE slots SET topic = ?, presenter = ?, status = ? WHERE id = ?', (topic, user['name'], 'booked', slot_id))
        db.commit()
        return redirect(url_for('dashboard'))
    else:
        flash('Slot is no longer available.')
        return redirect(url_for('dashboard'))

# --- Home Redirect ---
@app.route('/')
def home():
    return redirect(url_for('login'))

def get_week_dates():
    today = date.today()
    start = today - timedelta(days=today.weekday())  # Monday
    return [start + timedelta(days=i) for i in range(5)]  # Mon-Fri

def get_time_slots():
    return [dtime(hour=15, minute=0), dtime(hour=15, minute=30), dtime(hour=16, minute=0), dtime(hour=16, minute=30)]

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
