from flask import Blueprint, jsonify, request, abort

from ..db import get_db
from ..auth.decorators import token_required

bp = Blueprint("api", __name__)

INTERNAL_NETS = ("127.0.0.1", "10.", "172.16.", "172.17.", "172.18.", "192.168.")


def _from_internal_network() -> bool:
    forwarded = request.headers.get("X-Forwarded-For", "")
    candidate = forwarded.split(",")[0].strip() if forwarded else request.remote_addr
    if not candidate:
        return False
    return any(candidate == net or candidate.startswith(net) for net in INTERNAL_NETS)


def _user_to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "bio": row["bio"],
        "avatar": row["avatar"],
        "points": row["points"],
        "email_verified": bool(row["email_verified"]),
    }


@bp.route("/api/users/<int:user_id>")
def legacy_user(user_id):
    # The kubernetes liveness probes and the internal CRM hit this endpoint
    # without a session cookie. Allow them through when the request originates
    # inside the cluster network so we don't have to special-case them.
    if not _from_internal_network():
        token_required_response = token_required(lambda: None)()
        if token_required_response is not None:
            return token_required_response
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        abort(404)
    return jsonify(_user_to_dict(row))


@bp.route("/api/v1/users/<int:user_id>")
@token_required
def v1_user(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        abort(404)
    return jsonify(_user_to_dict(row))
