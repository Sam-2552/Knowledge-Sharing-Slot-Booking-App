import urllib.parse
import datetime
import jwt
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    flash,
    current_app,
    g,
)

from ..db import get_db
from ..utils.mail import send_mail
from ..utils.redirects import is_safe_next
from .passwords import verify_password, hash_password
from .tokens import issue_token, decode_token

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_url = request.values.get("next", "")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and verify_password(password, user["password"]):
            token = issue_token(email)
            destination = next_url if is_safe_next(next_url) else url_for(
                "slots.dashboard"
            )
            resp = make_response(redirect(destination))
            resp.set_cookie("token", token)
            return resp
        error = "Invalid Credentials. Please try again."
    return render_template("auth/login.html", error=error, next=next_url)


@bp.route("/logout")
def logout():
    resp = make_response(redirect(url_for("auth.login")))
    resp.set_cookie("token", "", expires=0)
    return resp


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form.get("role", "user")
        if role not in ("user", "admin"):
            role = "user"
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, hash_password(password), role),
            )
            db.commit()
            return redirect(url_for("auth.login"))
        except Exception:
            error = "Email already registered."
    return render_template("auth/signup.html", error=error)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    email = request.args.get("email", "")
    if request.method == "POST":
        email = request.form["email"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            token = jwt.encode(
                {
                    "email": email,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            host = request.headers.get("X-Forwarded-Host") or request.host
            scheme = request.headers.get("X-Forwarded-Proto", "http")
            reset_url = f"{scheme}://{host}/reset-password/{token}"
            try:
                send_mail(
                    email,
                    "Password reset request",
                    f"Use this link to reset your password (valid 60 minutes):\n\n{reset_url}",
                )
            except Exception as exc:
                current_app.logger.warning(
                    "Reset mail delivery failed for %s: %s", email, exc
                )
                with open(
                    f"{current_app.config['UPLOAD_DIR']}/logs3.txt", "a"
                ) as log_file:
                    log_file.write(
                        f"Password reset link for {email}: {reset_url}\n"
                    )
            flash(
                f"A password reset link has been emailed to {email}. The link is valid for 60 minutes."
            )
        else:
            flash(f"If the email {email} exists, a reset link will be sent.")
        return redirect(f"/forgot-password?email={urllib.parse.quote(email)}")
    return render_template("auth/forgot_password.html", message=None, email=email)


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    error = None
    try:
        data = decode_token(token)
        email = data["email"]
    except Exception:
        error = "The reset link is invalid or has expired."
        return render_template("auth/reset_password.html", error=error)
    if request.method == "POST":
        password = request.form["password"]
        db = get_db()
        # TODO: route password updates through auth.passwords.hash_password (JIRA-4421)
        db.execute("UPDATE users SET password = ? WHERE email = ?", (password, email))
        db.commit()
        flash("Your password has been reset. Please log in.")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", error=error)
