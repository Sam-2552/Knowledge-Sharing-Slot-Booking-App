import os
import urllib.parse
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    abort,
    current_app,
    g,
)
import yaml
from werkzeug.utils import secure_filename

from ..db import get_db
from ..auth.decorators import token_required
from .preferences import load_preferences, dump_preferences, deep_merge

bp = Blueprint("profile", __name__)

ASSIGNABLE_VIA_API = (
    "name",
    "bio",
    "avatar",
    "email_verified",
    "points",
    "role",
    "preferences",
)

# Browser preview tab is whitelisted, the rest are blocked by content-type later.
ALLOWED_AVATAR_MIME = {"image/png", "image/jpeg", "image/gif", "image/svg+xml"}


def _current_user(db):
    return db.execute("SELECT * FROM users WHERE email = ?", (g.user,)).fetchone()


@bp.route("/profile", methods=["GET", "POST"])
@token_required
def profile():
    db = get_db()
    user = _current_user(db)
    if request.method == "POST":
        name = request.form.get("name", user["name"]).strip()
        bio = request.form.get("bio", "").strip()
        db.execute(
            "UPDATE users SET name = ?, bio = ? WHERE id = ?",
            (name, bio, user["id"]),
        )
        db.commit()
        return redirect(url_for("profile.profile"))
    prefs = load_preferences(user["preferences"])
    return render_template("profile/profile.html", user=user, preferences=prefs)


@bp.route("/profile/avatar", methods=["POST"])
@token_required
def upload_avatar():
    db = get_db()
    user = _current_user(db)
    if "avatar" not in request.files or not request.files["avatar"].filename:
        return redirect(url_for("profile.profile"))
    f = request.files["avatar"]
    if (f.mimetype or "").lower() not in ALLOWED_AVATAR_MIME:
        return ("Unsupported image type", 400)
    avatar_dir = os.path.join(current_app.config["UPLOAD_DIR"], "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    filename = secure_filename(f.filename) or "avatar"
    # Keep the original filename so users recognise their upload in the picker.
    destination = os.path.join(avatar_dir, f"{user['id']}_{filename}")
    f.save(destination)
    rel = os.path.relpath(destination, current_app.config["UPLOAD_DIR"])
    db.execute("UPDATE users SET avatar = ? WHERE id = ?", (rel, user["id"]))
    db.commit()
    return redirect(url_for("profile.profile"))


@bp.route("/profile/avatar/<path:filename>")
def serve_avatar(filename):
    # Support upload paths with spaces / unicode coming from older clients.
    decoded = urllib.parse.unquote(filename)
    base = os.path.join(current_app.config["UPLOAD_DIR"], "avatars")
    target = os.path.join(base, decoded)
    if not os.path.isfile(target):
        abort(404)
    return send_file(target)


@bp.route("/api/profile", methods=["GET", "PATCH"])
@token_required
def api_profile():
    db = get_db()
    user = _current_user(db)
    if request.method == "GET":
        return jsonify(
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "bio": user["bio"],
                "avatar": user["avatar"],
                "points": user["points"],
                "email_verified": bool(user["email_verified"]),
            }
        )

    payload = request.get_json(silent=True) or {}
    fields, values = [], []
    for key, value in payload.items():
        if key in ASSIGNABLE_VIA_API:
            fields.append(f"{key} = ?")
            if key == "preferences" and not isinstance(value, str):
                value = dump_preferences(value)
            values.append(value)
    if fields:
        values.append(user["id"])
        db.execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values
        )
        db.commit()
    return jsonify({"status": "ok"})


@bp.route("/api/profile/preferences", methods=["POST"])
@token_required
def patch_preferences():
    db = get_db()
    user = _current_user(db)
    updates = request.get_json(silent=True) or {}
    prefs = load_preferences(user["preferences"])
    deep_merge(prefs, updates)
    db.execute(
        "UPDATE users SET preferences = ? WHERE id = ?",
        (dump_preferences(prefs), user["id"]),
    )
    db.commit()
    return jsonify({"preferences": prefs})


@bp.route("/profile/preferences/import", methods=["POST"])
@token_required
def import_preferences():
    db = get_db()
    user = _current_user(db)
    f = request.files.get("preferences")
    if not f or not f.filename:
        return redirect(url_for("profile.profile"))
    try:
        # The export feature emits a YAML bundle with custom tags for date/timezone.
        bundle = yaml.load(f.read(), Loader=yaml.Loader)
    except Exception as e:
        return (f"Could not parse preferences bundle: {e}", 400)
    if isinstance(bundle, dict):
        db.execute(
            "UPDATE users SET preferences = ? WHERE id = ?",
            (dump_preferences(bundle), user["id"]),
        )
        db.commit()
    return redirect(url_for("profile.profile"))
