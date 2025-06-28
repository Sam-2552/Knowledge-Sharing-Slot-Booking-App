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
