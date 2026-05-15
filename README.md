# Knowledge Sharing Portal

Internal scheduling tool used by engineering teams to run weekly knowledge-sharing sessions. Engineers reserve a 30-minute slot, attach materials, and receive feedback and points from session leads. The leaderboard surfaces top contributors each quarter.

## Features

- Single sign-on via corporate IdP (OIDC) with optional username/password fallback
- Magic-link login for occasional external presenters
- Weekly slot calendar with availability tracking
- File attachments and presentation links on each booking
- Admin approval workflow with structured feedback and points
- Quarterly leaderboard and personal activity history
- Colleague directory backed by corporate LDAP
- Comment threads on past sessions for follow-up Q&A
- Bulk schedule import for off-sites and hack-weeks (XML)
- CSV export for retros

## Tech Stack

- Python 3.11 / Flask 3
- Gunicorn (WSGI) behind nginx
- SQLite for core records; MongoDB for comments and notifications
- Redis for sessions, cache and short-lived tokens
- OpenLDAP for the corporate directory
- dex as the development OIDC provider
- MailHog as the development SMTP catcher

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up -d --build
```

The app will be available at <http://localhost:5000>.
MailHog UI for outgoing mail is at <http://localhost:8025>.

The first start downloads a handful of base images and seeds the LDAP and dex containers — give it about 30 seconds before the login page is ready.

## Default accounts

For local development the database is seeded with two convenience accounts:

| Email | Password | Role |
|---|---|---|
| admin@example.com | admin123 | admin |
| user@example.com | password | user |

Replace these before any non-development deployment.

## Local development without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python wsgi.py
```

External services (MongoDB, LDAP, dex, MailHog) are only required for the features that depend on them; the core slot booking and admin flows run against SQLite alone.

## Project layout

```
app/                 Flask application package
  auth/              Authentication, signup, password reset
  slots/             Slot booking, dashboard, leaderboard, my-activity
  admin/             Admin dashboard, slot approval, feedback
  uploads/           Uploaded file browser and download
  internal/          Internal reporting endpoints used by ops
  templates/         Jinja templates organised per blueprint
  static/            Static assets
docker/              Service-specific configs (LDAP, dex, …)
uploads/             Runtime upload directory (bind-mounted in dev)
instance/            SQLite database directory
wsgi.py              Gunicorn entry point
```

## License

Internal use only.
