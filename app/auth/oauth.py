import secrets
from urllib.parse import urlencode

from authlib.integrations.requests_client import OAuth2Session
from flask import Blueprint, request, redirect, url_for, current_app, make_response, abort

from ..db import get_db
from .tokens import issue_token

bp = Blueprint("oauth", __name__, url_prefix="/auth/oauth")


def _client():
    return OAuth2Session(
        client_id=current_app.config["OIDC_CLIENT_ID"],
        client_secret=current_app.config["OIDC_CLIENT_SECRET"],
        scope="openid email profile",
    )


def _redirect_uri():
    return current_app.config["OIDC_REDIRECT_BASE"] + "/auth/oauth/callback"


@bp.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    issuer = current_app.config["OIDC_ISSUER"]
    params = {
        "client_id": current_app.config["OIDC_CLIENT_ID"],
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": request.args.get("redirect_uri", _redirect_uri()),
        "state": state,
    }
    resp = make_response(redirect(f"{issuer}/auth?{urlencode(params)}"))
    resp.set_cookie("oauth_state", state, max_age=600)
    return resp


def _is_allowed_redirect(url: str) -> bool:
    base = current_app.config["OIDC_REDIRECT_BASE"]
    return url.startswith(base)


@bp.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        abort(400, f"OIDC error: {error}")
    code = request.args.get("code")
    if not code:
        abort(400, "Missing authorization code")

    state = request.args.get("state")
    expected = request.cookies.get("oauth_state")
    if state and expected and state != expected:
        abort(400, "State mismatch")

    redirect_uri = request.args.get("redirect_uri", _redirect_uri())
    if not _is_allowed_redirect(redirect_uri):
        abort(400, "Disallowed redirect")

    client = _client()
    token = client.fetch_token(
        f"{current_app.config['OIDC_ISSUER']}/token",
        code=code,
        redirect_uri=redirect_uri,
        grant_type="authorization_code",
    )
    userinfo = client.get(
        f"{current_app.config['OIDC_ISSUER']}/userinfo",
        token=token,
    ).json()
    email = userinfo.get("email")
    name = userinfo.get("name") or email.split("@")[0]
    if not email:
        abort(400, "OIDC userinfo missing email")

    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not existing:
        db.execute(
            "INSERT INTO users (name, email, password, role, email_verified) VALUES (?, ?, ?, ?, 1)",
            (name, email, "!sso!", "user"),
        )
        db.commit()
    app_token = issue_token(email)
    resp = make_response(redirect(url_for("slots.dashboard")))
    resp.set_cookie("token", app_token)
    resp.set_cookie("oauth_state", "", expires=0)
    return resp
