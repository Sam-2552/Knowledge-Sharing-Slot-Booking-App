from flask import Blueprint, request, jsonify, g, abort

from ..db import get_db
from ..auth.decorators import token_required
from . import store

bp = Blueprint("comments", __name__)


def _current_user(db):
    return db.execute("SELECT * FROM users WHERE email = ?", (g.user,)).fetchone()


@bp.route("/api/comments/<int:slot_id>", methods=["GET", "POST"])
@token_required
def comments(slot_id):
    db = get_db()
    user = _current_user(db)
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        body = (payload.get("body") or "").strip()
        if not body:
            return jsonify({"error": "body required"}), 400
        try:
            doc = store.add_comment(slot_id, user["email"], user["name"], body)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 503
        return jsonify({"comment": doc}), 201
    try:
        comments = store.list_for_slot(slot_id)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"comments": comments})


@bp.route("/api/comments/search", methods=["POST"])
@token_required
def search_comments():
    payload = request.get_json(silent=True) or {}
    filter_doc = payload.get("filter", {})
    if not isinstance(filter_doc, dict):
        return jsonify({"error": "filter must be an object"}), 400
    try:
        results = store.search(filter_doc)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 503
    return jsonify({"comments": results})
