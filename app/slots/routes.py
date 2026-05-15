import os
import datetime
from datetime import date, timedelta
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    g,
)
from werkzeug.utils import secure_filename

from ..db import get_db
from ..auth.decorators import token_required
from .calendar import get_week_dates, get_time_slots

bp = Blueprint("slots", __name__)


def _build_week_view(db, week_dates, time_slots):
    for day in week_dates:
        for slot_time in time_slots:
            slot_date = day.strftime("%Y-%m-%d")
            slot_time_str = slot_time.strftime("%H:%M")
            exists = db.execute(
                "SELECT 1 FROM slots WHERE date = ? AND time = ?",
                (slot_date, slot_time_str),
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO slots (date, time) VALUES (?, ?)",
                    (slot_date, slot_time_str),
                )
    db.commit()
    slots = db.execute(
        "SELECT * FROM slots WHERE date IN ({}) ORDER BY date, time".format(
            ",".join(["?"] * len(week_dates))
        ),
        [d.strftime("%Y-%m-%d") for d in week_dates],
    ).fetchall()
    slots_lookup = {}
    booked_dates = set()
    for slot in slots:
        slots_lookup[(slot["date"], slot["time"])] = slot
        if slot["status"] in ("booked", "approved"):
            booked_dates.add(slot["date"])
    return slots_lookup, booked_dates


def _week_navigation():
    all_dates = get_week_dates()
    all_weekdays = [d for d in all_dates if d.weekday() < 5]
    weeks = [all_weekdays[i : i + 5] for i in range(0, len(all_weekdays), 5)]
    today = date.today()
    current_week_index = 0
    for idx, week in enumerate(weeks):
        if today in week:
            current_week_index = idx
            break
    week_number = request.args.get("week")
    if week_number is not None:
        try:
            week_number = int(week_number)
        except ValueError:
            week_number = current_week_index
        if week_number < 0 or week_number >= len(weeks):
            week_number = current_week_index
    else:
        week_number = current_week_index
    return weeks, week_number


@bp.route("/dashboard")
@token_required
def dashboard():
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    if user and user["role"] == "admin":
        return redirect(url_for("admin.dashboard"))
    weeks, week_number = _week_navigation()
    week_dates = weeks[week_number]
    time_slots = get_time_slots()
    slots_lookup, booked_dates = _build_week_view(db, week_dates, time_slots)
    today = date.today()
    now = datetime.datetime.now()
    return render_template(
        "slots/dashboard.html",
        user=user,
        slots_lookup=slots_lookup,
        week_dates=week_dates,
        time_slots=time_slots,
        booked_dates=booked_dates,
        today_str=today.strftime("%Y-%m-%d"),
        now_str=now.strftime("%H:%M"),
        week_number=week_number,
        total_weeks=len(weeks),
        current_month=today.strftime("%B"),
        current_date=today.strftime("%d %b %Y"),
        current_time=now.strftime("%I:%M %p"),
    )


@bp.route("/book-slot", methods=["POST"])
@token_required
def book_slot():
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    slot_id = request.form["slot_id"]
    user_id = request.form.get("user_id", user["id"])
    topic = request.form["topic"]
    agenda = request.form.get("agenda")
    link = request.form.get("link")

    if link:
        import requests

        try:
            response = requests.head(link, timeout=5, allow_redirects=True)
            if response.status_code >= 400:
                flash("Invalid link provided. Please check the URL and try again.")
                return redirect(url_for("slots.dashboard"))
        except requests.RequestException:
            flash("Invalid link provided. Please check the URL and try again.")
            return redirect(url_for("slots.dashboard"))

    file_path = None
    if "file" in request.files and request.files["file"].filename:
        f = request.files["file"]
        filename = secure_filename(f.filename)
        file_path = os.path.join(current_app.config["UPLOAD_DIR"], filename)
        f.save(file_path)

    slot = db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()
    if slot and slot["status"] == "available":
        target_user = db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not target_user:
            flash("Invalid user ID provided.")
            return redirect(url_for("slots.dashboard"))
        db.execute(
            "UPDATE slots SET topic = ?, agenda = ?, presenter_id = ?, presenter_name = ?, status = ?, file_path = ?, link = ? WHERE id = ?",
            (
                topic,
                agenda,
                user_id,
                target_user["name"],
                "booked",
                file_path,
                link,
                slot_id,
            ),
        )
        db.execute(
            "INSERT INTO slot_activity (slot_id, user_id, status, topic, agenda, file_path, link) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (slot_id, user_id, "booked", topic, agenda, file_path, link),
        )
        db.commit()
        return redirect(url_for("slots.dashboard"))
    flash("Slot is no longer available.")
    return redirect(url_for("slots.dashboard"))


@bp.route("/my-activity")
@token_required
def my_activity():
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    is_admin = user["role"] == "admin"
    if is_admin:
        all_activities = db.execute(
            """
            SELECT sa.*, u.name as username FROM slot_activity sa
            JOIN users u ON sa.user_id = u.id
            ORDER BY sa.created_at DESC
            """
        ).fetchall()
    else:
        all_activities = db.execute(
            "SELECT * FROM slot_activity WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()

    def get_week_start(dt):
        return dt - timedelta(days=dt.weekday())

    activities_by_week = {}
    for a in all_activities:
        dt = datetime.datetime.strptime(a["created_at"][:10], "%Y-%m-%d")
        week_start = get_week_start(dt)
        activities_by_week.setdefault(week_start, []).append(a)
    sorted_weeks = sorted(activities_by_week.keys(), reverse=True)

    try:
        week_number = int(request.args.get("week", 0))
    except ValueError:
        week_number = 0
    if not sorted_weeks:
        week_dates, activities, total_weeks = [], [], 0
    else:
        if week_number < 0 or week_number >= len(sorted_weeks):
            week_number = 0
        week_dates = [
            sorted_weeks[week_number] + timedelta(days=i) for i in range(5)
        ]
        activities = activities_by_week.get(sorted_weeks[week_number], [])
        total_weeks = len(sorted_weeks)

    return render_template(
        "slots/my_activity.html",
        user=user,
        activities=activities,
        is_admin=is_admin,
        week_number=week_number,
        total_weeks=total_weeks,
        week_dates=week_dates,
    )


@bp.route("/slots/<int:slot_id>/edit", methods=["GET", "POST"])
@token_required
def edit_slot(slot_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (g.user,)).fetchone()
    slot = db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()
    if not slot:
        flash("Slot not found.")
        return redirect(url_for("slots.dashboard"))
    if request.method == "POST":
        topic = request.form.get("topic") or slot["topic"]
        agenda = request.form.get("agenda") or slot["agenda"]
        link = request.form.get("link") or slot["link"]
        db.execute(
            "UPDATE slots SET topic = ?, agenda = ?, link = ? WHERE id = ?",
            (topic, agenda, link, slot_id),
        )
        db.execute(
            "UPDATE slot_activity SET topic = ?, agenda = ?, link = ?, updated_at = CURRENT_TIMESTAMP WHERE slot_id = ? AND user_id = ?",
            (topic, agenda, link, slot_id, slot["presenter_id"]),
        )
        db.commit()
        flash("Slot updated.")
        return redirect(url_for("slots.dashboard"))
    return render_template("slots/edit.html", slot=slot, user=user)


@bp.route("/slots/<int:slot_id>/cancel", methods=["POST"])
@token_required
def cancel_slot(slot_id):
    db = get_db()
    slot = db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()
    if not slot:
        flash("Slot not found.")
        return redirect(url_for("slots.dashboard"))
    db.execute(
        "UPDATE slots SET topic = NULL, agenda = NULL, presenter_id = NULL, "
        "presenter_name = NULL, status = 'available', approved_by_id = NULL, "
        "approved_by_name = NULL, file_path = NULL, link = NULL WHERE id = ?",
        (slot_id,),
    )
    db.commit()
    flash("Booking cancelled.")
    return redirect(url_for("slots.dashboard"))


@bp.route("/leaderboard")
@token_required
def leaderboard():
    db = get_db()
    rows = db.execute(
        """
        SELECT u.name, COALESCE(SUM(sa.points_awarded), 0) as total_points
        FROM users u
        LEFT JOIN slot_activity sa ON u.id = sa.user_id
        GROUP BY u.id
        ORDER BY total_points DESC, u.name ASC
        """
    ).fetchall()
    return render_template("slots/leaderboard.html", leaderboard=rows)
