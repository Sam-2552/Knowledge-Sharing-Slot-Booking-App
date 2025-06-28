# Knowledge Sharing Slot Booking App

A Flask-based web application for managing knowledge sharing sessions with user authentication, slot booking, admin approval system, and various security vulnerabilities for educational purposes.

## 🚨 **SECURITY WARNING**

This application contains **intentional security vulnerabilities** for educational and testing purposes. **DO NOT deploy this in production environments** or use it with real user data.

## Features

### Core Functionality
- **User Authentication**: Login/signup with JWT tokens
- **Slot Booking**: Book knowledge sharing slots with topics, agendas, and file uploads
- **Admin Panel**: Approve/reject bookings with feedback and points
- **Activity Tracking**: View booking history and status
- **Leaderboard**: User rankings based on points
- **File Management**: Upload and view files
- **Week Navigation**: Navigate through different weeks

### Security Vulnerabilities (Intentional)
- **Reflected XSS**: In forgot password page via email parameter
- **Stored XSS**: In admin approval/rejection reasons and feedback
- **Open Redirect**: In slot booking links
- **IDOR**: Book slots on behalf of other users
- **Directory Traversal**: Access files outside uploads directory
- **CSRF**: Missing CSRF protection in admin feedback
- **Weak Authentication**: No password complexity requirements

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Setup and Deployment

### 🚀 Quick Setup Guide

#### **Step 1: Download/Clone the Project**
```bash
# If you have the files already, skip this step
git clone <repository-url>
cd Knowledge-Sharing-Slot-Booking-App
```

#### **Step 2: Create Virtual Environment**
```bash
# Create a virtual environment
python -m venv venv

# Activate it (choose your OS):
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

#### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **Step 4: Run the Application**
```bash
python app.py
```

#### **Step 5: Access the Application**
- Open your web browser
- Go to: `http://localhost:5000`
- For external access: `http://your-ip:5000`

### 🎯 Quick Start Usage

1. **Login** with admin credentials
2. **Book a slot** by filling in topic, agenda, and optional files/links
3. **Switch to admin view** to approve/reject bookings
4. **Add feedback and points** to approved sessions
5. **View activity** and leaderboard

### 🐛 Troubleshooting

#### **Port Already in Use**
```bash
# Kill process on port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Kill process on port 5000 (macOS/Linux)
lsof -ti:5000 | xargs kill -9
```

#### **Permission Errors**
```bash
# Make sure you have write permissions
chmod +x app.py
```

#### **Database Issues**
```bash
# Delete the database file to reset
rm users.db
# Then run the app again - it will recreate the database
```

#### **Virtual Environment Issues**
```bash
# If activation doesn't work, try:
# Windows:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate
```

### 🔧 Development Setup

#### **For External Access**
The app is configured to run on `0.0.0.0:5000` so you can access it from other devices on your network.

#### **Debug Mode**
The app runs in debug mode by default, so you'll see detailed error messages and the Flask debugger.

#### **File Uploads**
- Files are stored in the `uploads/` directory
- Access them via `/uploads/` or `/uploads/code?file=filename`

### 🎯 Security Testing Quick Start

1. **Test Reflected XSS**: Go to forgot password page and enter `<script>alert('XSS')</script>`
2. **Test Stored XSS**: As admin, approve a slot with `<script>alert('XSS')</script>` in reason
3. **Test Open Redirect**: Book a slot with `javascript:alert('XSS')` in link field
4. **Test IDOR**: Modify user_id in booking form via browser dev tools
5. **Test Directory Traversal**: Access `/uploads/code?file=../../../etc/passwd`

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Knowledge-Sharing-Slot-Booking-App
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - For external access: `http://your-ip:5000`

## Default Users

The application comes with default users:

- **Admin User**:
  - Email: `admin@example.com`
  - Password: `admin123`
  - Role: Admin

- **Regular User**:
  - Email: `user@example.com`
  - Password: `password`
  - Role: User

## Usage

### For Regular Users
1. **Login** with your credentials
2. **Book Slots**: Select available time slots and fill in topic, agenda, and optional files/links
3. **View Activity**: Check your booking status and admin feedback
4. **Leaderboard**: See your ranking among other users

### For Admins
1. **Login** with admin credentials
2. **Approve/Reject**: Review pending bookings and provide reasons
3. **Add Feedback**: Give feedback and award points to approved sessions
4. **View All Activity**: Monitor all user activities

## Security Vulnerabilities Details

### 1. Reflected XSS (Forgot Password)
- **Location**: `/forgot-password` page
- **Payload**: `<script>alert('XSS')</script>` in email field
- **Exploitation**: Enter XSS payload in email input or URL parameter

### 2. Stored XSS (Admin Feedback)
- **Location**: Admin approval/rejection reasons and feedback
- **Payload**: `<script>alert('Stored XSS')</script>`
- **Exploitation**: Admin enters XSS payload in reason/feedback fields

### 3. Open Redirect (Slot Links)
- **Location**: Slot booking links
- **Payload**: `javascript:alert('XSS')` or `https://evil.com`
- **Exploitation**: Enter malicious URL in link field during booking

### 4. IDOR (Slot Booking)
- **Location**: `/book-slot` endpoint
- **Exploitation**: Modify `user_id` parameter to book for other users
- **Method**: Browser dev tools or proxy interception

### 5. Directory Traversal (File Access)
- **Location**: `/uploads/code` endpoint
- **Payload**: `../../../etc/passwd`
- **Exploitation**: Access files outside uploads directory

### 6. CSRF (Admin Feedback)
- **Location**: Admin feedback form
- **Exploitation**: Create malicious form that submits feedback
- **Impact**: Admin actions without consent

## File Structure

```
Knowledge-Sharing-Slot-Booking-App/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── users.db              # SQLite database
├── static/
│   └── js/
│       └── password.js   # Password protection for uploads
├── templates/
│   ├── dashboard.html    # Main dashboard
│   ├── login.html        # Login page
│   ├── signup.html       # Signup page
│   ├── my_activity.html  # Activity tracking
│   ├── leaderboard.html  # User rankings
│   ├── admin_feedback.html # Admin feedback form
│   ├── forgot_password.html # Password reset
│   ├── reset_password.html  # Password reset form
│   └── uploads_directory.html # File listing
└── uploads/              # File upload directory
```

## Database Schema

### Users Table
- `id`: Primary key
- `name`: User's full name
- `email`: Unique email address
- `password`: Plain text password (vulnerable)
- `role`: User role (user/admin)

### Slots Table
- `id`: Primary key
- `date`: Slot date
- `time`: Slot time
- `topic`: Presentation topic
- `agenda`: Presentation agenda
- `presenter_id`: User ID of presenter
- `presenter_name`: Name of presenter
- `status`: Slot status (available/booked/approved)
- `approved_by_id`: Admin who approved
- `approved_by_name`: Name of approving admin
- `file_path`: Path to uploaded file
- `link`: External link

### Slot Activity Table
- `id`: Primary key
- `slot_id`: Reference to slot
- `user_id`: User who booked
- `status`: Activity status
- `approval_reason`: Admin approval reason (XSS vulnerable)
- `rejection_reason`: Admin rejection reason (XSS vulnerable)
- `feedback`: Admin feedback (XSS vulnerable)
- `points_awarded`: Points given by admin
- `topic`: Topic from booking
- `agenda`: Agenda from booking
- `file_path`: File path from booking
- `link`: Link from booking
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## API Endpoints

- `GET /` - Redirect to login
- `GET/POST /login` - User authentication
- `GET /logout` - User logout
- `GET/POST /signup` - User registration
- `GET /dashboard` - Main dashboard
- `GET /admin-dashboard` - Admin dashboard
- `POST /book-slot` - Book a slot (IDOR vulnerable)
- `POST /admin-slot-action` - Approve/reject slots
- `GET/POST /admin-feedback/<id>` - Add feedback (CSRF vulnerable)
- `GET /my-activity` - View activity history
- `GET /leaderboard` - User rankings
- `GET/POST /forgot-password` - Password reset (XSS vulnerable)
- `GET/POST /reset-password/<token>` - Password reset form
- `GET /uploads/` - File directory listing
- `GET /uploads/code` - File access (Directory traversal vulnerable)

## Security Testing

This application is designed for:
- **Security Research**: Understanding common web vulnerabilities
- **Penetration Testing**: Practicing security assessment techniques
- **Educational Purposes**: Learning about web application security
- **CTF Challenges**: Capture The Flag competitions

## Contributing

This is an educational project. Feel free to:
- Report bugs in the core functionality
- Suggest improvements to the vulnerabilities
- Add new security vulnerabilities for learning
- Improve documentation

## License

This project is for educational purposes only. Use responsibly and ethically.

## Disclaimer

The authors are not responsible for any misuse of this application. This software is provided "as is" without warranty of any kind. Users are responsible for ensuring they have proper authorization before testing security vulnerabilities. 