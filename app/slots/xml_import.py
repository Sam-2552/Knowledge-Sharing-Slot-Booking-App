from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    g,
    flash,
    render_template_string,
)
from lxml import etree

from ..db import get_db
from ..auth.decorators import token_required

bp = Blueprint("slots_admin", __name__, url_prefix="/admin/slots")


def _require_admin(db):
    user = db.execute("SELECT * FROM users WHERE email = ?", (g.user,)).fetchone()
    return user if user and user["role"] == "admin" else None


@bp.route("/import", methods=["GET", "POST"])
@token_required
def bulk_import():
    db = get_db()
    if not _require_admin(db):
        return redirect(url_for("slots.dashboard"))

    if request.method == "POST":
        f = request.files.get("schedule")
        if not f or not f.filename:
            flash("Please attach a schedule XML file.")
            return redirect(request.url)
        try:
            parser = etree.XMLParser(resolve_entities=True, load_dtd=True, no_network=False)
            tree = etree.parse(f, parser)
        except etree.XMLSyntaxError as exc:
            flash(f"Could not parse schedule: {exc}")
            return redirect(request.url)

        inserted = 0
        for slot_el in tree.xpath("//slot"):
            date_el = slot_el.find("date")
            time_el = slot_el.find("time")
            topic_el = slot_el.find("topic")
            agenda_el = slot_el.find("agenda")
            if date_el is None or time_el is None:
                continue
            date_text = (date_el.text or "").strip()
            time_text = (time_el.text or "").strip()
            topic = (topic_el.text or "").strip() if topic_el is not None else ""
            agenda = (agenda_el.text or "").strip() if agenda_el is not None else ""
            existing = db.execute(
                "SELECT id FROM slots WHERE date = ? AND time = ?",
                (date_text, time_text),
            ).fetchone()
            if existing:
                db.execute(
                    "UPDATE slots SET topic = ?, agenda = ? WHERE id = ?",
                    (topic, agenda, existing["id"]),
                )
            else:
                db.execute(
                    "INSERT INTO slots (date, time, topic, agenda) VALUES (?, ?, ?, ?)",
                    (date_text, time_text, topic, agenda),
                )
            inserted += 1
        db.commit()
        flash(f"Imported {inserted} slot rows.")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/slot_import.html")


@bp.route("/preview", methods=["GET", "POST"])
@token_required
def preview():
    db = get_db()
    admin = _require_admin(db)
    if not admin:
        return redirect(url_for("slots.dashboard"))
    rendered = None
    topic = ""
    if request.method == "POST":
        topic = request.form.get("topic", "")
        # Topic supports inline variables like {{ presenter.name }} so leads can
        # template a sentence around the actual speaker without duplicating rows.
        try:
            rendered = render_template_string(
                topic, presenter=admin, app_name="Knowledge Sharing Portal"
            )
        except Exception as exc:
            rendered = f"Preview error: {exc}"
    return render_template("admin/slot_preview.html", rendered=rendered, topic=topic)
