"""
notify.py — Shared notification helpers used by payments, subscribers, and heartbeat.
Reads from the shared CONFIG object on each call; values are set at startup from environment variables.
"""
import logging
import requests
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
