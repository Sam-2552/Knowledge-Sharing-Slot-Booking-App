import os
import random
import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    send_from_directory,
    current_app,
)
import jwt

bp = Blueprint("uploads", __name__)


@bp.route("/uploads/")
def root():
    return redirect("/uploads/code")


@bp.route("/uploads/code")
def code():
    filename = request.args.get("file")
    if not filename:
        uploads_path = current_app.config["UPLOAD_DIR"]
        files = []
        if os.path.exists(uploads_path):
            for name in os.listdir(uploads_path):
                fp = os.path.join(uploads_path, name)
                if os.path.isfile(fp):
                    stat = os.stat(fp)
                    files.append(
                        {
                            "name": name,
                            "modified": datetime.datetime.fromtimestamp(
                                stat.st_mtime
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            "size": f"{stat.st_size} bytes",
                        }
                    )
        random.shuffle(files)
        return render_template("uploads/directory.html", files=files)

    token = request.cookies.get("token")
    if not token:
        return "Authentication required to view files", 401
    try:
        jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except Exception:
        return "Invalid token", 401

    uploads_path = os.path.abspath(current_app.config["UPLOAD_DIR"])
    requested_path = os.path.abspath(os.path.join(uploads_path, filename))

    if not requested_path.startswith(uploads_path):
        try:
            with open(requested_path, "r", encoding="utf-8") as fh:
                content = fh.readlines()[:50]
                html_content = []
                for line in content:
                    line = line.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
                    line = line.replace("\n", "<br>")
                    html_content.append(line)
                return "".join(html_content)
        except Exception as e:
            return f"Error reading file: {str(e)}", 500

    return send_from_directory(
        os.path.dirname(requested_path), os.path.basename(requested_path)
    )
