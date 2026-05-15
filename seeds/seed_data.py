"""Populate the SQLite DB with realistic demo data.

Idempotent: re-running won't duplicate rows. Run via:

    python -m seeds.seed_data
"""
import os
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta

NAMES = [
    "Alice Wang", "Bob Mendoza", "Charlie Brooks", "Diane Park", "Erin Tanaka",
    "Fiona Cruz", "George Schmidt", "Hannah Patel", "Ivan Petrov", "Julia Reyes",
    "Karthik Iyer", "Linda Okafor", "Mateo Rossi", "Nora Lindqvist", "Omar Aziz",
    "Priya Sharma", "Quinn Murphy", "Rashid Ahmed", "Sara Berg", "Tomás Silva",
]

TOPICS = [
    "Postgres lock anatomy",
    "Practical OpenTelemetry",
    "Kafka consumer rebalancing",
    "Building durable workflows with Temporal",
    "Why our build takes 14 minutes (and how we fix it)",
    "Front-end performance budgets that stick",
    "Designing for keyboard-only users",
    "Lessons from migrating to k8s",
    "Pragmatic feature flags",
    "When to write a custom Postgres extension",
    "Capacity planning for queues",
    "Patterns for idempotent webhooks",
    "Failure modes of the new auth flow",
    "What we learnt running a chaos game day",
    "Refactoring without tests",
]


def main(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    for name in NAMES:
        slug = name.lower().split()[0]
        email = f"{slug}@ksp.local"
        try:
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, "!seed!", "user"),
            )
        except sqlite3.IntegrityError:
            pass

    user_ids = [row[0] for row in cur.execute("SELECT id FROM users WHERE role = 'user'")]

    today = date.today()
    times = ["15:00", "15:30", "16:00", "16:30"]
    for delta_days in range(-30, 60):
        day = today + timedelta(days=delta_days)
        if day.weekday() >= 5:
            continue
        for t in times:
            iso = day.strftime("%Y-%m-%d")
            existing = cur.execute(
                "SELECT id FROM slots WHERE date = ? AND time = ?", (iso, t)
            ).fetchone()
            if existing:
                continue
            cur.execute(
                "INSERT INTO slots (date, time) VALUES (?, ?)", (iso, t)
            )

    slot_ids = [row[0] for row in cur.execute("SELECT id FROM slots WHERE status = 'available' ORDER BY RANDOM() LIMIT 30")]
    for sid in slot_ids:
        presenter = random.choice(user_ids)
        presenter_name = cur.execute("SELECT name FROM users WHERE id = ?", (presenter,)).fetchone()[0]
        topic = random.choice(TOPICS)
        agenda = "Brief overview, code walk-through, Q&A."
        cur.execute(
            "UPDATE slots SET topic = ?, agenda = ?, presenter_id = ?, presenter_name = ?, status = 'approved', approved_by_name = 'Admin', approved_by_id = 1 WHERE id = ?",
            (topic, agenda, presenter, presenter_name, sid),
        )
        cur.execute(
            "INSERT INTO slot_activity (slot_id, user_id, status, topic, agenda, feedback, points_awarded) VALUES (?, ?, 'approved', ?, ?, ?, ?)",
            (sid, presenter, topic, agenda, "Great session, clear walkthrough.", random.randint(3, 10)),
        )

    con.commit()
    con.close()
    print(f"Seeded {db_path}")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "DATABASE_PATH", "instance/users.db"
    )
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}; run the app once to create it.")
        sys.exit(1)
    main(db_path)
