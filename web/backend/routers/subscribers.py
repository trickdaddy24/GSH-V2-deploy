import logging
import requests
from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from typing import Any, List, Optional
from auth import verify_api_key
from config import CONFIG
from database import (
    get_all_subscribers, get_subscriber_by_id, create_subscriber,
    update_subscriber, deactivate_subscriber, reactivate_subscriber,
    delete_subscriber, export_subscribers, import_subscribers,
    bulk_update_due_dates,
)
from models import (
    SubscriberCreate, SubscriberUpdate, SubscriberList,
    MessageResponse, BulkDueDateUpdate, BulkUpdateResult,
    BulkNoticeBody, BulkNoticeResult,
)
from notify import notify_all

logger = logging.getLogger("gsh.subscribers")
router = APIRouter()


def _send_notice(acc_id: str, sub: dict, cfg: dict) -> bool:
    """Send a Telegram due-notice message with inline 💳 Record Payment button.
    Returns True on success, False on any error.
    """
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
        r = requests.post(
            f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage",
            json={"chat_id": cfg["chat_id"], "text": text, "reply_markup": keyboard},
            timeout=10,
        )
        return r.status_code == 200 and r.json().get("ok", False)
    except Exception as exc:
        logger.warning("_send_notice error for %s: %s", acc_id, exc)
        return False


def _bulk_notice_task(acc_ids: list) -> None:
    """Background task: sends a due notice to each account ID."""
    cfg = CONFIG["NOTIFICATIONS"]["TELEGRAM"]
    if not cfg.get("bot_token") or not cfg.get("chat_id"):
        logger.warning("bulk_notice_task: Telegram not configured, skipping")
        return
    for acc_id in acc_ids:
        sub = get_subscriber_by_id(acc_id)
        if sub:
            _send_notice(acc_id, sub, cfg)


@router.post("/bulk/send-due-notices", response_model=BulkNoticeResult, dependencies=[Depends(verify_api_key)])
def bulk_send_due_notices(body: BulkNoticeBody, bg: BackgroundTasks):
    """Send a Telegram due-notice to all delinquent subscribers (or a specific list)."""
    if body.account_ids is not None:
        ids = body.account_ids
    else:
        result = get_all_subscribers(status_filter="delinquent", page_size=1000)
        ids = [s["id"] for s in result["subscribers"]]

    bg.add_task(_bulk_notice_task, ids)
    return BulkNoticeResult(
        sent=len(ids),
        failed=0,
        message=f"Sending due notices to {len(ids)} account{'s' if len(ids) != 1 else ''}",
    )


@router.post("/{acc_id}/send-due-notice", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def send_due_notice(acc_id: str):
    """Send a Telegram due-notice with inline payment button for a single subscriber."""
    sub = get_subscriber_by_id(acc_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Account {acc_id} not found")

    cfg = CONFIG["NOTIFICATIONS"]["TELEGRAM"]
    if not cfg.get("enabled"):
        raise HTTPException(status_code=400, detail="Telegram notifications are disabled")
    if not cfg.get("bot_token") or not cfg.get("chat_id"):
        raise HTTPException(status_code=400, detail="Telegram bot_token or chat_id not configured")

    ok = _send_notice(acc_id, sub, cfg)
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to send Telegram message")
    return {"message": f"Due notice sent for {acc_id}"}


@router.get("", response_model=SubscriberList, dependencies=[Depends(verify_api_key)])
def list_subscribers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    package: Optional[str] = Query(None),
    sort_by: str = Query("id"),
    sort_dir: str = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    include_inactive: bool = Query(False),
):
    return get_all_subscribers(
        search=search,
        status_filter=status,
        package_filter=package,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
        include_inactive=include_inactive,
    )


@router.get("/{acc_id}", dependencies=[Depends(verify_api_key)])
def get_subscriber(acc_id: str):
    sub = get_subscriber_by_id(acc_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Account {acc_id} not found")
    return sub


@router.post("", status_code=201, dependencies=[Depends(verify_api_key)])
def add_subscriber(body: SubscriberCreate):
    acc_id, error = create_subscriber(
        username=body.username,
        email=body.email,
        phone=body.phone,
        package_id=body.package_id,
        due_date=body.due_date,
        custom_price=body.custom_price,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"id": acc_id, "message": f"Account {acc_id} created"}


@router.patch("/{acc_id}", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def edit_subscriber(acc_id: str, body: SubscriberUpdate, bg: BackgroundTasks):
    fields = body.model_dump(exclude_none=True)
    ok, error = update_subscriber(acc_id, fields)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    changed = ", ".join(fields.keys())
    bg.add_task(notify_all, f"✏️ Subscriber updated\nAccount: {acc_id}\nFields changed: {changed}")
    return {"message": f"Account {acc_id} updated"}


@router.post("/{acc_id}/deactivate", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def deactivate(acc_id: str):
    ok, error = deactivate_subscriber(acc_id)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} deactivated"}


@router.post("/{acc_id}/reactivate", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def reactivate(acc_id: str):
    ok, error = reactivate_subscriber(acc_id)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} reactivated"}


@router.delete("/{acc_id}", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def delete(acc_id: str):
    ok, error = delete_subscriber(acc_id)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} permanently deleted"}


@router.get("/export/json", dependencies=[Depends(verify_api_key)])
def export():
    return export_subscribers()


@router.post("/import/json", dependencies=[Depends(verify_api_key)])
def import_json(data: List[Any] = Body(...)):
    return import_subscribers(data)


@router.post("/bulk/due-dates", response_model=BulkUpdateResult, dependencies=[Depends(verify_api_key)])
def bulk_due_dates(body: BulkDueDateUpdate, preview: bool = Query(False)):
    result = bulk_update_due_dates(
        advance_days=body.advance_days,
        account_ids=body.account_ids,
        status_filter=body.status_filter,
        package_filter=body.package_filter,
        preview_only=preview,
    )
    return result
