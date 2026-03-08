import os
import requests
from fastapi import APIRouter, Depends, HTTPException
from dotenv import set_key
from auth import verify_api_key
from config import CONFIG
from database import backup_database
from models import MessageResponse, BackupResponse

router = APIRouter()

_ENV_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Maps "service.field" -> ENV_VAR_NAME
_ENV_MAP = {
    "telegram.enabled":    "TELEGRAM_ENABLED",
    "telegram.bot_token":  "TELEGRAM_BOT_TOKEN",
    "telegram.chat_id":    "TELEGRAM_CHAT_ID",
    "discord.enabled":     "DISCORD_ENABLED",
    "discord.webhook_url": "DISCORD_WEBHOOK_URL",
    "pushover.enabled":    "PUSHOVER_ENABLED",
    "pushover.api_token":  "PUSHOVER_API_TOKEN",
    "pushover.user_key":   "PUSHOVER_USER_KEY",
    "email.enabled":       "EMAIL_ENABLED",
    "email.smtp_server":   "EMAIL_SMTP_SERVER",
    "email.smtp_port":     "EMAIL_SMTP_PORT",
    "email.username":      "EMAIL_USERNAME",
    "email.password":      "EMAIL_PASSWORD",
    "email.from_email":    "EMAIL_FROM",
    "email.from_name":     "EMAIL_FROM_NAME",
}


@router.get("/settings", dependencies=[Depends(verify_api_key)])
def get_settings():
    n = CONFIG["NOTIFICATIONS"]
    return {
        "telegram": {
            "enabled":   n["TELEGRAM"]["enabled"],
            "bot_token": n["TELEGRAM"].get("bot_token") or "",
            "chat_id":   n["TELEGRAM"].get("chat_id") or "",
        },
        "discord": {
            "enabled":     n["DISCORD"]["enabled"],
            "webhook_url": n["DISCORD"].get("webhook_url") or "",
        },
        "pushover": {
            "enabled":   n["PUSHOVER"]["enabled"],
            "api_token": n["PUSHOVER"].get("api_token") or "",
            "user_key":  n["PUSHOVER"].get("user_key") or "",
        },
        "email": {
            "enabled":     n["EMAIL"]["enabled"],
            "smtp_server": n["EMAIL"].get("smtp_server") or "",
            "smtp_port":   str(n["EMAIL"].get("smtp_port") or "587"),
            "username":    n["EMAIL"].get("username") or "",
            "password":    n["EMAIL"].get("password") or "",
            "from_email":  n["EMAIL"].get("from_email") or "",
            "from_name":   n["EMAIL"].get("from_name") or "",
        },
    }


@router.patch("/settings", dependencies=[Depends(verify_api_key)])
def update_settings(body: dict):
    if not os.path.exists(_ENV_FILE):
        raise HTTPException(status_code=500, detail=f".env not found at {_ENV_FILE}")

    updated = []
    for flat_key, env_var in _ENV_MAP.items():
        service, field = flat_key.split(".", 1)
        if service not in body or field not in body[service]:
            continue
        value = body[service][field]
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif not isinstance(value, str):
            value = str(value)
        # Skip blank password — means "don't change"
        if field == "password" and not value:
            continue
        set_key(_ENV_FILE, env_var, value)
        # Update in-memory config so changes take effect immediately
        svc = service.upper()
        if field == "enabled":
            CONFIG["NOTIFICATIONS"][svc]["enabled"] = value == "true"
        elif field == "smtp_port":
            CONFIG["NOTIFICATIONS"][svc]["smtp_port"] = int(value) if value.isdigit() else 587
        else:
            CONFIG["NOTIFICATIONS"][svc][field] = value
        updated.append(env_var)

    return {"updated": updated, "message": f"Saved {len(updated)} setting(s)"}


@router.post("/test/telegram", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def test_telegram():
    cfg = CONFIG["NOTIFICATIONS"]["TELEGRAM"]
    if not cfg["enabled"]:
        raise HTTPException(status_code=400, detail="Telegram is disabled")
    if not cfg.get("bot_token") or not cfg.get("chat_id"):
        raise HTTPException(status_code=400, detail="Missing Telegram credentials")
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage",
            json={"chat_id": cfg["chat_id"], "text": "🧪 Test from GuardianStreams Web"},
            timeout=10,
        )
        if r.status_code != 200 or not r.json().get("ok"):
            raise HTTPException(status_code=502, detail=f"Telegram error: {r.text}")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"message": "Telegram test message sent"}


@router.get("/status", dependencies=[Depends(verify_api_key)])
def notification_status():
    return {
        svc: {"enabled": CONFIG["NOTIFICATIONS"][svc.upper()]["enabled"]}
        for svc in ("email", "telegram", "discord", "pushover")
    }


@router.post("/backup", response_model=BackupResponse, dependencies=[Depends(verify_api_key)])
def backup():
    filename, error = backup_database()
    if error:
        raise HTTPException(status_code=500, detail=error)
    import os
    size_kb = os.path.getsize(filename) / 1024
    return {"filename": filename, "size_kb": round(size_kb, 1)}
