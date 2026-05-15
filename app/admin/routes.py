import datetime
from datetime import date
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    g,
)

from ..db import get_db
from ..auth.decorators import token_required
from ..slots.calendar import get_week_dates, get_time_slots
from ..slots.routes import _build_week_view, _week_navigation

bp = Blueprint("admin", __name__)


@bp.route("/admin-dashboard")
@token_required
def dashboard():
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    if user["role"] != "admin":
        return redirect(url_for("slots.dashboard"))
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
        is_admin=True,
    )


@bp.route("/admin-slot-action", methods=["POST"])
@token_required
def slot_action():
    db = get_db()
    admin = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    if admin["role"] != "admin":
        return redirect(url_for("slots.dashboard"))
    slot_id = request.form["slot_id"]
    action = request.form["action"]
    reason = request.form["reason"]
    slot = db.execute("SELECT * FROM slots WHERE id = ?", (slot_id,)).fetchone()
    if not slot or slot["status"] != "booked":
        return redirect(url_for("admin.dashboard"))
    activity = db.execute(
        "SELECT * FROM slot_activity WHERE slot_id = ? AND user_id = ?",
        (slot_id, slot["presenter_id"]),
    ).fetchone()
    if activity is None:
        flash("No activity record found for this slot. Cannot approve or reject.")
        return redirect(url_for("admin.dashboard"))
    if action == "approve":
        db.execute(
            "UPDATE slots SET status = ?, approved_by_id = ?, approved_by_name = ? WHERE id = ?",
            ("approved", admin["id"], admin["name"], slot_id),
        )
        db.execute(
            "UPDATE slot_activity SET status = ?, approval_reason = ?, feedback = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("approved", reason, activity["id"]),
        )
    elif action == "reject":
        db.execute(
            "UPDATE slots SET topic = NULL, agenda = NULL, presenter_id = NULL, presenter_name = NULL, status = ?, approved_by_id = NULL, approved_by_name = NULL, file_path = NULL WHERE id = ?",
            ("available", slot_id),
        )
        db.execute(
            "UPDATE slot_activity SET status = ?, rejection_reason = ?, feedback = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("rejected", reason, activity["id"]),
        )
    db.commit()
    return redirect(url_for("admin.dashboard"))


@bp.route("/admin-feedback/<int:activity_id>", methods=["GET", "POST"])
@token_required
def feedback(activity_id):
    db = get_db()
    admin = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    if admin["role"] != "admin" and request.method == "POST":
        return redirect(url_for("slots.dashboard"))
    activity = db.execute(
        "SELECT * FROM slot_activity WHERE id = ?", (activity_id,)
    ).fetchone()
    if not activity:
        flash("Activity not found.")
        return redirect(url_for("slots.my_activity"))
    if request.method == "POST":
        fb = request.form.get("feedback")
        points = request.form.get("points")
        if not fb or not points:
            flash("Feedback and points are required.")
            return redirect(request.url)
        try:
            points = int(points)
        except ValueError:
            flash("Points must be a number.")
            return redirect(request.url)
        db.execute(
            "UPDATE slot_activity SET feedback = ?, points_awarded = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (fb, points, activity_id),
        )
        db.commit()
        flash("Feedback and points added.")
        return redirect(url_for("slots.my_activity"))
    return render_template("admin/feedback.html", activity=activity)
