"""
daily_summary.py — Builds and sends the daily delinquent subscriber summary email.
Runs as an asyncio background task started from main.py lifespan.
Fires at 4:10 AM US/Eastern every day.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from database import get_all_subscribers
from notify import notify_email_html

logger = logging.getLogger("gsh.daily_summary")
EASTERN = ZoneInfo("America/New_York")
ADMIN_EMAIL = "admin@stunna.xyz"
SEND_HOUR = 4
SEND_MINUTE = 10


def _build_card(sub: dict, bot_username: str) -> str:
    acc_id = sub["id"]
    username = sub["username"]
    price = sub["price"]
    days_val = sub.get("days_until_due")
    days_overdue = abs(days_val) if days_val is not None and days_val < 0 else 0

    website_url = f"https://gsh.stunna.xyz/subscribers/{acc_id}"
    tg_button = ""
    if bot_username:
        tg_url = f"https://t.me/{bot_username}?start=pay_{acc_id}"
        tg_button = f"""
        <a href="{tg_url}" style="
            display:inline-block;background:#0088cc;color:#ffffff;
            text-decoration:none;padding:8px 16px;border-radius:5px;
            font-size:13px;font-weight:600;margin-left:8px;">
            💬 Record via Telegram
        </a>"""

    return f"""
    <div style="
        background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;
        margin-bottom:16px;overflow:hidden;font-family:Arial,sans-serif;">
      <div style="background:#1a1f2e;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#ffffff;font-weight:700;font-size:14px;font-family:monospace;">{acc_id}</span>
        <span style="background:#dc2626;color:#ffffff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">
          DELINQUENT
        </span>
      </div>
      <div style="padding:14px 16px;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;color:#374151;">
          <tr>
            <td style="padding:4px 0;color:#6b7280;width:110px;">Name</td>
            <td style="padding:4px 0;font-weight:600;">{username}</td>
          </tr>
          <tr>
            <td style="padding:4px 0;color:#6b7280;">Days Overdue</td>
            <td style="padding:4px 0;font-weight:600;color:#dc2626;">{days_overdue} days</td>
          </tr>
          <tr>
            <td style="padding:4px 0;color:#6b7280;">Amount Due</td>
            <td style="padding:4px 0;font-weight:600;">${price:.2f}</td>
          </tr>
        </table>
        <div style="margin-top:12px;">
          <a href="{website_url}" style="
              display:inline-block;background:#8A4DFF;color:#ffffff;
              text-decoration:none;padding:8px 16px;border-radius:5px;
              font-size:13px;font-weight:600;">
            🌐 View on Website
          </a>
          {tg_button}
        </div>
      </div>
    </div>"""


def _build_html(subscribers: list, today: str, bot_username: str) -> str:
    count = len(subscribers)

    if count == 0:
        body = """
        <div style="
            background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
            padding:20px;text-align:center;font-family:Arial,sans-serif;">
          <p style="color:#16a34a;font-size:16px;font-weight:600;margin:0;">
            ✅ No delinquent accounts — all clear today!
          </p>
        </div>"""
    else:
        cards = "".join(_build_card(s, bot_username) for s in subscribers)
        body = cards

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f1f5f9;">
  <div style="max-width:600px;margin:0 auto;padding:24px 16px;font-family:Arial,sans-serif;">

    <div style="background:#1a1f2e;border-radius:8px 8px 0 0;padding:20px 24px;">
      <h1 style="color:#ffffff;margin:0;font-size:20px;">🛡️ GSH Daily Summary</h1>
      <p style="color:#8899aa;margin:6px 0 0;font-size:13px;">{today}</p>
    </div>

    <div style="background:#ffffff;border:1px solid #e2e8f0;border-top:none;
                border-radius:0 0 8px 8px;padding:20px 24px;">
      <p style="color:#374151;font-size:14px;margin:0 0 16px;">
        <strong>{count} delinquent account{'s' if count != 1 else ''}</strong> require attention.
      </p>
      {body}
    </div>

    <p style="color:#94a3b8;font-size:11px;text-align:center;margin-top:12px;">
      GuardianStreams Billing System · <a href="https://gsh.stunna.xyz" style="color:#8A4DFF;">gsh.stunna.xyz</a>
    </p>
  </div>
</body>
</html>"""
