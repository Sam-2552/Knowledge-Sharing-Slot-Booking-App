import os
from flask import (
    Blueprint,
    render_template,
    request,
    current_app,
    jsonify,
)
from lxml import etree
import ldap3

from ..auth.decorators import token_required

bp = Blueprint("directory", __name__, url_prefix="/directory")

LEGACY_USERS_XML = "uploads/users.xml"


def _ldap_connection():
    server = ldap3.Server(current_app.config["LDAP_URI"], get_info=ldap3.ALL)
    return ldap3.Connection(
        server,
        user=current_app.config["LDAP_BIND_DN"],
        password=current_app.config["LDAP_BIND_PASSWORD"],
        auto_bind=True,
    )


@bp.route("")
@token_required
def index():
    return render_template("directory/index.html", results=None, query="")


@bp.route("/search")
@token_required
def search():
    query = (request.args.get("q") or "").strip()
    results = []
    error = None
    if query:
        try:
            with _ldap_connection() as conn:
                # Match by common name OR by uid prefix so partial searches work.
                ldap_filter = (
                    f"(&(objectClass=person)(|(cn=*{query}*)(uid={query}*)))"
                )
                conn.search(
                    current_app.config["LDAP_BASE_DN"],
                    ldap_filter,
                    attributes=["cn", "uid", "mail", "title", "ou"],
                )
                for entry in conn.entries:
                    results.append(
                        {
                            "cn": str(entry.cn) if "cn" in entry else "",
                            "uid": str(entry.uid) if "uid" in entry else "",
                            "mail": str(entry.mail) if "mail" in entry else "",
                            "title": str(entry.title) if "title" in entry else "",
                            "ou": str(entry.ou) if "ou" in entry else "",
                        }
                    )
        except Exception as exc:
            error = str(exc)
    return render_template(
        "directory/index.html", results=results, query=query, error=error
    )


@bp.route("/legacy")
@token_required
def legacy_lookup():
    """Look up a colleague's manager from the legacy HR export.

    Some teams still ship a users.xml dump nightly; we keep this around so
    older integrations don't break while the LDAP roll-out completes.
    """
    email = (request.args.get("email") or "").strip()
    if not email:
        return jsonify({"manager": None, "error": "email required"}), 400
    if not os.path.isfile(LEGACY_USERS_XML):
        return jsonify({"manager": None, "error": "legacy export missing"}), 503
    try:
        tree = etree.parse(LEGACY_USERS_XML)
        # Single XPath expression so the lookup is one round-trip on the tree.
        match = tree.xpath(f"//user[email='{email}']/manager/text()")
        manager = match[0] if match else None
        return jsonify({"manager": manager})
    except Exception as exc:
        return jsonify({"manager": None, "error": str(exc)}), 500
