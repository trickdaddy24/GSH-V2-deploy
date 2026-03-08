"""
database.py — All DB operations for the FastAPI backend.
Same logic as subscription_manager.py but returns data instead of printing.
"""

import re
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from config import (
    CONFIG, DATE_FORMAT, DATE_INPUT_FORMATS, ACCOUNT_PREFIX, ACCOUNT_PADDING,
    DELINQUENT_DAYS, INITIAL_DAYS, PAID_DAYS, MAX_PAYMENT_HISTORY,
    RISK_HIGH, RISK_IMMINENT_DAYS,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(CONFIG["DB_NAME"])
    db.row_factory = sqlite3.Row
    return db


def migrate_db():
    """Add any missing columns to existing databases on startup."""
    db = get_db()
    try:
        c = db.cursor()
        existing = {row[1] for row in c.execute("PRAGMA table_info(subscriptions)")}
        if "is_active" not in existing:
            c.execute("ALTER TABLE subscriptions ADD COLUMN is_active INTEGER DEFAULT 1")
            db.commit()
        if "creation_date" not in existing:
            c.execute("ALTER TABLE subscriptions ADD COLUMN creation_date TEXT")
            db.commit()
        if "grace_period_used" not in existing:
            c.execute("ALTER TABLE subscriptions ADD COLUMN grace_period_used INTEGER DEFAULT 0")
            db.commit()
    finally:
        db.close()


def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def is_valid_email(email: str) -> bool:
    if not email:
        return True
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return True
    return len(re.sub(r"\D", "", phone)) >= 7


def determine_status(subscription: Dict, latest_payment: Optional[Dict]) -> str:
    now = datetime.now()
    try:
        due = datetime.strptime(subscription["due_date"], DATE_FORMAT)
    except (ValueError, TypeError):
        return subscription.get("status", "pending")

    if (now - due).days > DELINQUENT_DAYS:
        return "delinquent"

    creation_str = subscription.get("creation_date")
    if creation_str:
        try:
            created = datetime.strptime(creation_str, DATE_FORMAT)
            if (now - created).days <= INITIAL_DAYS:
                return "initial"
        except ValueError:
            pass

    if latest_payment and latest_payment.get("status") == "paid":
        try:
            paid_on = datetime.strptime(latest_payment["payment_date"], DATE_FORMAT)
            if (now - paid_on).days <= PAID_DAYS:
                return "paid"
        except ValueError:
            pass

    stored = subscription.get("status", "pending")
    return stored if stored == "active" else "pending"


def generate_account_id() -> str:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM subscriptions WHERE id LIKE 'dtv.%'")
            existing = {row[0] for row in c.fetchall()}
        i = 0
        while True:
            candidate = f"{ACCOUNT_PREFIX}{i:0{ACCOUNT_PADDING}d}"
            if candidate not in existing:
                return candidate
            i += 1
    except sqlite3.Error:
        return f"{ACCOUNT_PREFIX}{'0' * ACCOUNT_PADDING}"


def _row_to_subscriber(row, latest_payment: Optional[Dict] = None) -> Dict:
    sub = {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "phone": row["phone"],
        "package": row["package"],
        "price": row["price"],
        "due_date": row["due_date"],
        "status": row["status"],
        "creation_date": row["creation_date"],
        "grace_period_used": bool(row["grace_period_used"]),
        "is_active": bool(row["is_active"]),
    }
    sub["display_status"] = determine_status(sub, latest_payment)
    return sub


# ── Dashboard ──────────────────────────────────────────────────────────────────

def get_dashboard_stats() -> Dict:
    now = datetime.now()
    cutoff = now + timedelta(days=7)

    with get_db() as conn:
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1")
        total_active = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 0")
        total_inactive = c.fetchone()[0]

        c.execute("SELECT COALESCE(SUM(price), 0) FROM subscriptions WHERE is_active = 1")
        monthly_revenue = float(c.fetchone()[0])

        c.execute("SELECT status, COUNT(*) FROM subscriptions WHERE is_active = 1 GROUP BY status")
        status_counts = dict(c.fetchall())

        c.execute("""
            SELECT b.payment_date, b.amount, b.status, s.username, s.id
            FROM billing_history b
            JOIN subscriptions s ON s.id = b.subscription_id
            ORDER BY b.id DESC LIMIT 10
        """)
        recent_rows = c.fetchall()

        c.execute("""
            SELECT s.id, s.username, s.email, s.phone, s.package, s.price,
                   s.due_date, s.status, s.creation_date, s.is_active,
                   lp.payment_date, lp.status AS lp_status
            FROM subscriptions s
            LEFT JOIN (
                SELECT subscription_id, payment_date, status,
                       ROW_NUMBER() OVER (PARTITION BY subscription_id ORDER BY payment_date DESC) AS rn
                FROM billing_history
            ) lp ON lp.subscription_id = s.id AND lp.rn = 1
            WHERE s.is_active = 1
        """)
        all_rows = c.fetchall()

    delinquent = []
    due_soon = []
    for row in all_rows:
        sub = dict(row)
        lp = {"payment_date": sub.pop("payment_date", None), "status": sub.pop("lp_status", None)}
        display = determine_status(sub, lp if lp["payment_date"] else None)
        if display == "delinquent":
            delinquent.append({"id": sub["id"], "username": sub["username"], "due_date": sub["due_date"]})
        try:
            due_dt = datetime.strptime(sub["due_date"], DATE_FORMAT)
            if now <= due_dt <= cutoff:
                due_soon.append({"id": sub["id"], "username": sub["username"], "due_date": sub["due_date"]})
        except (ValueError, TypeError):
            pass

    recent_payments = [
        {"payment_date": r[0], "amount": r[1], "status": r[2], "username": r[3], "account_id": r[4]}
        for r in recent_rows
    ]

    return {
        "total_active": total_active,
        "total_inactive": total_inactive,
        "monthly_revenue": monthly_revenue,
        "status_breakdown": {
            "paid": status_counts.get("paid", 0),
            "active": status_counts.get("active", 0),
            "pending": status_counts.get("pending", 0),
            "initial": status_counts.get("initial", 0),
            "delinquent": status_counts.get("delinquent", 0),
        },
        "delinquent_count": len(delinquent),
        "due_soon_count": len(due_soon),
        "delinquent_accounts": delinquent[:10],
        "due_soon_accounts": due_soon[:10],
        "recent_payments": recent_payments,
    }


# ── Subscribers ────────────────────────────────────────────────────────────────

def get_all_subscribers(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    package_filter: Optional[str] = None,
    sort_by: str = "id",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 50,
    include_inactive: bool = False,
) -> Dict:
    with get_db() as conn:
        c = conn.cursor()
        where = [] if include_inactive else ["s.is_active = 1"]
        params = []

        if search:
            where.append("LOWER(s.username) LIKE ?")
            params.append(f"%{search.lower()}%")
        if package_filter:
            where.append("s.package = ?")
            params.append(package_filter)

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""

        c.execute(f"""
            SELECT s.id, s.username, s.email, s.phone, s.package, s.price,
                   s.due_date, s.status, s.creation_date, s.is_active,
                   s.grace_period_used,
                   lp.payment_date, lp.status AS lp_status
            FROM subscriptions s
            LEFT JOIN (
                SELECT subscription_id, payment_date, status,
                       ROW_NUMBER() OVER (PARTITION BY subscription_id ORDER BY payment_date DESC) AS rn
                FROM billing_history
            ) lp ON lp.subscription_id = s.id AND lp.rn = 1
            {where_clause}
        """, params)

        rows = c.fetchall()

    subscribers = []
    for row in rows:
        d = dict(row)
        lp = {"payment_date": d.pop("payment_date"), "status": d.pop("lp_status")}
        d["display_status"] = determine_status(d, lp if lp["payment_date"] else None)
        d["grace_period_used"] = bool(d["grace_period_used"])
        d["is_active"] = bool(d["is_active"])
        d["price"] = float(d["price"])
        subscribers.append(d)

    if status_filter:
        subscribers = [s for s in subscribers if s["display_status"] == status_filter]

    valid_sorts = {"id", "username", "due_date", "price", "display_status"}
    if sort_by not in valid_sorts:
        sort_by = "id"

    reverse = sort_dir == "desc"
    try:
        if sort_by == "due_date":
            subscribers.sort(
                key=lambda x: datetime.strptime(x["due_date"], DATE_FORMAT),
                reverse=reverse,
            )
        elif sort_by == "username":
            subscribers.sort(key=lambda x: x["username"].lower(), reverse=reverse)
        else:
            subscribers.sort(key=lambda x: x[sort_by], reverse=reverse)
    except (ValueError, KeyError):
        pass

    total = len(subscribers)
    start = (page - 1) * page_size
    paginated = subscribers[start: start + page_size]

    return {"items": paginated, "total": total, "page": page, "page_size": page_size}


def get_subscriber_by_id(acc_id: str) -> Optional[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, email, phone, package, price, due_date, status, "
            "creation_date, is_active, grace_period_used FROM subscriptions WHERE id = ?",
            (acc_id,),
        )
        row = c.fetchone()
        if not row:
            return None

        sub = dict(row)
        sub["price"] = float(sub["price"])
        sub["grace_period_used"] = bool(sub["grace_period_used"])
        sub["is_active"] = bool(sub["is_active"])

        c.execute(
            "SELECT payment_date, status FROM billing_history "
            "WHERE subscription_id = ? ORDER BY payment_date DESC LIMIT 1",
            (acc_id,),
        )
        lp_row = c.fetchone()
        lp = dict(lp_row) if lp_row else None
        sub["display_status"] = determine_status(sub, lp)

        c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM billing_history "
            "WHERE subscription_id = ? AND status = 'paid'",
            (acc_id,),
        )
        sub["total_paid"] = float(c.fetchone()[0])

        c.execute(
            "SELECT id, subscription_id, payment_date, amount, status FROM billing_history "
            "WHERE subscription_id = ? ORDER BY payment_date DESC LIMIT ?",
            (acc_id, MAX_PAYMENT_HISTORY),
        )
        sub["payment_history"] = [dict(r) for r in c.fetchall()]

    return sub


def create_subscriber(
    username: str,
    email: Optional[str],
    phone: Optional[str],
    package_id: str,
    due_date: str,
    custom_price: Optional[float] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Returns (account_id, error_message)."""
    if package_id not in CONFIG["PACKAGES"]:
        return None, "Invalid package ID"
    if not parse_date(due_date):
        return None, "Invalid due date format"
    if email and not is_valid_email(email):
        return None, "Invalid email format"
    if phone and not is_valid_phone(phone):
        return None, "Invalid phone number"

    pkg_name, pkg_price = CONFIG["PACKAGES"][package_id]
    if pkg_name == "Custom":
        if custom_price is None or custom_price <= 0:
            return None, "Custom price required and must be positive"
        price = custom_price
    else:
        price = float(pkg_price)

    acc_id = generate_account_id()
    today = datetime.now().strftime(DATE_FORMAT)
    due_fmt = parse_date(due_date).strftime(DATE_FORMAT)

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO subscriptions "
                "(id, username, email, phone, package, price, due_date, status, creation_date, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'initial', ?, 1)",
                (acc_id, username, email or None, phone or None, pkg_name, price, due_fmt, today),
            )
            conn.commit()
        return acc_id, None
    except sqlite3.Error as e:
        return None, str(e)


def update_subscriber(acc_id: str, fields: Dict) -> Tuple[bool, Optional[str]]:
    """Returns (success, error_message)."""
    ALLOWED = {"username", "email", "phone", "due_date", "package", "price"}
    updates = {k: v for k, v in fields.items() if k in ALLOWED and v is not None}
    if not updates:
        return False, "No valid fields to update"

    if "email" in updates and not is_valid_email(updates["email"]):
        return False, "Invalid email format"
    if "phone" in updates and not is_valid_phone(updates["phone"]):
        return False, "Invalid phone number"
    if "due_date" in updates and not parse_date(updates["due_date"]):
        return False, "Invalid due date format"

    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM subscriptions WHERE id = ? AND is_active = 1", (acc_id,))
            if not c.fetchone():
                return False, "Account not found or inactive"
            for field, value in updates.items():
                c.execute(f"UPDATE subscriptions SET {field} = ? WHERE id = ?", (value, acc_id))
            conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


def deactivate_subscriber(acc_id: str) -> Tuple[bool, Optional[str]]:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE subscriptions SET is_active = 0 WHERE id = ? AND is_active = 1", (acc_id,))
            if c.rowcount == 0:
                return False, "Account not found or already inactive"
            conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


def reactivate_subscriber(acc_id: str) -> Tuple[bool, Optional[str]]:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("UPDATE subscriptions SET is_active = 1 WHERE id = ? AND is_active = 0", (acc_id,))
            if c.rowcount == 0:
                return False, "Account not found or already active"
            conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


def delete_subscriber(acc_id: str) -> Tuple[bool, Optional[str]]:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM billing_history WHERE subscription_id = ?", (acc_id,))
            c.execute("DELETE FROM subscriptions WHERE id = ?", (acc_id,))
            if c.rowcount == 0:
                return False, "Account not found"
            conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


# ── Payments ───────────────────────────────────────────────────────────────────

def add_payment(
    acc_id: str,
    amount: float,
    status: str,
    advance_days: Optional[int] = None,
    custom_due_date: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Returns (success, error_message)."""
    valid_statuses = ("paid", "failed", "grace_period")
    if status not in valid_statuses:
        return False, f"Status must be one of: {', '.join(valid_statuses)}"

    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT username, price, due_date FROM subscriptions WHERE id = ? AND is_active = 1",
                (acc_id,),
            )
            row = c.fetchone()
            if not row:
                return False, "Account not found or inactive"

            _, _, current_due_str = row

            c.execute(
                "INSERT INTO billing_history (subscription_id, payment_date, amount, status) "
                "VALUES (?, ?, ?, ?)",
                (acc_id, datetime.now().strftime(DATE_FORMAT), amount, status),
            )

            if status == "paid":
                if custom_due_date:
                    new_due = parse_date(custom_due_date)
                    if not new_due:
                        return False, "Invalid custom due date format"
                    new_due_str = new_due.strftime(DATE_FORMAT)
                elif advance_days and advance_days > 0:
                    current = datetime.strptime(current_due_str, DATE_FORMAT)
                    new_due_str = (current + timedelta(days=advance_days)).strftime(DATE_FORMAT)
                else:
                    return False, "Paid status requires advance_days or custom_due_date"

                c.execute(
                    "UPDATE subscriptions SET due_date = ?, status = 'paid' WHERE id = ?",
                    (new_due_str, acc_id),
                )

            elif status == "grace_period":
                c.execute(
                    "UPDATE subscriptions SET grace_period_used = 1, status = 'pending' WHERE id = ?",
                    (acc_id,),
                )

            conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


def get_payment_history(acc_id: str) -> List[Dict]:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, subscription_id, payment_date, amount, status "
                "FROM billing_history WHERE subscription_id = ? ORDER BY payment_date DESC",
                (acc_id,),
            )
            return [dict(r) for r in c.fetchall()]
    except sqlite3.Error:
        return []


# ── Bulk Operations ────────────────────────────────────────────────────────────

def bulk_update_due_dates(
    advance_days: int,
    account_ids: Optional[List[str]] = None,
    status_filter: Optional[str] = None,
    package_filter: Optional[str] = None,
    preview_only: bool = False,
) -> Dict:
    result = get_all_subscribers(
        status_filter=status_filter,
        package_filter=package_filter,
        page=1,
        page_size=10000,
    )
    targets = result["items"]

    if account_ids:
        targets = [s for s in targets if s["id"] in account_ids]

    preview = []
    for s in targets:
        try:
            old = datetime.strptime(s["due_date"], DATE_FORMAT)
            new = (old + timedelta(days=advance_days)).strftime(DATE_FORMAT)
            preview.append({"id": s["id"], "username": s["username"],
                            "old_due": s["due_date"], "new_due": new})
        except ValueError:
            pass

    if preview_only:
        return {"updated": 0, "preview": preview, "confirmed": False}

    updated = 0
    try:
        with get_db() as conn:
            c = conn.cursor()
            for item in preview:
                c.execute(
                    "UPDATE subscriptions SET due_date = ? WHERE id = ?",
                    (item["new_due"], item["id"]),
                )
                updated += 1
            conn.commit()
    except sqlite3.Error:
        pass

    return {"updated": updated, "preview": preview, "confirmed": True}


# ── Export / Import ────────────────────────────────────────────────────────────

def export_subscribers() -> List[Dict]:
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, email, phone, package, price, due_date, status, creation_date "
            "FROM subscriptions WHERE is_active = 1"
        )
        rows = c.fetchall()
    return [
        {
            "id": r[0],
            "customer": {"name": r[1], "contact": {"phone": r[3], "email": r[2]}},
            "subscription": {
                "plan": r[4], "price": r[5], "due_date": r[6],
                "status": r[7], "creation_date": r[8],
            },
        }
        for r in rows
    ]


def import_subscribers(data: List[Dict]) -> Dict:
    imported, skipped = 0, 0
    try:
        with get_db() as conn:
            c = conn.cursor()
            for item in data:
                try:
                    username = item["customer"]["name"]
                    email = item["customer"]["contact"].get("email")
                    phone = item["customer"]["contact"].get("phone")
                    plan = item["subscription"]["plan"]
                    price = item["subscription"]["price"]
                    due_date = item["subscription"]["due_date"]
                    creation_date = item["subscription"].get(
                        "creation_date", datetime.now().strftime(DATE_FORMAT)
                    )
                    acc_id = item.get("id") or generate_account_id()

                    if not all([username, plan, price, due_date]) or not parse_date(due_date):
                        skipped += 1
                        continue

                    c.execute(
                        "INSERT OR REPLACE INTO subscriptions "
                        "(id, username, email, phone, package, price, due_date, status, creation_date, is_active) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, 'initial', ?, 1)",
                        (acc_id, username, email, phone, plan, price, due_date, creation_date),
                    )
                    imported += 1
                except (KeyError, ValueError):
                    skipped += 1
            conn.commit()
    except sqlite3.Error as e:
        return {"imported": imported, "skipped": skipped, "error": str(e)}
    return {"imported": imported, "skipped": skipped}


# ── Backup ─────────────────────────────────────────────────────────────────────

def backup_database() -> Tuple[Optional[str], Optional[str]]:
    import os
    db = CONFIG["DB_NAME"]
    if not os.path.exists(db):
        return None, f"Database file not found: {db}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = db.replace(".db", "") + f"_backup_{timestamp}.db"
    try:
        shutil.copy2(db, backup_name)
        size_kb = os.path.getsize(backup_name) / 1024
        return backup_name, None
    except OSError as e:
        return None, str(e)


# ── Customer data for risk ─────────────────────────────────────────────────────

def get_customer_data() -> List[Dict]:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT s.id, s.username, s.email, s.phone,
                       s.due_date, s.status,
                       COALESCE(s.grace_period_used, 0),
                       s.creation_date,
                       lp.payment_date, lp.status AS latest_payment_status,
                       COALESCE(late.late_count, 0) AS late_payments
                FROM subscriptions s
                LEFT JOIN (
                    SELECT subscription_id, payment_date, status,
                           ROW_NUMBER() OVER (
                               PARTITION BY subscription_id ORDER BY payment_date DESC
                           ) AS rn
                    FROM billing_history
                ) lp ON lp.subscription_id = s.id AND lp.rn = 1
                LEFT JOIN (
                    SELECT subscription_id, COUNT(*) AS late_count
                    FROM billing_history
                    WHERE status IN ('failed', 'grace_period')
                    GROUP BY subscription_id
                ) late ON late.subscription_id = s.id
                WHERE s.is_active = 1
            """)
            rows = c.fetchall()

        customers = []
        for row in rows:
            (acc_id, username, email, phone, due_str, status, grace, created,
             lp_date, lp_status, late) = row
            try:
                due_dt = datetime.strptime(due_str, DATE_FORMAT)
            except (ValueError, TypeError):
                continue
            sub = {"id": acc_id, "due_date": due_str, "status": status, "creation_date": created}
            lp = {"payment_date": lp_date, "status": lp_status} if lp_date else None
            display = determine_status(sub, lp)
            customers.append({
                "id": acc_id, "username": username, "email": email, "phone": phone,
                "due_date": due_dt, "status": display,
                "grace_period_used": bool(grace), "late_payments": int(late),
            })
        return customers
    except sqlite3.Error:
        return []
