import csv
import io
from flask import Blueprint, Response, redirect, url_for, g

from ..db import get_db
from ..auth.decorators import token_required

bp = Blueprint("admin_export", __name__)


@bp.route("/admin/export.csv")
@token_required
def export_csv():
    db = get_db()
    admin = db.execute(
        "SELECT * FROM users WHERE email = ?", (g.user,)
    ).fetchone()
    if not admin or admin["role"] != "admin":
        return redirect(url_for("slots.dashboard"))

    rows = db.execute(
        """
        SELECT u.name as presenter, sa.created_at, sa.status, sa.topic, sa.agenda,
               sa.feedback, sa.points_awarded, sa.approval_reason, sa.rejection_reason
        FROM slot_activity sa
        LEFT JOIN users u ON sa.user_id = u.id
        ORDER BY sa.created_at DESC
        """
    ).fetchall()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "Presenter",
            "Created At",
            "Status",
            "Topic",
            "Agenda",
            "Feedback",
            "Points",
            "Approval Reason",
            "Rejection Reason",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r["presenter"] or "",
                r["created_at"],
                r["status"],
                r["topic"] or "",
                r["agenda"] or "",
                r["feedback"] or "",
                r["points_awarded"] if r["points_awarded"] is not None else "",
                r["approval_reason"] or "",
                r["rejection_reason"] or "",
            ]
        )

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=slot-activity.csv"},
    )
