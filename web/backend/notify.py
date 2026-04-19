"""
notify.py — Shared notification helpers used by payments, subscribers, and heartbeat.
Reads from the shared CONFIG object on each call; values are set at startup from environment variables.
"""
import logging
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import CONFIG

logger = logging.getLogger("gsh.notify")


def notify_telegram(message: str) -> bool:
    cfg = CONFIG["NOTIFICATIONS"]["TELEGRAM"]
    if not cfg.get("enabled") or not cfg.get("bot_token") or not cfg.get("chat_id"):
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage",
            json={"chat_id": cfg["chat_id"], "text": message},
            timeout=10,
        )
        ok = r.status_code == 200 and r.json().get("ok")
        if not ok:
            logger.warning("Telegram notify failed: %s", r.text[:120])
        return ok
    except requests.exceptions.RequestException as e:
        logger.warning("Telegram notify error: %s", e)
        return False


def notify_discord(message: str) -> bool:
    cfg = CONFIG["NOTIFICATIONS"]["DISCORD"]
    if not cfg.get("enabled") or not cfg.get("webhook_url"):
        return False
    try:
        r = requests.post(cfg["webhook_url"], json={"content": message}, timeout=10)
        ok = r.status_code in (200, 204)
        if not ok:
            logger.warning("Discord notify failed: %s", r.text[:120])
        return ok
    except requests.exceptions.RequestException as e:
        logger.warning("Discord notify error: %s", e)
        return False


def notify_pushover(message: str, title: str = "GuardianStreams") -> bool:
    cfg = CONFIG["NOTIFICATIONS"]["PUSHOVER"]
    if not cfg.get("enabled") or not cfg.get("api_token") or not cfg.get("user_key"):
        return False
    try:
        r = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": cfg["api_token"],
                "user": cfg["user_key"],
                "title": title,
                "message": message,
            },
            timeout=10,
        )
        ok = r.status_code == 200 and r.json().get("status") == 1
        if not ok:
            logger.warning("Pushover notify failed: %s", r.text[:120])
        return ok
    except requests.exceptions.RequestException as e:
        logger.warning("Pushover notify error: %s", e)
        return False


def notify_all(message: str, title: str = "GuardianStreams") -> dict:
    """Fire message to all enabled channels. Returns per-channel result."""
    return {
        "telegram":  notify_telegram(message),
        "discord":   notify_discord(message),
        "pushover":  notify_pushover(message, title=title),
    }


def notify_email_html(subject: str, html_body: str, to: str) -> bool:
    cfg = CONFIG["NOTIFICATIONS"]["EMAIL"]
    if not cfg.get("enabled"):
        return False
    username = cfg.get("username")
    password = cfg.get("password")
    if not username or not password:
        logger.warning("notify_email_html: email credentials not configured")
        return False
    from_email = cfg.get("from_email", "billing@guardianstreams.com")
    from_name = cfg.get("from_name", "GuardianStreams")
    smtp_server = cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = int(cfg.get("smtp_port", 587))
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to
        msg.attach(MIMEText(
            "Open this email in an HTML-capable client to view the GSH daily summary.",
            "plain",
        ))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(username, password)
            server.sendmail(from_email, to, msg.as_string())
        logger.info("notify_email_html: sent '%s' to %s", subject, to)
        return True
    except Exception as exc:
        logger.warning("notify_email_html error: %s", exc)
        return False
