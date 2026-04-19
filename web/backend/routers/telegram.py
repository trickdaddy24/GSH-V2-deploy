"""
telegram.py — Telegram webhook handler for two-step payment recording.

Flow:
  1. User taps "💳 Record Payment" inline button on a due-notice message.
  2. Telegram sends a callback_query to POST /api/telegram/webhook.
  3. Bot stores pending state {chat_id → acc_id, price, username} and
     prompts user to reply with the payment amount (or 'ok').
  4. User replies with a text message.
  5. Bot records the payment via add_payment() and confirms.
"""
import logging
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from auth import verify_api_key
from config import CONFIG
from database import get_subscriber_by_id, add_payment

logger = logging.getLogger("gsh.telegram")
router = APIRouter()

# In-memory state: {chat_id: {"acc_id": str, "price": float, "username": str}}
# NOTE: in-memory only — not safe for multi-worker or multi-replica deploys.
# A container restart clears all pending states. Suitable for single-worker container only.
_pending: dict[int, dict] = {}

_bot_username: str = ""


def _fetch_bot_username() -> str:
    token = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("bot_token", "")
    if not token:
        return ""
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if r.status_code == 200 and r.json().get("ok"):
            return r.json()["result"]["username"]
    except Exception:
        pass
    return ""


_bot_username = _fetch_bot_username()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bot_url(method: str) -> str:
    token = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("bot_token", "")
    return f"https://api.telegram.org/bot{token}/{method}"


def _send_message(chat_id: int, text: str) -> None:
    token = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("bot_token")
    if not token:
        return
    try:
        requests.post(
            _bot_url("sendMessage"),
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("_send_message error: %s", exc)


def _answer_callback(callback_id: str) -> None:
    token = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("bot_token")
    if not token:
        return
    try:
        requests.post(
            _bot_url("answerCallbackQuery"),
            json={"callback_query_id": callback_id},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("_answer_callback error: %s", exc)


def _send_notice_message(chat_id: int, acc_id: str, sub: dict) -> None:
    """Send a due-notice message with inline 💳 Record Payment button to the given chat_id."""
    token = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("bot_token")
    if not token:
        logger.warning("_send_notice_message: bot_token not configured")
        return
    days_val = sub.get("days_until_due")
    days_text = f"{days_val} days" if days_val is not None else "unknown"
    text = (
        f"📅 Payment Due Soon\n"
        f"Account: {acc_id}\n"
        f"Name: {sub['username']}\n"
        f"Amount: ${sub['price']:.2f}\n"
        f"Due in: {days_text}"
    )
    keyboard = {
        "inline_keyboard": [[{
            "text": "💳 Record Payment",
            "callback_data": f"pay:{acc_id}:{sub['price']:.2f}",
        }]]
    }
    try:
        requests.post(
            _bot_url("sendMessage"),
            json={"chat_id": chat_id, "text": text, "reply_markup": keyboard},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("_send_notice_message error for %s: %s", acc_id, exc)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Receives Telegram updates. No API key auth — Telegram calls this directly.
    Always returns HTTP 200 so Telegram does not retry.
    Validated via X-Telegram-Bot-Api-Secret-Token header when TELEGRAM_WEBHOOK_SECRET is set.
    """
    expected_secret = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("webhook_secret", "")
    if expected_secret:
        incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if incoming_secret != expected_secret:
            return {"ok": True}

    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    # ── Callback query (button tap) ───────────────────────────────────────────
    if "callback_query" in body:
        cq = body["callback_query"]
        callback_id = cq.get("id", "")
        data = cq.get("data", "")
        chat_id: int = cq["message"]["chat"]["id"]
        logger.info("callback_query: chat_id=%s data=%r", chat_id, data)

        if data.startswith("pay:"):
            parts = data.split(":")
            if len(parts) == 3:
                acc_id, price_str = parts[1], parts[2]
                try:
                    price = float(price_str)
                except ValueError:
                    logger.warning("callback_query: bad price_str=%r", price_str)
                    _answer_callback(callback_id)
                    return {"ok": True}

                sub = get_subscriber_by_id(acc_id)
                username = sub["username"] if sub else acc_id

                _pending[chat_id] = {"acc_id": acc_id, "price": price, "username": username}
                logger.info("pending set: chat_id=%s acc_id=%s price=%.2f", chat_id, acc_id, price)
                _answer_callback(callback_id)
                _send_message(
                    chat_id,
                    f"💳 Recording payment for {username} ({acc_id})\n"
                    f"Current price: ${price:.2f}\n\n"
                    f"Reply with the amount, or send 'ok' to confirm ${price:.2f}.",
                )
            else:
                logger.warning("callback_query: unexpected parts count=%d data=%r", len(parts), data)

        return {"ok": True}

    # ── Text message (user replied with amount or 'ok') ───────────────────────
    if "message" in body:
        msg = body["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()
        logger.info("message: chat_id=%s text=%r pending_keys=%s", chat_id, text, list(_pending.keys()))

        if text.startswith("/start pay_"):
            acc_id = text[len("/start pay_"):]
            sub = get_subscriber_by_id(acc_id)
            if sub:
                _send_notice_message(chat_id, acc_id, sub)
            else:
                _send_message(chat_id, f"Account {acc_id} not found.")
            return {"ok": True}

        if chat_id in _pending:
            pending = _pending[chat_id]
            acc_id: str = pending["acc_id"]
            price: float = pending["price"]
            username: str = pending["username"]

            if text.lower() == "ok":
                amount = price
            else:
                try:
                    amount = float(text)
                except ValueError:
                    _send_message(chat_id, "Please send a number (e.g. 30) or 'ok' to confirm.")
                    return {"ok": True}

            logger.info("recording payment: acc_id=%s amount=%.2f", acc_id, amount)
            ok, error = add_payment(acc_id=acc_id, amount=amount, status="paid", advance_days=30)
            if ok:
                sub = get_subscriber_by_id(acc_id)
                new_due = sub["due_date"] if sub else "unknown"
                del _pending[chat_id]
                logger.info("payment ok: acc_id=%s new_due=%s", acc_id, new_due)
                _send_message(
                    chat_id,
                    f"✅ Payment of ${amount:.2f} recorded for {acc_id}.\nNew due date: {new_due}",
                )
            else:
                del _pending[chat_id]
                logger.error("payment failed: acc_id=%s error=%s", acc_id, error)
                _send_message(chat_id, f"❌ Failed to record payment: {error}")
        else:
            logger.info("message: chat_id=%s not in pending, ignoring", chat_id)

    return {"ok": True}


@router.get("/webhook/set", dependencies=[Depends(verify_api_key)])
def set_webhook():
    """
    One-time setup: registers https://gsh.stunna.xyz/api/telegram/webhook
    with the Telegram Bot API. Call this once after deploy.
    """
    token = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("bot_token")
    if not token:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN not configured")
    webhook_url = "https://gsh.stunna.xyz/api/telegram/webhook"
    secret = CONFIG["NOTIFICATIONS"]["TELEGRAM"].get("webhook_secret", "")
    payload: dict = {"url": webhook_url}
    if secret:
        payload["secret_token"] = secret
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json=payload,
            timeout=10,
        )
        return r.json()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))
