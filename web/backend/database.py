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
    """Create tables if missing and add any missing columns on startup."""
    db = get_db()
    try:
        c = db.cursor()
        # Schema matches the CLI's init_db() exactly
        c.executescript("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                package TEXT,
                price INTEGER,
                due_date TEXT,
                status TEXT NOT NULL CHECK(status IN
                    ('initial','paid','delinquent','pending','active')),
                grace_period_used INTEGER DEFAULT 0,
                creation_date TEXT,
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS billing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id TEXT,
                payment_date TEXT,
                amount REAL,
                status TEXT CHECK(status IN ('paid','failed','grace_period')),
                new_due_date TEXT,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_billing_sub
                ON billing_history(subscription_id);
        """)
        db.commit()

        # ── subscriptions: add missing columns ────────────────────────────────
        sub_cols = {row[1] for row in c.execute("PRAGMA table_info(subscriptions)")}
        for col, defn in [
            ("is_active",         "INTEGER DEFAULT 1"),
            ("creation_date",     "TEXT"),
            ("grace_period_used", "INTEGER DEFAULT 0"),
            ("price",             "INTEGER DEFAULT 0"),
            ("package",           "TEXT"),
            ("email",             "TEXT"),
            ("phone",             "TEXT"),
        ]:
            if col not in sub_cols:
                c.execute(f"ALTER TABLE subscriptions ADD COLUMN {col} {defn}")

        # Copy data from old column names if present (created by earlier broken migration)
        sub_cols = {row[1] for row in c.execute("PRAGMA table_info(subscriptions)")}
        if "custom_price" in sub_cols:
            c.execute("UPDATE subscriptions SET price = custom_price WHERE (price IS NULL OR price = 0) AND custom_price IS NOT NULL")
        if "package_id" in sub_cols:
            c.execute("UPDATE subscriptions SET package = package_id WHERE package IS NULL AND package_id IS NOT NULL")

        # ── billing_history: rename 'date' → 'payment_date' if needed ─────────
        bill_cols = {row[1] for row in c.execute("PRAGMA table_info(billing_history)")}
        if "date" in bill_cols and "payment_date" not in bill_cols:
            c.execute("ALTER TABLE billing_history RENAME COLUMN date TO payment_date")
        if "new_due_date" not in bill_cols:
            c.execute("ALTER TABLE billing_history ADD COLUMN new_due_date TEXT")

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
    today_str = now.strftime(DATE_FORMAT)
    this_month = now.strftime("%m-%Y")
    last_month_dt = (now.replace(day=1) - timedelta(days=1))
    last_month = last_month_dt.strftime("%m-%Y")

    with get_db() as conn:
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM subscriptions")
        total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1")
        active = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 0")
        inactive = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1 AND due_date = ?", (today_str,))
        due_today = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1 AND due_date < ?", (today_str,))
        overdue = c.fetchone()[0]

        c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM billing_history "
            "WHERE status = 'paid' AND strftime('%m-%Y', substr(payment_date,7,4)||'-'||substr(payment_date,1,2)||'-'||substr(payment_date,4,2)) = ?",
            (this_month,),
        )
        revenue_this = float(c.fetchone()[0])

        c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM billing_history "
            "WHERE status = 'paid' AND strftime('%m-%Y', substr(payment_date,7,4)||'-'||substr(payment_date,1,2)||'-'||substr(payment_date,4,2)) = ?",
            (last_month,),
        )
        revenue_last = float(c.fetchone()[0])

    return {
        "total_subscribers": total,
        "active_subscribers": active,
        "inactive_subscribers": inactive,
        "due_today": due_today,
        "overdue": overdue,
        "revenue_this_month": revenue_this,
        "revenue_last_month": revenue_last,
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
            where.append("(LOWER(s.username) LIKE ? OR LOWER(s.id) LIKE ?)")
            params.extend([f"%{search.lower()}%", f"%{search.lower()}%"])
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

    now = datetime.now()
    subscribers = []
    for row in rows:
        d = dict(row)
        lp_date = d.pop("payment_date", None)
        lp_status = d.pop("lp_status", None)
        lp = {"payment_date": lp_date, "status": lp_status} if lp_date else None
        display = determine_status(d, lp)

        pkg_id = str(d.get("package") or "")
        pkg_name = CONFIG["PACKAGES"].get(pkg_id, (pkg_id, 0))[0]
        price = float(d.get("price") or 0)

        try:
            due_dt = datetime.strptime(d["due_date"], DATE_FORMAT)
            days_until_due = (due_dt - now).days
        except (ValueError, TypeError):
            days_until_due = None

        subscribers.append({
            "id": d["id"],
            "username": d["username"],
            "email": d.get("email"),
            "phone": d.get("phone"),
            "package_id": pkg_id,
            "package_name": pkg_name,
            "price": price,
            "due_date": d["due_date"],
            "status": display,
            "days_until_due": days_until_due,
            "last_payment": lp_date,
            "is_active": 1 if d.get("is_active") else 0,
        })

    if status_filter:
        subscribers = [s for s in subscribers if s["status"].lower() == status_filter.lower()]

    valid_sorts = {"id", "username", "due_date", "price", "status"}
    if sort_by not in valid_sorts:
        sort_by = "id"

    reverse = sort_dir == "desc"
    try:
        if sort_by == "due_date":
            subscribers.sort(key=lambda x: datetime.strptime(x["due_date"], DATE_FORMAT), reverse=reverse)
        elif sort_by == "username":
            subscribers.sort(key=lambda x: x["username"].lower(), reverse=reverse)
        else:
            subscribers.sort(key=lambda x: x[sort_by], reverse=reverse)
    except (ValueError, KeyError):
        pass

    total = len(subscribers)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    paginated = subscribers[start: start + page_size]

    return {
        "subscribers": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_subscriber_by_id(acc_id: str) -> Optional[Dict]:
    now = datetime.now()
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

        c.execute(
            "SELECT payment_date, status FROM billing_history "
            "WHERE subscription_id = ? ORDER BY payment_date DESC LIMIT 1",
            (acc_id,),
        )
        lp_row = c.fetchone()
        lp = dict(lp_row) if lp_row else None
        display = determine_status(sub, lp)

        pkg_id = str(sub.get("package") or "")
        pkg_name = CONFIG["PACKAGES"].get(pkg_id, (pkg_id, 0))[0]
        price = float(sub.get("price") or 0)

        try:
            due_dt = datetime.strptime(sub["due_date"], DATE_FORMAT)
            days_until_due = (due_dt - now).days
        except (ValueError, TypeError):
            days_until_due = None

        return {
            "id": sub["id"],
            "username": sub["username"],
            "email": sub.get("email"),
            "phone": sub.get("phone"),
            "package_id": pkg_id,
            "package_name": pkg_name,
            "price": price,
            "due_date": sub["due_date"],
            "status": display,
            "days_until_due": days_until_due,
            "last_payment": lp["payment_date"] if lp else None,
            "is_active": 1 if sub.get("is_active") else 0,
        }


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

            new_due_str = None
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

            c.execute(
                "INSERT INTO billing_history (subscription_id, payment_date, amount, status, new_due_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (acc_id, datetime.now().strftime(DATE_FORMAT), amount, status, new_due_str),
            )

            conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)


def bulk_add_payments(
    amount: float,
    status: str,
    advance_days: int = 30,
    status_filter: Optional[str] = None,
    package_filter: Optional[str] = None,
    account_ids: Optional[List[str]] = None,
    preview_only: bool = False,
) -> dict:
    """Record the same payment for multiple subscribers. Returns affected/succeeded/failed."""
    # Early return for explicitly empty account list
    if account_ids is not None and len(account_ids) == 0:
        return {"affected": 0, "succeeded": [], "failed": [], "message": "No accounts specified"}

    db = get_db()
    try:
        c = db.cursor()
        if account_ids:
            placeholders = ",".join("?" * len(account_ids))
            c.execute(
                f"SELECT id FROM subscriptions WHERE id IN ({placeholders}) AND is_active = 1",
                account_ids,
            )
        else:
            q = "SELECT id FROM subscriptions WHERE is_active = 1"
            params = []
            if status_filter:
                q += " AND status = ?"
                params.append(status_filter)
            if package_filter:
                q += " AND package = ?"
                params.append(package_filter)
            c.execute(q, params)
        ids = [row[0] for row in c.fetchall()]
    finally:
        db.close()

    if preview_only:
        return {"affected": len(ids), "succeeded": [], "failed": [], "message": f"{len(ids)} accounts would be updated"}

    succeeded, failed = [], []
    for acc_id in ids:
        ok, error = add_payment(acc_id=acc_id, amount=amount, status=status, advance_days=advance_days)
        if ok:
            succeeded.append(acc_id)
        else:
            failed.append({"id": acc_id, "error": error})
    return {
        "affected": len(succeeded),
        "succeeded": succeeded,
        "failed": failed,
        "message": f"Recorded payment for {len(succeeded)}/{len(ids)} accounts",
    }


def get_payment_history(acc_id: str) -> List[Dict]:
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, subscription_id, payment_date, amount, status, new_due_date "
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
    targets = result["subscribers"]

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
    skip_reasons: List[str] = []
    try:
        with get_db() as conn:
            c = conn.cursor()
            for i, item in enumerate(data):
                try:
                    username  = item["customer"]["name"]
                    email     = item["customer"]["contact"].get("email")
                    phone     = item["customer"]["contact"].get("phone")
                    sub       = item["subscription"]
                    plan      = sub["plan"]
                    price     = sub["price"]
                    due_date  = sub["due_date"]
                    # null creation_date → use today; missing key → use today
                    creation_date = sub.get("creation_date") or datetime.now().strftime(DATE_FORMAT)
                    acc_id    = item.get("id") or generate_account_id()

                    if not username or not plan or not due_date:
                        skip_reasons.append(f"#{i}: missing required field (username/plan/due_date)")
                        skipped += 1
                        continue
                    if price is None:
                        skip_reasons.append(f"#{i} {username}: missing price")
                        skipped += 1
                        continue
                    if not parse_date(due_date):
                        skip_reasons.append(f"#{i} {username}: unrecognised due_date '{due_date}'")
                        skipped += 1
                        continue

                    c.execute(
                        "INSERT OR REPLACE INTO subscriptions "
                        "(id, username, email, phone, package, price, due_date, status, creation_date, is_active) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, 'initial', ?, 1)",
                        (acc_id, username, email or None, phone or None,
                         plan, price, due_date, creation_date),
                    )
                    imported += 1
                except (KeyError, TypeError) as e:
                    skip_reasons.append(f"#{i}: bad structure — {e}")
                    skipped += 1
            conn.commit()
    except sqlite3.Error as e:
        return {"imported": imported, "skipped": skipped, "error": str(e), "skip_reasons": skip_reasons}
    return {"imported": imported, "skipped": skipped, "skip_reasons": skip_reasons}


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
