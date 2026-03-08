import requests as http
from fastapi import APIRouter, Depends, HTTPException, Query
from auth import verify_api_key
from config import CONFIG
from database import get_customer_data
from risk import run_general_risk, run_enhanced_risk
from models import RiskReport

router = APIRouter()


@router.get("/general", response_model=RiskReport, dependencies=[Depends(verify_api_key)])
def general_risk():
    customers = get_customer_data()
    return run_general_risk(customers)


@router.get("/enhanced", response_model=RiskReport, dependencies=[Depends(verify_api_key)])
def enhanced_risk():
    customers = get_customer_data()
    return run_enhanced_risk(customers)


@router.post("/send-reminders", dependencies=[Depends(verify_api_key)])
def send_reminders(mode: str = Query("general", pattern="^(general|enhanced)$")):
    customers = get_customer_data()
    report = run_general_risk(customers) if mode == "general" else run_enhanced_risk(customers)

    if not report["predictions"]:
        return {"sent": 0, "total": 0, "errors": [], "message": "No at-risk subscribers found"}

    cfg = CONFIG["NOTIFICATIONS"]["TELEGRAM"]
    if not cfg.get("enabled") or not cfg.get("bot_token") or not cfg.get("chat_id"):
        raise HTTPException(status_code=400, detail="Telegram is not configured. Enable it in .env")

    sent, errors = 0, []
    for p in report["predictions"]:
        flags = ", ".join(p["flags"]) if p["flags"] else "—"
        msg = (
            f"⚠️ Payment Reminder\n"
            f"Account: {p['username']} ({p['id']})\n"
            f"Risk: {p['risk_level'].upper()} (score {p['risk_score']})\n"
            f"Flags: {flags}"
        )
        try:
            r = http.post(
                f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage",
                json={"chat_id": cfg["chat_id"], "text": msg},
                timeout=10,
            )
            if r.status_code == 200 and r.json().get("ok"):
                sent += 1
            else:
                errors.append(f"{p['username']}: {r.text[:120]}")
        except Exception as e:
            errors.append(f"{p['username']}: {e}")

    return {
        "sent": sent,
        "total": len(report["predictions"]),
        "errors": errors,
        "message": f"Sent {sent}/{len(report['predictions'])} reminders",
    }
