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
