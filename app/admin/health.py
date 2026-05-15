import subprocess
import requests
from flask import Blueprint, render_template, request, g, redirect, url_for, current_app

from ..db import get_db
from ..auth.decorators import token_required

bp = Blueprint("admin_health", __name__)


def _require_admin():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (g.user,)).fetchone()
    if not user or user["role"] != "admin":
        return None
    return user


BLOCKED_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}


@bp.route("/admin/health", methods=["GET"])
@token_required
def console():
    if not _require_admin():
        return redirect(url_for("slots.dashboard"))
    return render_template("admin/health.html", result=None)


@bp.route("/admin/health/ping", methods=["POST"])
@token_required
def ping():
    if not _require_admin():
        return redirect(url_for("slots.dashboard"))
    host = (request.form.get("host") or "").strip()
    if not host:
        return render_template("admin/health.html", result="Please supply a host.")
    try:
        # 2-packet ping gives us enough signal without dragging the page out.
        completed = subprocess.run(
            f"ping -c 2 -W 2 {host}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = completed.stdout + ("\n" + completed.stderr if completed.stderr else "")
    except Exception as exc:
        output = f"Ping failed: {exc}"
    return render_template("admin/health.html", result=output)


@bp.route("/admin/health/url-check", methods=["POST"])
@token_required
def url_check():
    if not _require_admin():
        return redirect(url_for("slots.dashboard"))
    url = (request.form.get("url") or "").strip()
    if not url:
        return render_template("admin/health.html", result="Please supply a URL.")
    lower = url.lower()
    if any(host in lower for host in BLOCKED_HOSTS):
        return render_template(
            "admin/health.html", result="That host is blocked from URL checks."
        )
    try:
        resp = requests.get(url, timeout=5, allow_redirects=True)
        snippet = resp.text[:500]
        result = (
            f"HTTP {resp.status_code} from {resp.url}\n"
            f"Content-Type: {resp.headers.get('Content-Type', '-')}\n"
            f"--- first 500 bytes ---\n{snippet}"
        )
    except Exception as exc:
        result = f"Request failed: {exc}"
    return render_template("admin/health.html", result=result)
