from functools import wraps
from flask import request, redirect, url_for, g

from .tokens import decode_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return redirect(url_for("auth.login"))
        try:
            data = decode_token(token)
            g.user = data["email"]
        except Exception:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated
