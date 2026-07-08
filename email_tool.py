"""
email_tool.py
Handles the actual sending of emails via SMTP.
Works with Gmail, Outlook, or any SMTP provider — just change the .env values.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email using SMTP credentials from environment variables.
    Returns a status string that gets fed back to the AI agent.
    """
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not smtp_user or not smtp_pass:
        return "ERROR: SMTP_USER or SMTP_PASS not set in .env file."

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to], msg.as_string())
        return f"SUCCESS: Email sent to {to} with subject '{subject}'."
    except Exception as e:
        return f"ERROR: Failed to send email — {e}"
