# GuardianStreams Billing System

A subscription billing management system for streaming service operators — available as both a command-line tool and a full web interface. Handles customer onboarding, payment recording, subscription status tracking, risk prediction, and multi-channel payment reminders.

---

## Overview

GuardianStreams Billing System is a self-contained application backed by a local SQLite database. It is designed for small-to-medium streaming service operators who need a simple but capable tool to manage subscriber billing without a full SaaS platform.

Two interfaces share the same database — use the **CLI** for quick terminal workflows or the **web UI** (FastAPI + React) for a visual browser-based dashboard. All data stays local. Notifications are sent via configurable external services.

---

## Features

### CLI
- **Dashboard** — Live summary of subscriber counts, revenue, delinquent accounts, upcoming dues, and recent payments shown on startup
- **Customer Management** — Add, view, edit, search by name, and soft-deactivate or permanently delete subscribers with color-coded status display
- **Flexible Sorting & Filtering** — Sort by ID, name, due date, price, or status; filter by status, package, or upcoming due dates
- **Payment Recording** — Log paid, failed, or grace-period payments with automatic due date advancement
- **Status Engine** — Automatically resolves display status (`initial`, `paid`, `pending`, `delinquent`, `active`) based on payment history and account age
- **Risk Prediction** — Two AI-style risk models flag customers likely to miss payments, with scoring based on days until due, late payment history, and grace period usage
- **Payment Reminders** — Send personalized reminders via Email (HTML + plain text), Telegram, Discord, and Pushover with rate limiting and retry logic
- **Bulk Due Date Update** — Advance due dates across all or filtered accounts by 30/60/90/custom days with preview before applying
- **Database Backup** — One-click timestamped copy of the SQLite database
- **Import / Export** — Bulk import and export subscriber data via JSON
- **Multi-Channel Notifications** — System events (new users, payments, errors) broadcast to all enabled notification channels
- **Schema Migrations** — Database columns are added automatically on startup if missing; safe to run against older databases

### Web Interface (`web/`)
- **Browser Dashboard** — Stat cards for totals, revenue, overdue counts; notification status panel; one-click DB backup and Telegram test
- **Subscribers Table** — Paginated, searchable, filterable grid with live search; click any row for full detail view
- **Subscriber Detail** — Edit account info, deactivate/reactivate, permanently delete, view and record payment history — all in-browser
- **Risk Analysis** — Toggle between General (7-day) and Enhanced (4-day) risk models; per-account flag list and suggested actions
- **REST API** — FastAPI backend with Swagger UI at `/docs`; all endpoints protected by optional API key auth
- **Shared Database** — Web backend reads the same SQLite file as the CLI — no sync required

---

## Requirements

### CLI
- Python 3.10+
- Dependencies: `colorama`, `requests` (see `requirements.txt`)

```bash
pip install -r requirements.txt
```

### Web Interface
- Python 3.10+ and Node.js 18+
- See `web/README.md` for full setup instructions

```bash
# Backend
pip install -r web/backend/requirements.txt

# Frontend
cd web/frontend && npm install
```

---

## Usage

### Run the CLI

```bash
python subscription_manager.py
```

### Run the Web Interface

```bash
# Terminal 1 — API backend (http://localhost:8898)
cd web/backend
python main.py

# Terminal 2 — React frontend (http://localhost:5173)
cd web/frontend
npm run dev
```

The frontend proxies all `/api` requests to the backend automatically. See `web/README.md` for production build and auth setup.

You will be presented with the main menu:

```
GuardianStreams Billing System  v2.1.0

 1.  Dashboard
 2.  Add user
 3.  View all users
 4.  View users (filtered)
 5.  Search customer by name
 6.  View customer subscription
 7.  Edit customer info
 8.  Deactivate / delete customer
 9.  Export to JSON
10.  Import from JSON
11.  Record payment
12.  AI: Predict risky customers
13.  AI: Enhanced Predictive Billing Assistant
14.  Bulk update due dates
15.  Database backup
16.  Test Telegram configuration
 0.  Exit
```

### CLI Workflows

**Add a new subscriber**
Select `2`, enter username, optional email/phone, choose a package, and set a due date.

**Search for a customer**
Select `5` and type part of the username — returns all partial matches.

**Record a payment**
Select `11`, enter the account ID digits (e.g. `001`), confirm the amount, choose paid/failed/grace period, then pick a new due date if paid.

**Deactivate or delete a customer**
Select `8`. Choose soft deactivate (hidden from views, data preserved) or permanent delete (requires typing `DELETE` to confirm). Inactive accounts can also be reactivated.

**Find at-risk customers**
- Option `12` — General model: flags anyone due within 7 days
- Option `13` — Enhanced model: focused 4-day window, prompts to send reminders immediately

**Bulk advance due dates**
Select `14`, filter by all/status/package, choose how many days to advance, preview the changes, then confirm.

**Back up the database**
Select `15` — creates a timestamped copy of the `.db` file in the current directory.

**Import existing data**
Select `10` and provide a path to a JSON file matching the export format (see [Data Directory](#data-directory)).

### Web Workflows

**View and manage subscribers**
Go to `/subscribers` — search by name or email, filter by status, toggle inactive accounts. Click any row to open the detail view.

**Edit or deactivate an account**
Open a subscriber's detail page → click **Edit** to change username/email/phone/price/due date, or **Deactivate** to soft-hide the account. Reactivate or permanently delete from the same page.

**Record a payment via web**
Open a subscriber's detail page → click **Record Payment** → fill in amount, status, and new due date advance days.

**Run risk analysis**
Go to `/risk` → toggle between General (7-day) and Enhanced (4-day) models. Each at-risk account shows its score, flags, and suggested actions.

**Backup the database**
Go to `/dashboard` → click **Backup Now**. A timestamped `.db` copy is created on the server.

---

## Configuration

All configuration is done via environment variables. Create a `.env` file in the project root or set them in your shell.

```env
# Email (Gmail recommended)
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=you@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=billing@guardianstreams.com
EMAIL_FROM_NAME=GuardianStreams Billing

# Telegram
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Discord
DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Pushover
PUSHOVER_ENABLED=true
PUSHOVER_API_TOKEN=your_api_token
PUSHOVER_USER_KEY=your_user_key
```

All notification services are optional and disabled by default.

### Web-Specific Variables

Add these to `web/backend/.env` (or copy from `web/README.md`):

```env
# Path to the shared SQLite database
DB_PATH=../../OnDemand_subscriptions.db

# Optional API key — leave blank to disable auth (local dev)
ADMIN_API_KEY=your_strong_secret_here
```

The web backend inherits all notification env vars from the same `.env` file.

---

## Data Directory

The following files are created automatically in the working directory:

| File | Description |
|---|---|
| `OnDemand_subscriptions.db` | Primary SQLite database (subscriptions + billing history) |
| `OnDemand_subscriptions_backup_YYYYMMDD_HHMMSS.db` | Timestamped database backup (CLI option 15 or web Dashboard) |
| `GuardianStreams_export.json` | Output of the JSON export function |
| `risky_customers.json` | Output of the general risk predictor |
| `payment_risk_report_YYYYMMDD_HHMM.json` | Timestamped report from the enhanced risk predictor |
| `email_detailed.log` | Detailed email send log with redacted content |

### Web Directory Structure

```
web/
├── backend/
│   ├── main.py          FastAPI app entry point
│   ├── config.py        CONFIG dict + env var loading
│   ├── database.py      All DB operations (shared with CLI logic)
│   ├── models.py        Pydantic v2 request/response models
│   ├── auth.py          X-API-Key header authentication
│   ├── risk.py          Risk scoring engine
│   ├── requirements.txt Backend Python dependencies
│   └── routers/         One file per API prefix
│       ├── dashboard.py
│       ├── subscribers.py
│       ├── payments.py
│       ├── risk.py
│       └── notifications.py
└── frontend/
    ├── src/
    │   ├── pages/       Dashboard, Subscribers, SubscriberDetail, Payments, Risk
    │   ├── components/  Layout, StatCard, StatusBadge, ui/{Button,Card,Input,Badge}
    │   └── lib/         api.ts (typed API client), utils.ts
    └── package.json
```

### Export Format

```json
[
  {
    "id": "dtv.001",
    "customer": {
      "name": "John Doe",
      "contact": {
        "phone": "555-1234",
        "email": "john@example.com"
      }
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

---

## Version History

| Version | Date | Summary |
|---|---|---|
| 2.2.0 | 2026-03-08 | FastAPI + React web interface (GSH Web v1.0); shared SQLite DB, 5 REST API routers, full browser UI |
| 2.1.0 | 2026-03-08 | Dashboard, search, deactivate/delete, bulk due dates, DB backup, .gitignore, .env.example |
| 2.0.0 | 2026-03-08 | Modular risk helpers, N+1-free SQL, named constants, HTML email, DB index |
| 1.0.2 | — | HTML email, retry logic, grace period, enhanced risk predictor |
| 1.0.1 | — | Payment history, due date advancement, Discord/Telegram |
| 1.0.0 | — | Initial release |

See [CHANGELOG.md](CHANGELOG.md) for full details.

---

## Packages

| ID | Name | Price |
|---|---|---|
| 0 | OnDemand | $10/mo |
| 1 | Grandfather | $25/mo |
| 2 | Silver | $30/mo |
| 3 | Gold | $40/mo |
| 4 | Platinum | $50/mo |
| 5 | Custom | User-defined |

---

## Status Reference

| Status | Meaning |
|---|---|
| `initial` | Account created within the last 5 days |
| `paid` | Payment recorded within the last 21 days |
| `active` | Manually set to active |
| `pending` | Awaiting payment, not yet delinquent |
| `delinquent` | More than 30 days past due date |
