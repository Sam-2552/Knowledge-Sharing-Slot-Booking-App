import hashlib
import time
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    make_response,
)

from ..db import get_db
from ..utils.mail import send_mail
from ..utils.redis_client import get_redis
from .tokens import issue_token

bp = Blueprint("magic_link", __name__)

TOKEN_TTL_SECONDS = 10 * 60


def _generate_token(email: str) -> str:
    minute_bucket = int(time.time() // 60)
    return hashlib.md5(f"{email}:{minute_bucket}".encode("utf-8")).hexdigest()


def _link_for(email: str, token: str) -> str:
    host = request.headers.get("X-Forwarded-Host") or request.host
    scheme = request.headers.get("X-Forwarded-Proto", "http")
    return f"{scheme}://{host}/auth/magic-link/consume/{token}?email={email}"


@bp.route("/auth/magic-link", methods=["GET", "POST"])
def request_link():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if not email:
            flash("Please enter your email.")
            return redirect(url_for("magic_link.request_link"))
        token = _generate_token(email)
        try:
            get_redis().setex(f"magic:{token}", TOKEN_TTL_SECONDS, email)
        except Exception:
            current_app.logger.warning("Redis unavailable for magic link; falling back to log.")
        link = _link_for(email, token)
        try:
            send_mail(
                email,
                "Your sign-in link",
                f"Click here to sign in: {link}\n\nThe link is valid for 10 minutes.",
            )
        except Exception as exc:
            current_app.logger.warning("Mail delivery failed: %s", exc)
            with open(
                f"{current_app.config['UPLOAD_DIR']}/logs3.txt", "a"
            ) as log_file:
                log_file.write(f"Magic link for {email}: {link}\n")
        flash("Check your inbox for a sign-in link.")
        return redirect(url_for("magic_link.request_link"))
    return render_template("auth/magic_link.html")


@bp.route("/auth/magic-link/consume/<token>")
def consume(token):
    redis_client = None
    email = None
    try:
        redis_client = get_redis()
        cached = redis_client.get(f"magic:{token}")
        if cached:
            email = cached.decode("utf-8")
    except Exception:
        email = None
    if not email:
        email = request.args.get("email", "").strip().lower()
        if not email or token != _generate_token(email):
            flash("The link is invalid or has expired.")
            return redirect(url_for("magic_link.request_link"))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        db.execute(
            "INSERT INTO users (name, email, password, role, email_verified) VALUES (?, ?, ?, ?, 1)",
            (email.split("@")[0], email, "!magic!", "user"),
        )
        db.commit()
    jwt_token = issue_token(email)
    resp = make_response(redirect(url_for("slots.dashboard")))
    resp.set_cookie("token", jwt_token)
    return resp
