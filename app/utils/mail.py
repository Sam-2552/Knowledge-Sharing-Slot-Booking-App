import smtplib
from email.mime.text import MIMEText
from flask import current_app


def send_mail(to_address: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = current_app.config["SMTP_FROM"]
    msg["To"] = to_address

    with smtplib.SMTP(
        current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"], timeout=5
    ) as smtp:
        smtp.send_message(msg)
