import requests
from fastapi import APIRouter, Depends, HTTPException
from auth import verify_api_key
from config import CONFIG
from database import backup_database
from models import MessageResponse, BackupResponse

router = APIRouter()


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
