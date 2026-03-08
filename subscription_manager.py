#!/usr/bin/env python3
"""
GuardianStreams Subscription Manager
Billing management CLI for streaming service subscriptions.
"""

__version__ = "2.0.0"

# ============================================================
# IMPORTS
# ============================================================
import json
import logging
import os
import re
import smtplib
import sqlite3
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple

import requests
from colorama import Fore, Style, init

init()


# ============================================================
# CONSTANTS
# ============================================================

DATE_FORMAT = "%m-%d-%Y"
DATE_INPUT_FORMATS = ("%m-%d-%y", "%m-%d-%Y")

ACCOUNT_PREFIX = "dtv."
ACCOUNT_PADDING = 3

DELINQUENT_DAYS = 30
INITIAL_DAYS = 5
PAID_DAYS = 21

RISK_IMMINENT_DAYS = 4
RISK_GENERAL_MIN = 4
RISK_ENHANCED_MIN = 5
RISK_HIGH = 7
RISK_MAX_LATE = 3

MAX_INPUT_ERRORS = 3
MAX_PAYMENT_HISTORY = 5
DISCORD_MAX_CHARS = 1999
NOTIFY_TIMEOUT = 10

STATUS_COLORS: Dict[str, str] = {
    "initial": Fore.WHITE,
    "paid": Fore.GREEN,
    "delinquent": Fore.RED,
    "pending": Fore.YELLOW,
    "active": Fore.CYAN,
}

STATUS_SORT_ORDER: Dict[str, int] = {
    "paid": 1,
    "active": 2,
    "pending": 3,
    "initial": 4,
    "delinquent": 5,
}

ALLOWED_EDIT_FIELDS = {"username", "email", "phone", "due_date", "package", "price"}


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG: Dict = {
    "PACKAGES": {
        "0": ("OnDemand", 10),
        "1": ("Grandfather", 25),
        "2": ("Silver", 30),
        "3": ("Gold", 40),
        "4": ("Platinum", 50),
        "5": ("Custom", None),
    },
    "DB_NAME": "OnDemand_subscriptions.db",
    "NOTIFICATIONS": {
        "EMAIL": {
            "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            "smtp_server": os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "from_email": os.getenv("EMAIL_FROM", "billing@guardianstreams.com"),
            "from_name": os.getenv("EMAIL_FROM_NAME", "GuardianStreams Billing"),
        },
        "TELEGRAM": {
            "enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        },
        "DISCORD": {
            "enabled": os.getenv("DISCORD_ENABLED", "false").lower() == "true",
            "webhook_url": os.getenv("DISCORD_WEBHOOK_URL"),
        },
        "PUSHOVER": {
            "enabled": os.getenv("PUSHOVER_ENABLED", "false").lower() == "true",
            "api_token": os.getenv("PUSHOVER_API_TOKEN"),
            "user_key": os.getenv("PUSHOVER_USER_KEY"),
        },
    },
    "RATE_LIMITING": {
        "delay_between_notifications": 15,
        "delay_between_customers": 25,
        "max_retries": 3,
    },
}


# ============================================================
# LOGGING SETUP
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

_email_logger = logging.getLogger("email_notifications")
_email_logger.setLevel(logging.DEBUG)
_email_handler = logging.FileHandler("email_detailed.log")
_email_handler.setLevel(logging.DEBUG)
_email_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
_email_logger.addHandler(_email_handler)


# ============================================================
# DATABASE
# ============================================================

def init_db() -> None:
    """Create tables and run schema migrations if needed."""
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute("""
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
                    creation_date TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS billing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id TEXT,
                    payment_date TEXT,
                    amount REAL,
                    status TEXT CHECK(status IN ('paid','failed','grace_period')),
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
                )
            """)
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_billing_sub "
                "ON billing_history(subscription_id)"
            )
            # Migrations: add columns that may be missing in older databases
            c.execute("PRAGMA table_info(subscriptions)")
            existing = {row[1] for row in c.fetchall()}
            if "creation_date" not in existing:
                c.execute("ALTER TABLE subscriptions ADD COLUMN creation_date TEXT")
            if "grace_period_used" not in existing:
                c.execute(
                    "ALTER TABLE subscriptions ADD COLUMN grace_period_used INTEGER DEFAULT 0"
                )
            conn.commit()
            logging.info("Database ready")
    except sqlite3.Error as e:
        logging.error(f"Database init failed: {e}")
        raise


def generate_account_id() -> str:
    """Return the next unused dtv.NNN account ID."""
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM subscriptions WHERE id LIKE 'dtv.%'")
            existing = {row[0] for row in c.fetchall()}
        i = 0
        while True:
            candidate = f"{ACCOUNT_PREFIX}{i:0{ACCOUNT_PADDING}d}"
            if candidate not in existing:
                return candidate
            i += 1
    except sqlite3.Error as e:
        logging.error(f"Error generating account ID: {e}")
        return f"{ACCOUNT_PREFIX}{'0' * ACCOUNT_PADDING}"


def determine_status(subscription: Dict, latest_payment: Optional[Dict]) -> str:
    """Compute display status from a subscription record and its latest payment."""
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


def _fetch_subscriptions(cursor) -> List[Dict]:
    """
    Fetch all subscriptions with resolved display status in a single query.
    Uses a window function to get each customer's latest payment without N+1 queries.
    """
    cursor.execute("""
        SELECT s.id, s.username, s.email, s.phone, s.package, s.price,
               s.due_date, s.status, s.creation_date,
               lp.payment_date, lp.status AS latest_payment_status
        FROM subscriptions s
        LEFT JOIN (
            SELECT subscription_id, payment_date, status,
                   ROW_NUMBER() OVER (
                       PARTITION BY subscription_id ORDER BY payment_date DESC
                   ) AS rn
            FROM billing_history
        ) lp ON lp.subscription_id = s.id AND lp.rn = 1
    """)
    result = []
    for row in cursor.fetchall():
        sub = {
            "id": row[0], "username": row[1], "email": row[2], "phone": row[3],
            "package": row[4], "price": row[5], "due_date": row[6],
            "status": row[7], "creation_date": row[8],
        }
        latest = {"payment_date": row[9], "status": row[10]} if row[9] else None
        sub["display_status"] = determine_status(sub, latest)
        result.append(sub)
    return result


# ============================================================
# VALIDATION HELPERS
# ============================================================

def is_valid_email(email: str) -> bool:
    """Return True if email is blank (optional field) or matches a valid pattern."""
    if not email:
        return True
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_valid_phone(phone: str) -> bool:
    """Return True if phone is blank (optional field) or contains at least 7 digits."""
    if not phone:
        return True
    return len(re.sub(r"\D", "", phone)) >= 7


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse MM-DD-YY or MM-DD-YYYY. Returns a datetime or None if invalid."""
    if not date_str:
        return None
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


# ============================================================
# NOTIFICATION SYSTEM
# ============================================================

def _log_email(subject: str, body: str, recipient: str) -> None:
    """Log email content to email_detailed.log with basic redaction."""
    redacted = body
    for term in ("password", "credit card", "cvv"):
        redacted = redacted.replace(term, "[REDACTED]")
    _email_logger.info(
        f"Email -> {recipient} | Subject: {subject} | "
        f"Preview: {redacted[:200]} | Chars: {len(body)}"
    )


def send_email(
    to_email: str, subject: str, body: str, html_body: Optional[str] = None
) -> bool:
    """Send an email via SMTP. Logs content before sending. Returns True on success."""
    cfg = CONFIG["NOTIFICATIONS"]["EMAIL"]
    if not cfg["enabled"]:
        return False
    if not all([cfg["username"], cfg["password"], to_email]):
        logging.error("Missing email credentials or recipient address")
        return False

    _log_email(subject, body, to_email)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{cfg['from_name']} <{cfg['from_email']}>"
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"], timeout=NOTIFY_TIMEOUT) as server:
            server.starttls()
            server.login(cfg["username"], cfg["password"])
            server.send_message(msg)

        logging.info(f"Email sent -> {to_email}")
        return True
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error -> {to_email}: {e}")
        return False
    except Exception as e:
        logging.error(f"Email error -> {to_email}: {e}", exc_info=True)
        return False


def send_notification(
    service: str, message: str, title: Optional[str] = None
) -> bool:
    """Send a push notification via Telegram, Discord, or Pushover."""
    cfg = CONFIG["NOTIFICATIONS"].get(service.upper())
    if cfg is None or not cfg["enabled"]:
        return False

    try:
        if service == "telegram":
            token, chat_id = cfg.get("bot_token"), cfg.get("chat_id")
            if not token or not chat_id:
                logging.error("Missing Telegram credentials")
                return False
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                timeout=NOTIFY_TIMEOUT,
            )
            if r.status_code != 200 or not r.json().get("ok"):
                logging.error(f"Telegram error: {r.status_code} {r.text}")
                return False
            return True

        if service == "discord":
            url = cfg.get("webhook_url")
            if not url:
                logging.error("Missing Discord webhook URL")
                return False
            r = requests.post(
                url,
                json={
                    "content": message[:DISCORD_MAX_CHARS],
                    "username": "GuardianStreams Billing",
                },
                timeout=NOTIFY_TIMEOUT,
            )
            if r.status_code != 204:
                logging.error(f"Discord error: {r.status_code} {r.text}")
                return False
            return True

        if service == "pushover":
            token, user_key = cfg.get("api_token"), cfg.get("user_key")
            if not token or not user_key:
                logging.error("Missing Pushover credentials")
                return False
            r = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": token,
                    "user": user_key,
                    "message": message,
                    "title": title or "GuardianStreams",
                },
                timeout=NOTIFY_TIMEOUT,
            )
            if r.status_code != 200:
                logging.error(f"Pushover error: {r.status_code} {r.text}")
                return False
            return True

    except requests.RequestException as e:
        logging.error(f"{service} notification error: {e}")

    return False


def send_with_retry(
    service: str,
    message: str,
    title: Optional[str] = None,
    recipient: Optional[str] = None,
) -> bool:
    """Send a notification with exponential backoff on failure."""
    retries = CONFIG["RATE_LIMITING"]["max_retries"]
    delay = CONFIG["RATE_LIMITING"]["delay_between_notifications"]

    for attempt in range(retries):
        try:
            if service == "email" and recipient:
                ok = send_email(recipient, title or "GuardianStreams Notification", message)
            elif service in ("telegram", "discord", "pushover"):
                ok = send_notification(service, message, title)
            else:
                return False

            if ok:
                logging.info(f"{service} sent on attempt {attempt + 1}")
                return True
        except Exception as e:
            logging.warning(f"{service} attempt {attempt + 1}/{retries} failed: {e}")

        if attempt < retries - 1:
            time.sleep(delay * (attempt + 1))

    logging.error(f"All {retries} attempts failed for {service}")
    return False


def notify_all(message: str, title: Optional[str] = None) -> None:
    """Fire a notification to all enabled push channels."""
    for svc in ("telegram", "discord", "pushover"):
        send_notification(svc, message, title)


def test_telegram_config() -> bool:
    """Validate Telegram credentials and send a test message."""
    cfg = CONFIG["NOTIFICATIONS"]["TELEGRAM"]
    print(f"{Fore.CYAN}Testing Telegram configuration...{Style.RESET_ALL}")

    if not cfg["enabled"]:
        print(f"{Fore.RED}Telegram disabled - set TELEGRAM_ENABLED=true{Style.RESET_ALL}")
        return False
    if not cfg.get("bot_token"):
        print(f"{Fore.RED}Missing TELEGRAM_BOT_TOKEN{Style.RESET_ALL}")
        return False
    if not cfg.get("chat_id"):
        print(f"{Fore.RED}Missing TELEGRAM_CHAT_ID{Style.RESET_ALL}")
        return False

    print(f"{Fore.GREEN}Credentials present. Sending test message...{Style.RESET_ALL}")
    ok = send_notification("telegram", "🧪 Test message from GuardianStreams Billing", "Test")
    if ok:
        print(f"{Fore.GREEN}Test message sent successfully.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Test failed - check logs for details.{Style.RESET_ALL}")
    return ok


# ============================================================
# CUSTOMER MANAGEMENT
# ============================================================

def _print_subscription_rows(subs: List[Dict]) -> None:
    """Print a list of subscription dicts with color-coded status."""
    for s in subs:
        color = STATUS_COLORS.get(s["display_status"], Fore.WHITE)
        print(
            f"{Fore.WHITE}ID: {s['id']}  User: {s['username']}  "
            f"Email: {s['email'] or 'N/A'}  Phone: {s['phone'] or 'N/A'}  "
            f"Pkg: {s['package']}  Price: ${s['price']}  "
            f"Due: {s['due_date']}  "
            f"Status: {color}{s['display_status']}{Style.RESET_ALL}"
        )


def add_user() -> None:
    """Interactively add a new customer. Aborts after MAX_INPUT_ERRORS failures."""
    errors = 0

    while errors < MAX_INPUT_ERRORS:
        print(f"{Fore.YELLOW}Username: {Style.RESET_ALL}", end="")
        username = input().strip()
        if not username:
            errors += 1
            print(f"{Fore.MAGENTA}Username required. {MAX_INPUT_ERRORS - errors} attempt(s) left.{Style.RESET_ALL}")
            continue

        print(f"{Fore.YELLOW}Email (optional): {Style.RESET_ALL}", end="")
        email = input().strip()
        if email and not is_valid_email(email):
            errors += 1
            print(f"{Fore.MAGENTA}Invalid email format. {MAX_INPUT_ERRORS - errors} attempt(s) left.{Style.RESET_ALL}")
            continue

        print(f"{Fore.YELLOW}Phone (optional): {Style.RESET_ALL}", end="")
        phone = input().strip()
        if phone and not is_valid_phone(phone):
            errors += 1
            print(f"{Fore.MAGENTA}Invalid phone (min 7 digits). {MAX_INPUT_ERRORS - errors} attempt(s) left.{Style.RESET_ALL}")
            continue

        print(f"\n{Fore.CYAN}Available packages:{Style.RESET_ALL}")
        for k, (name, price) in CONFIG["PACKAGES"].items():
            label = f"${price}" if price else "custom"
            print(f"{Fore.WHITE}  {k}: {name} ({label}){Style.RESET_ALL}")

        print(f"{Fore.YELLOW}Package (0-5): {Style.RESET_ALL}", end="")
        pkg_id = input().strip()
        if pkg_id not in CONFIG["PACKAGES"]:
            errors += 1
            print(f"{Fore.MAGENTA}Invalid package. {MAX_INPUT_ERRORS - errors} attempt(s) left.{Style.RESET_ALL}")
            continue

        pkg_name, pkg_price = CONFIG["PACKAGES"][pkg_id]
        if pkg_name == "Custom":
            print(f"{Fore.YELLOW}Custom price: {Style.RESET_ALL}", end="")
            try:
                pkg_price = float(input().strip())
                if pkg_price <= 0:
                    raise ValueError
            except ValueError:
                errors += 1
                print(f"{Fore.MAGENTA}Price must be a positive number. {MAX_INPUT_ERRORS - errors} attempt(s) left.{Style.RESET_ALL}")
                continue

        print(f"{Fore.YELLOW}Due date (MM-DD-YY or MM-DD-YYYY): {Style.RESET_ALL}", end="")
        due = parse_date(input().strip())
        if not due:
            errors += 1
            print(f"{Fore.MAGENTA}Invalid date format. {MAX_INPUT_ERRORS - errors} attempt(s) left.{Style.RESET_ALL}")
            continue

        acc_id = generate_account_id()
        today = datetime.now().strftime(DATE_FORMAT)
        due_str = due.strftime(DATE_FORMAT)

        try:
            with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
                conn.execute(
                    "INSERT INTO subscriptions "
                    "(id, username, email, phone, package, price, due_date, status, creation_date) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 'initial', ?)",
                    (acc_id, username, email or None, phone or None, pkg_name, pkg_price, due_str, today),
                )
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"DB error adding user: {e}")
            notify_all(f"⚠️ DB error adding user: {e}")
            print(f"{Fore.RED}Database error - user not added.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}User added. Account ID: {acc_id}{Style.RESET_ALL}")
        logging.info(
            f"Added {acc_id}: {username} | {pkg_name} ${pkg_price:.2f} | due {due_str}"
        )
        notify_all(
            f"✅ New user added\nID: {acc_id}\nName: {username}\n"
            f"Package: {pkg_name}\nPrice: ${pkg_price:.2f}\nDue: {due_str}\nStatus: initial"
        )
        return

    print(f"{Fore.RED}Too many invalid inputs. Cancelled.{Style.RESET_ALL}")
    logging.warning("add_user aborted: too many validation errors")


def view_users() -> None:
    """Display all customers with a sort option."""
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            subs = _fetch_subscriptions(conn.cursor())

        if not subs:
            print(f"{Fore.MAGENTA}No subscriptions found.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Sort by:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  1. Account ID          5. Due date (latest){Style.RESET_ALL}")
        print(f"{Fore.WHITE}  2. Username A-Z        6. Status{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  3. Username Z-A        7. Price (lowest){Style.RESET_ALL}")
        print(f"{Fore.WHITE}  4. Due date (earliest) 8. Price (highest){Style.RESET_ALL}")
        print(f"{Fore.WHITE}  9. No sort (DB order){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Choice (1-9): {Style.RESET_ALL}", end="")
        choice = input().strip()

        if choice == "1":
            subs.sort(key=lambda x: x["id"])
        elif choice == "2":
            subs.sort(key=lambda x: x["username"].lower())
        elif choice == "3":
            subs.sort(key=lambda x: x["username"].lower(), reverse=True)
        elif choice == "4":
            subs.sort(key=lambda x: datetime.strptime(x["due_date"], DATE_FORMAT))
        elif choice == "5":
            subs.sort(key=lambda x: datetime.strptime(x["due_date"], DATE_FORMAT), reverse=True)
        elif choice == "6":
            subs.sort(key=lambda x: STATUS_SORT_ORDER.get(x["display_status"], 6))
        elif choice == "7":
            subs.sort(key=lambda x: x["price"])
        elif choice == "8":
            subs.sort(key=lambda x: x["price"], reverse=True)

        print(f"\n{Fore.CYAN}Subscriptions ({len(subs)} total):{Style.RESET_ALL}")
        _print_subscription_rows(subs)
        print(f"\n{Fore.CYAN}Total subscriptions: {len(subs)}{Style.RESET_ALL}")
        logging.info(f"Viewed all subscriptions (sort={choice})")

    except sqlite3.Error as e:
        logging.error(f"DB error viewing users: {e}")
        print(f"{Fore.RED}Database error.{Style.RESET_ALL}")


def view_users_with_filters() -> None:
    """Display customers with a status/package/date filter, then sort."""
    try:
        print(f"\n{Fore.CYAN}Filter by:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  1. All users          4. Pending{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  2. Paid               5. Due in next 7 days{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  3. Delinquent         6. Package type{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Choice (1-6): {Style.RESET_ALL}", end="")
        flt = input().strip()

        pkg_filter: Optional[str] = None
        if flt == "6":
            print(f"\n{Fore.CYAN}Packages:{Style.RESET_ALL}")
            for k, (name, _) in CONFIG["PACKAGES"].items():
                print(f"{Fore.WHITE}  {k}: {name}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Package name: {Style.RESET_ALL}", end="")
            pkg_filter = input().strip()

        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            subs = _fetch_subscriptions(conn.cursor())

        status_map = {"2": "paid", "3": "delinquent", "4": "pending"}
        if flt in status_map:
            subs = [s for s in subs if s["display_status"] == status_map[flt]]
        elif flt == "5":
            now = datetime.now()
            cutoff = now + timedelta(days=7)
            filtered = []
            for s in subs:
                try:
                    due = datetime.strptime(s["due_date"], DATE_FORMAT)
                    if now <= due <= cutoff:
                        filtered.append(s)
                except ValueError:
                    continue
            subs = filtered
        elif flt == "6" and pkg_filter:
            subs = [s for s in subs if s["package"] == pkg_filter]

        if not subs:
            print(f"{Fore.MAGENTA}No subscriptions match that filter.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Sort by:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  1. Account ID  2. Username A-Z  3. Due date  4. Price{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Choice (1-4): {Style.RESET_ALL}", end="")
        srt = input().strip()

        if srt == "1":
            subs.sort(key=lambda x: x["id"])
        elif srt == "2":
            subs.sort(key=lambda x: x["username"].lower())
        elif srt == "3":
            subs.sort(key=lambda x: datetime.strptime(x["due_date"], DATE_FORMAT))
        elif srt == "4":
            subs.sort(key=lambda x: x["price"])

        print(f"\n{Fore.CYAN}Results ({len(subs)}):{Style.RESET_ALL}")
        _print_subscription_rows(subs)
        logging.info(f"Filtered view: filter={flt}, sort={srt}")

    except sqlite3.Error as e:
        logging.error(f"DB error in filtered view: {e}")
        print(f"{Fore.RED}Database error.{Style.RESET_ALL}")


def view_subscription_by_id() -> None:
    """Display full details and payment history for a single account."""
    print(f"{Fore.YELLOW}Account ID digits (e.g. 001): {Style.RESET_ALL}", end="")
    acc_id = f"{ACCOUNT_PREFIX}{input().strip().zfill(ACCOUNT_PADDING)}"

    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, username, email, phone, package, price, due_date, status, creation_date "
                "FROM subscriptions WHERE id = ?",
                (acc_id,),
            )
            row = c.fetchone()
            if not row:
                print(f"{Fore.MAGENTA}Account {acc_id} not found.{Style.RESET_ALL}")
                return

            sub = {
                "id": row[0], "username": row[1], "email": row[2], "phone": row[3],
                "package": row[4], "price": row[5], "due_date": row[6],
                "status": row[7], "creation_date": row[8],
            }
            c.execute(
                "SELECT payment_date, status FROM billing_history "
                "WHERE subscription_id = ? ORDER BY payment_date DESC LIMIT 1",
                (acc_id,),
            )
            lp_row = c.fetchone()
            latest = {"payment_date": lp_row[0], "status": lp_row[1]} if lp_row else None
            display = determine_status(sub, latest)
            color = STATUS_COLORS.get(display, Fore.WHITE)

            c.execute(
                "SELECT SUM(amount) FROM billing_history "
                "WHERE subscription_id = ? AND status = 'paid'",
                (acc_id,),
            )
            total_paid = c.fetchone()[0] or 0.0

            c.execute(
                "SELECT payment_date, amount, status FROM billing_history "
                "WHERE subscription_id = ? ORDER BY payment_date DESC LIMIT ?",
                (acc_id, MAX_PAYMENT_HISTORY),
            )
            payments = c.fetchall()

        print(f"\n{Fore.CYAN}[ {acc_id} ]{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Username    : {sub['username']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Email       : {sub['email'] or 'N/A'}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Phone       : {sub['phone'] or 'N/A'}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Package     : {sub['package']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Price       : ${sub['price']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Due Date    : {sub['due_date']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Status      : {color}{display}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Created     : {sub['creation_date'] or 'N/A'}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Total Paid  : ${total_paid:.2f}{Style.RESET_ALL}")

        if payments:
            print(f"\n{Fore.CYAN}Recent Payments:{Style.RESET_ALL}")
            for pdate, amount, pstatus in payments:
                print(f"{Fore.WHITE}  {pdate}: ${amount:.2f} - {pstatus}{Style.RESET_ALL}")

        logging.info(f"Viewed subscription {acc_id}")

    except sqlite3.Error as e:
        logging.error(f"DB error viewing {acc_id}: {e}")
        print(f"{Fore.RED}Database error.{Style.RESET_ALL}")


def edit_customer() -> None:
    """Edit customer fields. Press Enter to keep an existing value."""
    print(f"{Fore.YELLOW}Account ID digits (e.g. 001): {Style.RESET_ALL}", end="")
    acc_id = f"{ACCOUNT_PREFIX}{input().strip().zfill(ACCOUNT_PADDING)}"

    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT username, email, phone, due_date, package, price "
                "FROM subscriptions WHERE id = ?",
                (acc_id,),
            )
            row = c.fetchone()
            if not row:
                print(f"{Fore.MAGENTA}Account {acc_id} not found.{Style.RESET_ALL}")
                return

            cur_user, cur_email, cur_phone, cur_due, cur_pkg, cur_price = row

            print(f"\n{Fore.CYAN}Current details for {acc_id}:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  Username : {cur_user}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  Email    : {cur_email or 'N/A'}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  Phone    : {cur_phone or 'N/A'}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  Due date : {cur_due}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}  Package  : {cur_pkg}  Price: ${cur_price}{Style.RESET_ALL}")

            print(f"{Fore.YELLOW}New username (Enter=keep): {Style.RESET_ALL}", end="")
            username = input().strip() or cur_user

            print(f"{Fore.YELLOW}New email (Enter=keep): {Style.RESET_ALL}", end="")
            email_in = input().strip()
            if email_in and not is_valid_email(email_in):
                print(f"{Fore.MAGENTA}Invalid email format.{Style.RESET_ALL}")
                return
            email = email_in or cur_email

            print(f"{Fore.YELLOW}New phone (Enter=keep): {Style.RESET_ALL}", end="")
            phone_in = input().strip()
            if phone_in and not is_valid_phone(phone_in):
                print(f"{Fore.MAGENTA}Invalid phone number.{Style.RESET_ALL}")
                return
            phone = phone_in or cur_phone

            print(f"{Fore.YELLOW}New due date (Enter=keep): {Style.RESET_ALL}", end="")
            due_in = input().strip()
            if due_in:
                parsed = parse_date(due_in)
                if not parsed:
                    print(f"{Fore.MAGENTA}Invalid date format.{Style.RESET_ALL}")
                    return
                due_date = parsed.strftime(DATE_FORMAT)
            else:
                due_date = cur_due

            pkg_name, price = cur_pkg, cur_price
            print(f"{Fore.YELLOW}Change package? (y/n): {Style.RESET_ALL}", end="")
            if input().strip().lower() == "y":
                print(f"\n{Fore.CYAN}Packages:{Style.RESET_ALL}")
                for k, (name, p) in CONFIG["PACKAGES"].items():
                    print(f"{Fore.WHITE}  {k}: {name} (${p if p else 'custom'}){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Package (0-5): {Style.RESET_ALL}", end="")
                pkg_id = input().strip()
                if pkg_id not in CONFIG["PACKAGES"]:
                    print(f"{Fore.MAGENTA}Invalid package.{Style.RESET_ALL}")
                    return
                pkg_name, pkg_price = CONFIG["PACKAGES"][pkg_id]
                if pkg_name == "Custom":
                    print(f"{Fore.YELLOW}Custom price: {Style.RESET_ALL}", end="")
                    try:
                        price = float(input().strip())
                        if price <= 0:
                            raise ValueError
                    except ValueError:
                        print(f"{Fore.MAGENTA}Price must be a positive number.{Style.RESET_ALL}")
                        return
                else:
                    price = pkg_price

            updates = []
            if username != cur_user:
                updates.append(("username", username))
            if (email or None) != cur_email:
                updates.append(("email", email or None))
            if (phone or None) != cur_phone:
                updates.append(("phone", phone or None))
            if due_date != cur_due:
                updates.append(("due_date", due_date))
            if pkg_name != cur_pkg or price != cur_price:
                updates.extend([("package", pkg_name), ("price", price)])

            if not updates:
                print(f"{Fore.MAGENTA}No changes made.{Style.RESET_ALL}")
                return

            for field, value in updates:
                if field not in ALLOWED_EDIT_FIELDS:
                    continue
                c.execute(f"UPDATE subscriptions SET {field} = ? WHERE id = ?", (value, acc_id))
            conn.commit()

            print(f"{Fore.GREEN}Customer updated.{Style.RESET_ALL}")
            logging.info(f"Updated {acc_id}: {updates}")
            notify_all(
                f"✏️ Customer updated\nID: {acc_id}\nName: {username}\n"
                f"Package: {pkg_name}\nPrice: ${price:.2f}\nDue: {due_date}"
            )

    except sqlite3.Error as e:
        logging.error(f"DB error editing {acc_id}: {e}")
        print(f"{Fore.RED}Database error.{Style.RESET_ALL}")


# ============================================================
# PAYMENT SYSTEM
# ============================================================

def add_payment_record(subscription_id: str, amount: float, status: str) -> bool:
    """Insert a payment record into billing_history. Returns True on success."""
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            conn.execute(
                "INSERT INTO billing_history (subscription_id, payment_date, amount, status) "
                "VALUES (?, ?, ?, ?)",
                (subscription_id, datetime.now().strftime(DATE_FORMAT), amount, status),
            )
            conn.commit()
        logging.info(f"Payment recorded {subscription_id}: ${amount:.2f} ({status})")
        notify_all(
            f"💰 Payment recorded\nAccount: {subscription_id}\n"
            f"Amount: ${amount:.2f}\nStatus: {status}"
        )
        return True
    except sqlite3.Error as e:
        logging.error(f"Error recording payment for {subscription_id}: {e}")
        notify_all(f"⚠️ Payment record error for {subscription_id}: {e}")
        return False


def record_payment() -> None:
    """Interactively record a payment for a customer."""
    print(f"{Fore.YELLOW}Account ID digits (e.g. 001): {Style.RESET_ALL}", end="")
    acc_id = f"{ACCOUNT_PREFIX}{input().strip().zfill(ACCOUNT_PADDING)}"

    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT username, price, due_date FROM subscriptions WHERE id = ?", (acc_id,)
            )
            row = c.fetchone()
            if not row:
                print(f"{Fore.MAGENTA}Account {acc_id} not found.{Style.RESET_ALL}")
                notify_all(f"⚠️ Payment failed: account {acc_id} not found")
                return

            username, price, current_due_str = row
            print(f"{Fore.CYAN}Recording payment for {username} ({acc_id}){Style.RESET_ALL}")
            print(f"{Fore.WHITE}Expected amount: ${price}{Style.RESET_ALL}")

            print(f"{Fore.YELLOW}Amount (Enter=${price}): {Style.RESET_ALL}", end="")
            amount_in = input().strip()
            if not amount_in:
                amount = float(price)
            else:
                try:
                    amount = float(amount_in)
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    print(f"{Fore.MAGENTA}Invalid amount.{Style.RESET_ALL}")
                    return

            print(f"\n{Fore.CYAN}Payment status:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  1. Paid{Style.RESET_ALL}")
            print(f"{Fore.RED}  2. Failed{Style.RESET_ALL}")
            print(f"{Fore.BLUE}  3. Grace Period{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Choice (1-3): {Style.RESET_ALL}", end="")

            status_map = {"1": "paid", "2": "failed", "3": "grace_period"}
            status = status_map.get(input().strip())
            if not status:
                print(f"{Fore.MAGENTA}Invalid choice.{Style.RESET_ALL}")
                return

            if not add_payment_record(acc_id, amount, status):
                print(f"{Fore.RED}Could not record payment. Check logs.{Style.RESET_ALL}")
                return

            if status == "paid":
                print(f"\n{Fore.CYAN}New due date:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}  1. +30 days  2. +60 days  3. +90 days  4. Custom{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Choice (1-4): {Style.RESET_ALL}", end="")
                date_choice = input().strip()

                try:
                    current_due = datetime.strptime(current_due_str, DATE_FORMAT)
                    if date_choice == "1":
                        next_due = current_due + timedelta(days=30)
                    elif date_choice == "2":
                        next_due = current_due + timedelta(days=60)
                    elif date_choice == "3":
                        next_due = current_due + timedelta(days=90)
                    elif date_choice == "4":
                        print(f"{Fore.YELLOW}Custom date (MM-DD-YY or MM-DD-YYYY): {Style.RESET_ALL}", end="")
                        next_due = parse_date(input().strip())
                        if not next_due:
                            print(f"{Fore.MAGENTA}Invalid date format.{Style.RESET_ALL}")
                            return
                    else:
                        print(f"{Fore.MAGENTA}Invalid option.{Style.RESET_ALL}")
                        return

                    next_due_str = next_due.strftime(DATE_FORMAT)
                    c.execute(
                        "UPDATE subscriptions SET due_date = ?, status = 'paid' WHERE id = ?",
                        (next_due_str, acc_id),
                    )
                    conn.commit()

                    print(f"{Fore.GREEN}Updated. New due date: {next_due_str}{Style.RESET_ALL}")
                    logging.info(f"{acc_id} paid - new due date: {next_due_str}")
                    notify_all(
                        f"💰 Payment successful\nAccount: {acc_id}\nName: {username}\n"
                        f"Amount: ${amount:.2f}\nNew Due: {next_due_str}\nStatus: paid"
                    )
                except (ValueError, TypeError) as e:
                    logging.error(f"Due date update failed for {acc_id}: {e}")
                    print(f"{Fore.RED}Could not update due date.{Style.RESET_ALL}")

            elif status == "grace_period":
                c.execute(
                    "UPDATE subscriptions SET grace_period_used = 1, status = 'pending' WHERE id = ?",
                    (acc_id,),
                )
                conn.commit()
                print(f"{Fore.YELLOW}Grace period activated for {acc_id}.{Style.RESET_ALL}")
                logging.info(f"{acc_id} grace period activated")
                notify_all(
                    f"⚠️ Grace period activated\nAccount: {acc_id}\n"
                    f"Name: {username}\nAmount Due: ${amount:.2f}\nStatus: pending"
                )
            # status == "failed": payment logged, no subscription update needed

    except sqlite3.Error as e:
        logging.error(f"DB error recording payment for {acc_id}: {e}")
        print(f"{Fore.RED}Database error.{Style.RESET_ALL}")


# ============================================================
# IMPORT / EXPORT
# ============================================================

def export_to_json() -> None:
    """Export all subscriptions to GuardianStreams_export.json."""
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, username, email, phone, package, price, due_date, status, creation_date "
                "FROM subscriptions"
            )
            rows = c.fetchall()

        data = [
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

        with open("GuardianStreams_export.json", "w") as f:
            json.dump(data, f, indent=4)

        print(f"{Fore.GREEN}Exported {len(data)} records to GuardianStreams_export.json{Style.RESET_ALL}")
        logging.info(f"Exported {len(data)} subscriptions to JSON")
        notify_all("📤 Data exported to JSON")

    except (sqlite3.Error, OSError) as e:
        logging.error(f"Export failed: {e}")
        print(f"{Fore.RED}Export failed: {e}{Style.RESET_ALL}")


def import_from_json() -> None:
    """Import subscriptions from a user-specified JSON file."""
    print(f"{Fore.YELLOW}JSON filename: {Style.RESET_ALL}", end="")
    filename = input().strip()

    try:
        with open(filename) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logging.error(f"Import read error: {e}")
        print(f"{Fore.RED}Could not read file: {e}{Style.RESET_ALL}")
        return

    if not isinstance(data, list):
        print(f"{Fore.MAGENTA}Invalid format - expected a JSON array.{Style.RESET_ALL}")
        return

    count = 0
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
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
                        logging.warning("Skipping invalid record: missing required fields")
                        print(f"{Fore.MAGENTA}Skipped invalid record.{Style.RESET_ALL}")
                        continue

                    c.execute(
                        "INSERT OR REPLACE INTO subscriptions "
                        "(id, username, email, phone, package, price, due_date, status, creation_date) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, 'initial', ?)",
                        (acc_id, username, email, phone, plan, price, due_date, creation_date),
                    )
                    count += 1
                except (KeyError, ValueError) as e:
                    logging.warning(f"Skipping malformed record: {e}")
                    print(f"{Fore.MAGENTA}Skipped malformed record: {e}{Style.RESET_ALL}")
            conn.commit()

    except sqlite3.Error as e:
        logging.error(f"DB error during import: {e}")
        print(f"{Fore.RED}Database error during import.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}Imported {count} records.{Style.RESET_ALL}")
    logging.info(f"Imported {count} subscriptions from {filename}")
    notify_all(f"📥 Imported {count} records from JSON")


# ============================================================
# RISK PREDICTION
# ============================================================

def get_customer_data() -> List[Dict]:
    """
    Fetch all customers with payment stats in a single query.
    Returns late payment counts and latest payment info via JOINs — no N+1.
    """
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
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
            """)
            rows = c.fetchall()

        customers = []
        for row in rows:
            acc_id, username, email, phone, due_str, status, grace, created, \
                lp_date, lp_status, late = row

            try:
                due_dt = datetime.strptime(due_str, DATE_FORMAT)
            except (ValueError, TypeError):
                logging.warning(f"Skipping {acc_id}: invalid due_date {due_str!r}")
                continue

            sub = {"id": acc_id, "due_date": due_str, "status": status, "creation_date": created}
            latest = {"payment_date": lp_date, "status": lp_status} if lp_date else None
            display = determine_status(sub, latest)

            customers.append({
                "id": acc_id,
                "username": username,
                "email": email,
                "phone": phone,
                "due_date": due_dt,
                "status": display,
                "grace_period_used": bool(grace),
                "late_payments": int(late),
            })

        logging.info(f"Loaded {len(customers)} customers for analysis")
        return customers

    except sqlite3.Error as e:
        logging.error(f"DB error loading customer data: {e}")
        notify_all(f"⚠️ DB error loading customer data: {e}")
        return []


def calculate_risk_score(customer: Dict) -> Tuple[int, List[str]]:
    """Calculate risk score and reasons for a customer. Used by both risk predictors."""
    now = datetime.now()
    days = (customer["due_date"] - now).days
    score, reasons = 0, []

    if days <= 7:
        score += min(max(7 - days, 1), 7)
        label = f"{days} day(s)" if days >= 0 else f"{abs(days)} day(s) overdue"
        reasons.append(f"Due in {label}")

    if customer["late_payments"] > 0:
        score += 3 * min(customer["late_payments"], RISK_MAX_LATE)
        reasons.append(f"{customer['late_payments']} late payment(s)")

    if customer["grace_period_used"]:
        score += 2
        reasons.append("Used grace period")

    return score, reasons


def suggest_actions(customer: Dict, score: int) -> List[str]:
    """Return suggested actions based on risk score and customer contact info."""
    actions: List[str] = []
    if score >= RISK_HIGH:
        actions.append("Send urgent reminder via email or Telegram")
        if customer.get("email"):
            actions.append(f"Email: {customer['email']}")
        if customer.get("phone"):
            actions.append(f"Call: {customer['phone']}")
    else:
        actions.append("Send friendly reminder via Telegram")
    return actions


def predict_risky_customers() -> None:
    """General risk model: flag customers due within 7 days. Saves to risky_customers.json."""
    print(f"{Fore.CYAN}Running Predictive Billing Assistant...{Style.RESET_ALL}")
    notify_all("🤖 Starting AI risk prediction")

    predictions = []

    for customer in get_customer_data():
        score, reasons = calculate_risk_score(customer)
        if score < RISK_GENERAL_MIN:
            continue

        risk_level = "high" if score >= RISK_HIGH else "medium"
        predictions.append({
            "id": customer["id"],
            "username": customer["username"],
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
            "suggested_actions": suggest_actions(customer, score),
            "due_date": customer["due_date"].strftime(DATE_FORMAT),
        })

    output = {
        "predictions": predictions,
        "generated_at": datetime.now().strftime(f"{DATE_FORMAT} %H:%M:%S"),
    }
    try:
        with open("risky_customers.json", "w") as f:
            json.dump(output, f, indent=4)
    except OSError as e:
        logging.error(f"Could not save predictions: {e}")
        print(f"{Fore.RED}Could not save report.{Style.RESET_ALL}")
        return

    if not predictions:
        print(f"{Fore.GREEN}No customers at risk.{Style.RESET_ALL}")
        notify_all("✅ AI analysis: no customers at risk")
        return

    high = sum(1 for p in predictions if p["risk_level"] == "high")
    print(f"\n{Fore.CYAN}Found {len(predictions)} customers at risk:{Style.RESET_ALL}")
    for p in predictions:
        color = Fore.RED if p["risk_level"] == "high" else Fore.YELLOW
        print(f"\n{Fore.WHITE}{p['username']} (ID: {p['id']}){Style.RESET_ALL}")
        print(f"{color}Risk: {p['risk_score']} ({p['risk_level']}){Style.RESET_ALL}")
        print(f"{Fore.BLUE}Reasons: {', '.join(p['reasons'])}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Actions: {', '.join(p['suggested_actions'])}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Due: {p['due_date']}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}Saved to risky_customers.json{Style.RESET_ALL}")
    notify_all(
        f"🔍 AI found {len(predictions)} at-risk customers\n"
        f"High: {high}  Medium: {len(predictions) - high}"
    )


def enhanced_predict_risky_customers() -> None:
    """Focused risk model: customers due within 4 days. Optionally sends reminders."""
    print(f"{Fore.CYAN}Running Enhanced Payment Risk Predictor...{Style.RESET_ALL}")

    now = datetime.now()
    predictions = []

    for customer in get_customer_data():
        days = (customer["due_date"] - now).days
        if days > RISK_IMMINENT_DAYS:
            continue

        score, reasons = 0, []

        score += max(5 - days, 0)
        reasons.append(f"Due in {days} day(s)")

        if customer["late_payments"] > 0:
            score += 2 * min(customer["late_payments"], RISK_MAX_LATE)
            reasons.append(f"{customer['late_payments']} late payment(s)")

        if customer["grace_period_used"]:
            score += 1
            reasons.append("Used grace period")

        if score < RISK_ENHANCED_MIN:
            continue

        risk_level = "high" if score >= RISK_HIGH else "medium"
        predictions.append({
            "id": customer["id"],
            "username": customer["username"],
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
            "due_in_days": days,
            "due_date": customer["due_date"].strftime(DATE_FORMAT),
            "suggested_actions": [
                "Urgent personal contact needed"
                if risk_level == "high"
                else "Send payment reminder"
            ],
        })

    if not predictions:
        print(f"{Fore.GREEN}No customers with imminent payment risk.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Customers needing attention (<={RISK_IMMINENT_DAYS} days):{Style.RESET_ALL}")
    for p in predictions:
        color = Fore.RED if p["risk_level"] == "high" else Fore.YELLOW
        print(f"\n{color}{p['username']} - due in {p['due_in_days']} day(s){Style.RESET_ALL}")
        print(f"  Score  : {p['risk_score']} ({p['risk_level']})")
        print(f"  Reasons: {', '.join(p['reasons'])}")
        print(f"  Action : {p['suggested_actions'][0]}")

    print(f"\n{Fore.YELLOW}Send reminders to these customers? (y/n): {Style.RESET_ALL}", end="")
    if input().strip().lower() == "y":
        send_customer_reminders(predictions)

    save_prediction_report(predictions)


def save_prediction_report(predictions: List[Dict]) -> None:
    """Save an enhanced risk report to a timestamped JSON file."""
    report = {
        "metadata": {
            "report_date": datetime.now().strftime(f"{DATE_FORMAT} %H:%M:%S"),
            "time_window": f"{RISK_IMMINENT_DAYS}_day_imminent",
            "risk_model_version": "2.1",
            "total_customers": len(predictions),
            "high_risk_count": sum(1 for p in predictions if p["risk_level"] == "high"),
            "medium_risk_count": sum(1 for p in predictions if p["risk_level"] == "medium"),
        },
        "customers": sorted(predictions, key=lambda x: (x["due_in_days"], -x["risk_score"])),
        "action_summary": {
            "auto_reminders_recommended": len(predictions),
            "urgent_interventions": sum(1 for p in predictions if p["risk_level"] == "high"),
        },
    }
    filename = f"payment_risk_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    try:
        with open(filename, "w") as f:
            json.dump(report, f, indent=4, default=str)
        print(f"{Fore.GREEN}Report saved to {filename}{Style.RESET_ALL}")
        logging.info(f"Risk report saved: {filename}")
    except OSError as e:
        logging.error(f"Could not save report: {e}")
        print(f"{Fore.RED}Could not save report.{Style.RESET_ALL}")


# ============================================================
# EMAIL REMINDERS
# ============================================================

def create_payment_reminder_email(
    customer_name: str, account_id: str, amount: float, due_date: str, risk_level: str
) -> Tuple[str, str, str]:
    """Build a payment reminder. Returns (subject, plain_text_body, html_body)."""
    subject = f"Payment Reminder - GuardianStreams Account {account_id}"
    urgency = "urgent" if risk_level == "high" else "friendly"

    text_body = (
        f"Dear {customer_name},\n\n"
        f"This is a {urgency} reminder that your GuardianStreams subscription payment is due.\n\n"
        f"Account ID : {account_id}\n"
        f"Amount Due : ${amount:.2f}\n"
        f"Due Date   : {due_date}\n\n"
        f"To avoid service interruption, please submit your payment by the due date.\n\n"
        f"If you have questions or need to discuss payment options, please contact us.\n\n"
        f"Thank you for choosing GuardianStreams!\n\nGuardianStreams Billing Team"
    )

    urgency_style = (
        "color:#e74c3c;font-weight:bold"
        if risk_level == "high"
        else "color:#f39c12;font-weight:bold"
    )
    html_body = f"""<!DOCTYPE html>
<html><head>
  <style>
    body{{font-family:Arial,sans-serif;margin:20px}}
    .header{{background:#2c3e50;color:white;padding:20px;text-align:center}}
    .box{{background:#f8f9fa;padding:15px;border-radius:5px;margin:20px 0}}
    .footer{{background:#ecf0f1;padding:15px;text-align:center;margin-top:20px}}
  </style>
</head><body>
  <div class="header"><h1>GuardianStreams Payment Reminder</h1></div>
  <div style="padding:20px">
    <p>Dear {customer_name},</p>
    <p>This is a <span style="{urgency_style}">{urgency}</span> reminder that your
    subscription payment is due.</p>
    <div class="box">
      <strong>Account ID:</strong> {account_id}<br>
      <strong>Amount Due:</strong> ${amount:.2f}<br>
      <strong>Due Date:</strong> {due_date}
    </div>
    <p>To avoid service interruption, please pay by the due date.</p>
    <p>Thank you for choosing GuardianStreams!</p>
  </div>
  <div class="footer">GuardianStreams Billing Team</div>
</body></html>"""

    return subject, text_body, html_body


def send_customer_reminders(predictions: List[Dict]) -> None:
    """Send payment reminders to a list of at-risk customers."""
    if not predictions:
        print(f"{Fore.YELLOW}No customers to remind.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}Sending reminders to {len(predictions)} customers...{Style.RESET_ALL}")
    success: Dict[str, int] = {"email": 0, "telegram": 0, "discord": 0, "pushover": 0}
    failed: Dict[str, int] = {"email": 0, "telegram": 0, "discord": 0, "pushover": 0}

    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            for i, pred in enumerate(predictions):
                cid = pred["id"]
                c.execute("SELECT email, price FROM subscriptions WHERE id = ?", (cid,))
                row = c.fetchone()
                if not row:
                    print(f"{Fore.MAGENTA}  {cid} not found - skipped.{Style.RESET_ALL}")
                    continue

                email, price = row
                risk_level = "high" if pred["risk_score"] >= RISK_HIGH else "medium"
                admin_msg = (
                    f"📧 Reminder → {pred['username']} ({cid}): "
                    f"${float(price):.2f} due {pred['due_date']}"
                )

                if email and CONFIG["NOTIFICATIONS"]["EMAIL"]["enabled"]:
                    subj, text, html = create_payment_reminder_email(
                        pred["username"], cid, float(price), pred["due_date"], risk_level
                    )
                    if send_with_retry("email", text, subj, email):
                        success["email"] += 1
                        print(f"{Fore.GREEN}  [OK]   Email -> {email}{Style.RESET_ALL}")
                    else:
                        failed["email"] += 1
                        print(f"{Fore.RED}  [FAIL] Email -> {email}{Style.RESET_ALL}")

                for svc in ("telegram", "discord", "pushover"):
                    if CONFIG["NOTIFICATIONS"][svc.upper()]["enabled"]:
                        if send_with_retry(svc, admin_msg, "Payment Reminder"):
                            success[svc] += 1
                        else:
                            failed[svc] += 1

                if i < len(predictions) - 1:
                    delay = CONFIG["RATE_LIMITING"]["delay_between_customers"]
                    print(f"{Fore.YELLOW}  Waiting {delay}s...{Style.RESET_ALL}")
                    time.sleep(delay)

    except sqlite3.Error as e:
        logging.error(f"DB error sending reminders: {e}")
        print(f"{Fore.RED}Database error during reminders.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}Reminder Summary:{Style.RESET_ALL}")
    for svc, n in success.items():
        if n:
            print(f"{Fore.GREEN}  {svc.title()}: {n} sent{Style.RESET_ALL}")
    for svc, n in failed.items():
        if n:
            print(f"{Fore.RED}  {svc.title()}: {n} failed{Style.RESET_ALL}")
    logging.info(f"Reminders - sent: {success} | failed: {failed}")


# ============================================================
# WEB API STUBS
# ============================================================

def add_user_web(
    username: str, email: str, phone: str, package_id: str, due_date: str
) -> Optional[str]:
    """Add a user via web API. Returns the new account ID or None on failure."""
    if package_id not in CONFIG["PACKAGES"]:
        logging.error(f"add_user_web: invalid package_id {package_id!r}")
        return None
    if not parse_date(due_date):
        logging.error(f"add_user_web: invalid due_date {due_date!r}")
        return None

    pkg_name, pkg_price = CONFIG["PACKAGES"][package_id]
    price = float(pkg_price) if pkg_price else 0.0
    acc_id = generate_account_id()
    today = datetime.now().strftime(DATE_FORMAT)

    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            conn.execute(
                "INSERT INTO subscriptions "
                "(id, username, email, phone, package, price, due_date, status, creation_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 'initial', ?)",
                (acc_id, username, email or None, phone or None, pkg_name, price, due_date, today),
            )
            conn.commit()
        logging.info(f"add_user_web: created {acc_id} for {username}")
        return acc_id
    except sqlite3.Error as e:
        logging.error(f"add_user_web DB error: {e}")
        return None


def get_all_users() -> List[Dict]:
    """Return all subscriptions as a list of dicts for web API use."""
    try:
        with sqlite3.connect(CONFIG["DB_NAME"]) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, username, email, phone, package, price, due_date, status "
                "FROM subscriptions"
            )
            return [
                {
                    "id": r[0], "username": r[1], "email": r[2], "phone": r[3],
                    "package": r[4], "price": r[5], "due_date": r[6], "status": r[7],
                }
                for r in c.fetchall()
            ]
    except sqlite3.Error as e:
        logging.error(f"get_all_users error: {e}")
        return []


# ============================================================
# MAIN MENU
# ============================================================

_MENU = f"""
{Fore.CYAN}{Style.BRIGHT}GuardianStreams Billing System  v{__version__}{Style.RESET_ALL}
{Fore.WHITE} 1.  Add user
 2.  View all users
 3.  View users (filtered)
 4.  Export to JSON
 5.  View customer subscription
 6.  Edit customer info
 7.  Import from JSON
 8.  Record payment
 9.  AI: Predict risky customers
 10. AI: Enhanced Predictive Billing Assistant
 11. Test Telegram configuration
 0.  Exit{Style.RESET_ALL}
"""

_MENU_ACTIONS = {
    "1": add_user,
    "2": view_users,
    "3": view_users_with_filters,
    "4": export_to_json,
    "5": view_subscription_by_id,
    "6": edit_customer,
    "7": import_from_json,
    "8": record_payment,
    "9": predict_risky_customers,
    "10": enhanced_predict_risky_customers,
    "11": test_telegram_config,
}


def main() -> None:
    try:
        init_db()
        logging.info(f"GuardianStreams Subscription Manager v{__version__} started")
        notify_all("🚀 GuardianStreams Billing System started")

        while True:
            print(_MENU)
            print(f"{Fore.YELLOW}Choice (0-11): {Style.RESET_ALL}", end="")
            choice = input().strip()
            logging.info(f"Menu choice: {choice}")

            if choice == "0":
                logging.info("Application shutting down")
                notify_all("🛑 GuardianStreams Billing System stopped")
                print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                break
            elif choice in _MENU_ACTIONS:
                _MENU_ACTIONS[choice]()
            else:
                print(f"{Fore.MAGENTA}Invalid choice. Try again.{Style.RESET_ALL}")

    except Exception as e:
        logging.critical(f"Application crashed: {e}", exc_info=True)
        notify_all(f"💥 Critical error: {e}")
        print(f"{Fore.RED}Critical error. Check logs.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
