"""
email_tool.py
SMTP send helper used by the Streamlit email agent.

Reads SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS from os.environ
(populated by streamlit_app.py from .env or st.secrets).
"""

import os
import smtplib
from email.mime.text import MIMEText


def send_email(to, subject, body):
    """
    Send an email. `to` can be a single address (str) or a list/tuple of
    addresses. When there are multiple recipients, they are placed in Bcc
    so they don't see each other's email addresses.

    Returns a human-readable status string (used directly as the chat
    reply / tool result content).
    """
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_user = os.environ["SMTP_USER"]
    smtp_pass = os.environ["SMTP_PASS"]

    # Normalize `to` into a clean list of address strings, whether it
    # arrived as "a@x.com, b@y.com" or ["a@x.com", "b@y.com"].
    if isinstance(to, str):
        recipients = [addr.strip() for addr in to.split(",") if addr.strip()]
    elif isinstance(to, (list, tuple)):
        recipients = [str(addr).strip() for addr in to if str(addr).strip()]
    else:
        recipients = []

    if not recipients:
        return "No valid recipient email address was provided."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user

    if len(recipients) == 1:
        msg["To"] = recipients[0]
    else:
        # Keep the visible "To" clean and put the real list in Bcc so a
        # multi-person email (e.g. a feedback request) doesn't expose
        # everyone's address to everyone.
        msg["To"] = smtp_user
        msg["Bcc"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipients, msg.as_string())
        return f"✅ Email sent successfully to {len(recipients)} recipient(s): {', '.join(recipients)}"
    except Exception as e:
        return f"Failed to send email: {e}"
