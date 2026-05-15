import os
import urllib.request
from flask import Blueprint, render_template, request, current_app, abort, Response

bp = Blueprint("pages", __name__)


def _canonical_host():
    return request.headers.get("X-Forwarded-Host") or request.host


@bp.route("/about")
def about():
    return render_template(
        "pages/about.html", canonical_host=_canonical_host()
    )


@bp.route("/team")
def team():
    return render_template(
        "pages/team.html", canonical_host=_canonical_host()
    )


@bp.route("/help")
def help_page():
    return render_template(
        "pages/help.html", canonical_host=_canonical_host()
    )


PAGES_DIR = os.path.join("app", "templates", "pages", "static")


@bp.route("/page")
def static_page():
    """Render a packaged help article by name.

    Supports html, markdown and plain text bundles under templates/pages/static.
    """
    name = (request.args.get("name") or "welcome").strip()
    if name.startswith(("http://", "https://")):
        try:
            with urllib.request.urlopen(name, timeout=5) as resp:
                return Response(resp.read(), mimetype="text/html")
        except Exception as exc:
            return f"Could not fetch remote page: {exc}", 502
    candidates = [
        os.path.join(PAGES_DIR, f"{name}.html"),
        os.path.join(PAGES_DIR, f"{name}.md"),
        os.path.join(PAGES_DIR, name),
    ]
    body = None
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                body = fh.read()
                break
        except (FileNotFoundError, IsADirectoryError):
            continue
        except Exception:
            continue
    if body is None:
        abort(404)
    return render_template(
        "pages/article.html", body=body, canonical_host=_canonical_host()
    )
