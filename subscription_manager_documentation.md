# GuardianStreams Subscription Manager — Full Documentation

**Version:** 2.1.0
**Last Updated:** 2026-03-08
**File:** `subscription_manager.py`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Configuration Reference](#3-configuration-reference)
4. [Database Schema](#4-database-schema)
5. [Status System](#5-status-system)
6. [Menu Reference](#6-menu-reference)
7. [Function Reference](#7-function-reference)
8. [Notification Services](#8-notification-services)
9. [Risk Prediction Models](#9-risk-prediction-models)
10. [Data Files](#10-data-files)
11. [Constants Reference](#11-constants-reference)
12. [Error Handling](#12-error-handling)
13. [Known Limitations](#13-known-limitations)

---

## 1. Overview

GuardianStreams Subscription Manager is a self-contained command-line billing tool for streaming service operators. It manages subscriber records, tracks payment history, resolves subscription statuses dynamically, predicts payment risk, and sends multi-channel notifications — all backed by a local SQLite database.

**Design goals:**
- No external database server required — everything runs from a single `.db` file
- All notification services are optional and independently toggled via environment variables
- Status is computed dynamically from payment history rather than stored as a static flag
- SQL queries use window functions and JOINs to avoid N+1 performance problems
- Schema migrations run automatically on startup — safe to run against any database version

---

## 2. Architecture

```
subscription_manager.py
│
├── Constants & Configuration
│   ├── Named constants (DATE_FORMAT, DELINQUENT_DAYS, RISK_HIGH, etc.)
│   └── CONFIG dict (packages, DB name, notification credentials, rate limits)
│
├── Logging Setup
│   ├── Root logger → stdout
│   └── email_notifications logger → email_detailed.log
│
├── Database Layer
│   ├── init_db()             — table creation + migrations
│   ├── generate_account_id() — next available dtv.NNN ID
│   ├── _fetch_subscriptions()— single-query fetch with window function
│   └── get_customer_data()   — optimized fetch for risk analysis
│
├── Validation Helpers
│   ├── is_valid_email()
│   ├── is_valid_phone()
│   └── parse_date()
│
├── Notification System
│   ├── send_email()          — SMTP with HTML support
│   ├── send_notification()   — Telegram / Discord / Pushover
│   ├── send_with_retry()     — exponential backoff wrapper
│   ├── notify_all()          — broadcast to all enabled channels
│   └── test_telegram_config()
│
├── Customer Management
│   ├── show_dashboard()
│   ├── add_user()
│   ├── view_users()
│   ├── view_users_with_filters()
│   ├── search_customer()
│   ├── view_subscription_by_id()
│   ├── edit_customer()
│   └── deactivate_customer()
│
├── Payment System
│   ├── add_payment_record()
│   └── record_payment()
│
├── Import / Export
│   ├── export_to_json()
│   └── import_from_json()
│
├── Risk Prediction
│   ├── calculate_risk_score()
│   ├── suggest_actions()
│   ├── predict_risky_customers()
│   ├── enhanced_predict_risky_customers()
│   └── save_prediction_report()
│
├── Email Reminders
│   ├── create_payment_reminder_email()
│   └── send_customer_reminders()
│
├── Bulk Operations
│   └── bulk_update_due_dates()
│
├── Database Backup
│   └── backup_database()
│
├── Web API Stubs
│   ├── add_user_web()
│   └── get_all_users()
│
└── Main Menu
    ├── show_dashboard() on startup
    └── menu loop (options 0–16)
```

---

## 3. Configuration Reference

All configuration is loaded from environment variables at startup. Copy `.env.example` to `.env` and fill in values. No restart is required after changing env vars — restart the script to reload.

### Packages

Defined in `CONFIG["PACKAGES"]`. Modifying requires editing the source file.

| ID | Name | Price |
|---|---|---|
| 0 | OnDemand | $10/mo |
| 1 | Grandfather | $25/mo |
| 2 | Silver | $30/mo |
| 3 | Gold | $40/mo |
| 4 | Platinum | $50/mo |
| 5 | Custom | User-defined |

### Rate Limiting

| Setting | Default | Description |
|---|---|---|
| `delay_between_notifications` | 15s | Pause between notification service calls in retry loop |
| `delay_between_customers` | 25s | Pause between customers when sending bulk reminders |
| `max_retries` | 3 | Retry attempts before giving up on a notification |

---

## 4. Database Schema

### Table: `subscriptions`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT (PK) | Account ID, format `dtv.NNN` |
| `username` | TEXT NOT NULL | Display name |
| `email` | TEXT | Optional email address |
| `phone` | TEXT | Optional phone number |
| `package` | TEXT | Package name (OnDemand, Gold, etc.) |
| `price` | INTEGER | Monthly price in dollars |
| `due_date` | TEXT | Next payment due date, format `MM-DD-YYYY` |
| `status` | TEXT | Stored status — one of: `initial`, `paid`, `delinquent`, `pending`, `active` |
| `grace_period_used` | INTEGER | `1` if a grace period has ever been granted, else `0` |
| `creation_date` | TEXT | Account creation date, format `MM-DD-YYYY` |
| `is_active` | INTEGER | `1` = active, `0` = soft-deactivated |

> **Note:** `status` is the *stored* status written to the DB. The *display* status shown in all views is computed dynamically by `determine_status()` and may differ. See [Status System](#5-status-system).

### Table: `billing_history`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK, auto) | Row ID |
| `subscription_id` | TEXT (FK) | References `subscriptions.id` |
| `payment_date` | TEXT | Date of the payment event, format `MM-DD-YYYY` |
| `amount` | REAL | Amount recorded |
| `status` | TEXT | One of: `paid`, `failed`, `grace_period` |

### Index

```sql
CREATE INDEX idx_billing_sub ON billing_history(subscription_id);
```

Speeds up all payment lookups, which are joined on `subscription_id` in every query.

### Schema Migrations

`init_db()` checks for missing columns on every startup and adds them automatically:

| Column | Migration |
|---|---|
| `creation_date` | `ALTER TABLE subscriptions ADD COLUMN creation_date TEXT` |
| `grace_period_used` | `ALTER TABLE subscriptions ADD COLUMN grace_period_used INTEGER DEFAULT 0` |
| `is_active` | `ALTER TABLE subscriptions ADD COLUMN is_active INTEGER DEFAULT 1` |

---

## 5. Status System

Status is **computed at read time** from payment history and account age — not simply read from the `status` column. This is handled by `determine_status()`.

### Resolution Order

```
1. Is the account more than 30 days past due_date?
   → delinquent

2. Was the account created within the last 5 days?
   → initial

3. Was the most recent payment marked 'paid' within the last 21 days?
   → paid

4. Is the stored status 'active'?
   → active

5. Default
   → pending
```

### Status Colors (CLI)

| Status | Color |
|---|---|
| `paid` | Green |
| `active` | Cyan |
| `pending` | Yellow |
| `initial` | White |
| `delinquent` | Red |

### Status Sort Order (view_users sort-by-status)

`paid` → `active` → `pending` → `initial` → `delinquent`

---

## 6. Menu Reference

| Option | Function | Description |
|---|---|---|
| 1 | `show_dashboard` | Summary of subscribers, revenue, delinquent, due soon, recent payments |
| 2 | `add_user` | Add a new subscriber interactively |
| 3 | `view_users` | View all active subscribers with sort options |
| 4 | `view_users_with_filters` | Filter by status/package/due date, then sort |
| 5 | `search_customer` | Partial username search |
| 6 | `view_subscription_by_id` | Full details + payment history for one account |
| 7 | `edit_customer` | Edit username, email, phone, due date, or package |
| 8 | `deactivate_customer` | Soft deactivate, reactivate, or permanently delete |
| 9 | `export_to_json` | Export all active subscribers to JSON |
| 10 | `import_from_json` | Import subscribers from a JSON file |
| 11 | `record_payment` | Record a payment and update due date |
| 12 | `predict_risky_customers` | General 7-day risk model |
| 13 | `enhanced_predict_risky_customers` | Focused 4-day risk model with reminder sending |
| 14 | `bulk_update_due_dates` | Advance due dates in bulk with preview |
| 15 | `backup_database` | Timestamped copy of the SQLite database |
| 16 | `test_telegram_config` | Validate Telegram credentials and send a test message |
| 0 | — | Exit |

---

## 7. Function Reference

### Database

#### `init_db() → None`
Creates the `subscriptions` and `billing_history` tables and `idx_billing_sub` index if they don't exist. Runs column migrations for `creation_date`, `grace_period_used`, and `is_active`. Called once at startup. Raises `sqlite3.Error` on failure.

#### `generate_account_id() → str`
Queries all existing `dtv.NNN` IDs and returns the next available one starting from `dtv.000`. Thread-unsafe — suitable for single-user CLI use only.

#### `determine_status(subscription, latest_payment) → str`
Computes the display status for a subscription. See [Status System](#5-status-system) for resolution order. Returns a string from `('initial', 'paid', 'pending', 'delinquent', 'active')`.

#### `_fetch_subscriptions(cursor, include_inactive=False) → List[Dict]`
Fetches all subscriptions with display status resolved in a single SQL query using a `ROW_NUMBER()` window function to retrieve each account's latest payment without N+1 queries. Set `include_inactive=True` to include deactivated accounts. Each returned dict contains: `id`, `username`, `email`, `phone`, `package`, `price`, `due_date`, `status`, `creation_date`, `is_active`, `display_status`.

#### `get_customer_data() → List[Dict]`
Fetches active subscribers with late payment counts and latest payment info via a single query with two LEFT JOINs. Used by both risk predictors. Returns a list of dicts with: `id`, `username`, `email`, `phone`, `due_date` (as `datetime`), `status`, `grace_period_used`, `late_payments`.

---

### Validation

#### `is_valid_email(email) → bool`
Returns `True` if the email is blank (field is optional) or matches `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`.

#### `is_valid_phone(phone) → bool`
Returns `True` if the phone is blank or contains at least 7 digits after stripping non-numeric characters.

#### `parse_date(date_str) → Optional[datetime]`
Tries `MM-DD-YY` then `MM-DD-YYYY`. Returns a `datetime` object or `None` if both fail.

---

### Notification

#### `send_email(to_email, subject, body, html_body=None) → bool`
Sends via SMTP using credentials from `CONFIG["NOTIFICATIONS"]["EMAIL"]`. Logs content to `email_detailed.log` via `_log_email()` before sending. Attaches both plain-text and HTML parts if `html_body` is provided. Uses `smtplib.SMTP` as a context manager. Returns `True` on success.

#### `send_notification(service, message, title=None) → bool`
Sends to `telegram`, `discord`, or `pushover`. Checks that the service is enabled and credentials are present before making the request. Returns `True` on success, `False` on any failure.

- **Telegram:** `POST /bot{token}/sendMessage` with `parse_mode=HTML`
- **Discord:** `POST` to webhook URL; expects HTTP 204
- **Pushover:** `POST` to `api.pushover.net/1/messages.json`

#### `send_with_retry(service, message, title=None, recipient=None) → bool`
Wraps `send_email` or `send_notification` with up to `max_retries` attempts and exponential backoff (`delay * attempt` seconds between tries). Returns `True` if any attempt succeeds.

#### `notify_all(message, title=None) → None`
Calls `send_notification` for `telegram`, `discord`, and `pushover`. Used for system events (new user, payment recorded, errors). Does not send email.

---

### Customer Management

#### `show_dashboard() → None`
Queries subscriber counts, monthly revenue, status breakdown, delinquent accounts, accounts due in the next 7 days, and the 5 most recent billing history entries. Prints a formatted summary to the terminal. Called automatically on startup.

#### `add_user() → None`
Interactive prompt loop for username, email (optional), phone (optional), package selection, custom price (if Custom package), and due date. Aborts after `MAX_INPUT_ERRORS` (3) consecutive validation failures. Inserts with `status='initial'` and `is_active=1`. Fires `notify_all` on success.

#### `view_users() → None`
Fetches all active subscribers via `_fetch_subscriptions()`, prompts for a sort key (1–9), prints with `_print_subscription_rows()`, and shows a total count footer.

#### `view_users_with_filters() → None`
Prompts for a filter (all / paid / delinquent / pending / due in 7 days / package), then a sort key. Filters against computed `display_status` (not the raw stored `status` column).

#### `search_customer() → None`
Accepts a partial username string and runs a `LIKE '%query%'` search (case-insensitive via `LOWER()`). Returns both active and inactive accounts. Displays results with `_print_subscription_rows()`.

#### `view_subscription_by_id() → None`
Prompts for account ID digits (e.g. `001` → `dtv.001`). Displays full account details, computed display status, total amount paid, last `MAX_PAYMENT_HISTORY` (5) payments, and active/inactive label.

#### `edit_customer() → None`
Prompts for account ID, loads current values, then allows updating username, email, phone, due date, and package/price. Press Enter at any prompt to keep the existing value. Only allows fields in `ALLOWED_EDIT_FIELDS`. Refuses edits on inactive accounts.

#### `deactivate_customer() → None`
Loads account and shows current state. Presents options contextually:
- If **active**: deactivate (soft) or permanently delete
- If **inactive**: reactivate or permanently delete

**Soft deactivate** — sets `is_active = 0`. Account is hidden from all views, payment recording, and exports. Data is fully preserved and can be restored.

**Permanent delete** — requires typing `DELETE` exactly. Removes the row from `subscriptions` and all matching rows from `billing_history`. This is irreversible.

---

### Payment System

#### `add_payment_record(subscription_id, amount, status) → bool`
Inserts a row into `billing_history` with today's date. Fires `notify_all`. Returns `True` on success. Valid statuses: `paid`, `failed`, `grace_period`.

#### `record_payment() → None`
Prompts for account ID, shows expected amount, accepts optional custom amount, then asks for payment status. If `paid`, prompts for new due date (+30/60/90/custom days). If `grace_period`, sets `grace_period_used = 1` and `status = 'pending'`. Refuses if account is inactive.

---

### Import / Export

#### `export_to_json() → None`
Exports all **active** subscribers to `GuardianStreams_export.json` in the nested format below. Fires `notify_all`.

```json
[
  {
    "id": "dtv.001",
    "customer": {
      "name": "John Doe",
      "contact": { "phone": "555-1234", "email": "john@example.com" }
    },
    "subscription": {
      "plan": "Gold",
      "price": 40,
      "due_date": "03-15-2026",
      "status": "paid",
      "creation_date": "01-01-2026"
    }
  }
]
```

#### `import_from_json() → None`
Reads a user-specified JSON file in the format above. Uses `INSERT OR REPLACE` so re-importing the same file is safe. Skips records with missing required fields (`username`, `plan`, `price`, `due_date`) or invalid date format. Sets all imported records to `status='initial'` and `is_active=1`.

---

### Risk Prediction

#### `calculate_risk_score(customer) → Tuple[int, List[str]]`
Scores a customer based on three factors:

| Factor | Points |
|---|---|
| Days until due (≤ 7) | `min(max(7 - days, 1), 7)` — capped at 7 to prevent unbounded scores for overdue accounts |
| Late payments | `3 × min(late_count, 3)` — max 9 pts |
| Grace period used | +2 pts |

Returns `(score, reasons)` where `reasons` is a list of human-readable strings.

#### `suggest_actions(customer, score) → List[str]`
Returns a list of action strings based on score threshold:
- **High** (`score >= 7`): urgent reminder + email address + phone number if available
- **Medium** (`score < 7`): friendly Telegram reminder

#### `predict_risky_customers() → None`
General model. Processes all active customers, filters to `score >= RISK_GENERAL_MIN` (4), classifies as high/medium, saves results to `risky_customers.json`, and prints a formatted report. Fires `notify_all` with summary counts.

#### `enhanced_predict_risky_customers() → None`
Focused model. Only considers customers due within `RISK_IMMINENT_DAYS` (4) days. Uses a tighter minimum score of `RISK_ENHANCED_MIN` (5). Prompts to send reminders immediately via `send_customer_reminders()`. Saves a full report via `save_prediction_report()`.

#### `save_prediction_report(predictions) → None`
Saves a timestamped JSON file (`payment_risk_report_YYYYMMDD_HHMM.json`) with metadata (model version, risk counts), sorted customer list, and action summary.

---

### Email Reminders

#### `create_payment_reminder_email(customer_name, account_id, amount, due_date, risk_level) → Tuple[str, str, str]`
Returns `(subject, plain_text_body, html_body)`. The HTML version uses inline CSS with a dark header, account info box, and footer. Urgency label is `urgent` (red) for high risk, `friendly` (amber) for medium.

#### `send_customer_reminders(predictions) → None`
Iterates predictions, fetches email and price from the DB, sends:
1. HTML email to the customer's address (if email is set and `EMAIL_ENABLED`)
2. Admin notification to Telegram, Discord, and Pushover (if each is enabled)

Respects `delay_between_customers` between each customer to avoid rate limits. Prints a per-service success/failure summary.

---

### Bulk Operations

#### `bulk_update_due_dates() → None`
Filter options: all active subscribers, by display status, or by package name. Advancement options: +30, +60, +90, or a custom number of days. Shows a preview of up to 10 accounts (old → new due date) before asking for confirmation. Updates all matching `due_date` values in a single transaction.

---

### Database Backup

#### `backup_database() → None`
Uses `shutil.copy2()` to create a byte-for-byte copy of `OnDemand_subscriptions.db` named `OnDemand_subscriptions_backup_YYYYMMDD_HHMMSS.db` in the working directory. Prints the backup filename and file size. The backup is excluded from git by `.gitignore`.

---

### Web API Stubs

#### `add_user_web(username, email, phone, package_id, due_date) → Optional[str]`
Programmatic interface for adding a user without interactive prompts. Validates `package_id` and `due_date`, then inserts. Returns the new account ID on success or `None` on failure. Intended for integration with a web front-end.

#### `get_all_users() → List[Dict]`
Returns all active subscriptions as a list of plain dicts. Intended for web API use.

---

## 8. Notification Services

### Setup Guide

#### Email (Gmail)
1. Enable 2-factor authentication on your Google account
2. Generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Set `EMAIL_USERNAME` to your Gmail address and `EMAIL_PASSWORD` to the app password
4. Set `EMAIL_ENABLED=true`

#### Telegram
1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow prompts
2. Copy the bot token to `TELEGRAM_BOT_TOKEN`
3. Send any message to your new bot, then visit:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   and copy the `chat.id` value to `TELEGRAM_CHAT_ID`
4. Set `TELEGRAM_ENABLED=true`

#### Discord
1. Open your Discord server → Channel Settings → Integrations → Webhooks → New Webhook
2. Copy the webhook URL to `DISCORD_WEBHOOK_URL`
3. Set `DISCORD_ENABLED=true`

#### Pushover
1. Register at [pushover.net](https://pushover.net) and copy your User Key to `PUSHOVER_USER_KEY`
2. Create a new application/API token at [pushover.net/apps](https://pushover.net/apps) and copy to `PUSHOVER_API_TOKEN`
3. Set `PUSHOVER_ENABLED=true`

### Notification Events

| Event | Function that fires |
|---|---|
| App started | `main()` |
| App stopped | `main()` |
| New user added | `add_user()` |
| User updated | `edit_customer()` |
| User deactivated / deleted | `deactivate_customer()` |
| Payment recorded | `add_payment_record()` |
| Payment successful (due date updated) | `record_payment()` |
| Grace period activated | `record_payment()` |
| Export complete | `export_to_json()` |
| Import complete | `import_from_json()` |
| Risk prediction started | `predict_risky_customers()` |
| Risk prediction complete | `predict_risky_customers()` |
| Bulk due date update | `bulk_update_due_dates()` |
| DB error (various) | multiple functions |

---

## 9. Risk Prediction Models

### Model 1 — General (`predict_risky_customers`)

- **Window:** Customers due within 7 days (or already overdue)
- **Minimum score to include:** 4 (`RISK_GENERAL_MIN`)
- **High risk threshold:** 7 (`RISK_HIGH`)
- **Output:** `risky_customers.json`
- **Actions:** Display report, save file, send `notify_all` summary

### Model 2 — Enhanced (`enhanced_predict_risky_customers`)

- **Window:** Customers due within 4 days (`RISK_IMMINENT_DAYS`)
- **Minimum score to include:** 5 (`RISK_ENHANCED_MIN`)
- **High risk threshold:** 7 (`RISK_HIGH`)
- **Output:** `payment_risk_report_YYYYMMDD_HHMM.json`
- **Actions:** Display report, optionally send customer reminders, save timestamped report

### Scoring Comparison

| Factor | Model 1 | Model 2 |
|---|---|---|
| Days until due | `min(max(7-days,1),7)` | `max(5-days,0)` |
| Late payments | `3 × min(count, 3)` | `2 × min(count, 3)` |
| Grace period | +2 | +1 |
| Minimum score | 4 | 5 |

Model 2 uses lower weights because it already pre-filters to the highest-urgency window. A customer due in 4 days needs less payment-history evidence to be flagged.

---

## 10. Data Files

| File | Created by | Notes |
|---|---|---|
| `OnDemand_subscriptions.db` | `init_db()` | Primary database, created on first run |
| `GuardianStreams_export.json` | `export_to_json()` | Overwritten on each export |
| `risky_customers.json` | `predict_risky_customers()` | Overwritten on each run |
| `payment_risk_report_YYYYMMDD_HHMM.json` | `save_prediction_report()` | New file per run |
| `OnDemand_subscriptions_backup_YYYYMMDD_HHMMSS.db` | `backup_database()` | New file per backup |
| `email_detailed.log` | `_log_email()` | Appended; content is redacted before logging |

All of these are excluded from git by `.gitignore`.

---

## 11. Constants Reference

| Constant | Value | Used in |
|---|---|---|
| `DATE_FORMAT` | `%m-%d-%Y` | All date formatting |
| `DATE_INPUT_FORMATS` | `(%m-%d-%y, %m-%d-%Y)` | `parse_date()` |
| `ACCOUNT_PREFIX` | `dtv.` | Account ID generation |
| `ACCOUNT_PADDING` | `3` | Account ID zero-padding (dtv.001) |
| `DELINQUENT_DAYS` | `30` | Days past due before delinquent status |
| `INITIAL_DAYS` | `5` | Days after creation to show initial status |
| `PAID_DAYS` | `21` | Days after payment to show paid status |
| `RISK_IMMINENT_DAYS` | `4` | Enhanced model window |
| `RISK_GENERAL_MIN` | `4` | General model minimum score threshold |
| `RISK_ENHANCED_MIN` | `5` | Enhanced model minimum score threshold |
| `RISK_HIGH` | `7` | Score at which risk is classified as high |
| `RISK_MAX_LATE` | `3` | Cap on late payments used in scoring |
| `MAX_INPUT_ERRORS` | `3` | Input attempts before aborting add/edit |
| `MAX_PAYMENT_HISTORY` | `5` | Payments shown in subscription detail view |
| `DISCORD_MAX_CHARS` | `1999` | Discord message character limit |
| `NOTIFY_TIMEOUT` | `10` | Seconds before notification request times out |

---

## 12. Error Handling

- All database operations are wrapped in `try/except sqlite3.Error` blocks
- Failed notification sends are logged but do not raise exceptions — the application continues
- `send_with_retry` catches all exceptions per attempt and retries up to `max_retries` times
- `import_from_json` skips malformed individual records rather than aborting the whole import
- `main()` wraps the entire menu loop in `try/except Exception` — on crash it logs the traceback, fires `notify_all`, and prints a user-facing error message
- Invalid menu input prints a message and loops — it does not crash or exit

---

## 13. Known Limitations

- **Single-user only** — SQLite WAL mode is not enabled; concurrent access from multiple processes is not safe
- **Date storage** — Dates are stored as `MM-DD-YYYY` strings. Sorting by date in raw SQL requires string parsing; the application sorts in Python after fetching
- **No pagination** — `view_users()` loads all subscribers into memory; very large datasets (10,000+) may be slow to display
- **No authentication** — The CLI has no login system; anyone with access to the machine can run it
- **Email is plain SMTP** — No OAuth or TLS certificate pinning; relies on app passwords for Gmail
- **Backup is a file copy** — Backups are not compressed or encrypted; protect the directory appropriately
- **`is_active` filter** — Deactivated accounts are hidden from most views but are not moved to a separate table; direct SQL access still shows them
