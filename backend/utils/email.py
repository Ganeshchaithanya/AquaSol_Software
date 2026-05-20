import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config.settings import get_settings

_settings = get_settings()

def send_email(to_address: str, subject: str, body: str) -> bool:
    """Send an email using SMTP.
    This is a minimal placeholder implementation. In production replace with a proper
    email service (SendGrid, SES, etc.).
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = _settings.SMTP_FROM
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(_settings.SMTP_HOST, _settings.SMTP_PORT) as server:
            if _settings.SMTP_TLS:
                server.starttls()
            if _settings.SMTP_USER and _settings.SMTP_PASSWORD:
                server.login(_settings.SMTP_USER, _settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        # Log the error – the logger import is optional to avoid circular imports
        try:
            from backend.utils.logger import logger
            logger.error(f"[email] Failed to send email to {to_address}: {e}")
        finally:
            return False
