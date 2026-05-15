import sqlite3
from flask import g, current_app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_sqlite(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_sqlite():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            bio TEXT,
            avatar TEXT,
            preferences TEXT,
            email_verified INTEGER NOT NULL DEFAULT 0,
            points INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    # Older deployments predate the profile fields; back-fill silently.
    for column, ddl in (
        ("bio", "ALTER TABLE users ADD COLUMN bio TEXT"),
        ("avatar", "ALTER TABLE users ADD COLUMN avatar TEXT"),
        ("preferences", "ALTER TABLE users ADD COLUMN preferences TEXT"),
        ("email_verified", "ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0"),
        ("points", "ALTER TABLE users ADD COLUMN points INTEGER NOT NULL DEFAULT 0"),
        ("created_at", "ALTER TABLE users ADD COLUMN created_at TEXT"),
    ):
        try:
            db.execute(ddl)
        except Exception:
            pass
    db.execute(
        """CREATE TABLE IF NOT EXISTS slots (
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
        )"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS slot_activity (
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
        )"""
    )
    db.commit()

    db.execute(
        "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        ("Admin", "admin@example.com", "admin123", "admin"),
    )
    db.execute(
        "INSERT OR IGNORE INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        ("User", "user@example.com", "password", "user"),
    )
    db.commit()
