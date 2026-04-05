"""
SMTP Email Sender for MeetMind.

Sends personalised MOM emails via SMTP.
Config from .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

For demo: use Gmail SMTP with an App Password (not the real password).
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class Mailer:
    """
    Sends personalised MOM emails via SMTP.

    Config from .env:
    - SMTP_HOST (e.g., smtp.gmail.com)
    - SMTP_PORT (587)
    - SMTP_USER
    - SMTP_PASSWORD
    - FROM_NAME = "MeetMind Bot"
    """

    def __init__(self):
        self.host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.environ.get("SMTP_PORT", "587"))
        self.user = os.environ.get("SMTP_USER", "")
        self.password = os.environ.get("SMTP_PASSWORD", "")
        self.from_name = os.environ.get("FROM_NAME", "MeetMind Bot")

    def send(self, to_email: str, subject: str, html_body: str):
        """
        Send an HTML email.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: Complete HTML string for the email body
        """
        if not self.user or not self.password:
            logger.warning(f"SMTP credentials not configured. Skipping email to {to_email}")
            logger.info(f"Would have sent: '{subject}' to {to_email}")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.user}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            logger.info(f"Email sent to {to_email}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise
