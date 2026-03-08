# GuardianStreams Billing System

A command-line billing management tool for streaming service subscriptions. Handles customer onboarding, payment recording, subscription status tracking, risk prediction, and multi-channel payment reminders.

---

## Overview

GuardianStreams Billing System is a self-contained CLI application backed by a local SQLite database. It is designed for small-to-medium streaming service operators who need a simple but capable tool to manage subscriber billing without a full SaaS platform. All data stays local. Notifications are sent via configurable external services.

---

## Features

- **Customer Management** — Add, view, edit, and search subscribers with color-coded status display
- **Flexible Sorting & Filtering** — Sort by ID, name, due date, price, or status; filter by status, package, or upcoming due dates
- **Payment Recording** — Log paid, failed, or grace-period payments with automatic due date advancement
- **Status Engine** — Automatically resolves display status (`initial`, `paid`, `pending`, `delinquent`, `active`) based on payment history and account age
- **Risk Prediction** — Two AI-style risk models flag customers likely to miss payments, with scoring based on days until due, late payment history, and grace period usage
- **Payment Reminders** — Send personalized reminders via Email (HTML + plain text), Telegram, Discord, and Pushover with rate limiting and retry logic
- **Import / Export** — Bulk import and export subscriber data via JSON
- **Multi-Channel Notifications** — System events (new users, payments, errors) broadcast to all enabled notification channels
- **Schema Migrations** — Database columns are added automatically on startup if missing; safe to run against older databases

---

## Requirements

- Python 3.10+
- See `requirements.txt` for dependencies

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### Run the CLI

```bash
python subscription_manager.py
```

You will be presented with the main menu:

```
GuardianStreams Billing System  v2.0.0

 1.  Add user
 2.  View all users
 3.  View users (filtered)
 4.  Export to JSON
 5.  View customer subscription
 6.  Edit customer info
 7.  Import from JSON
 8.  Record payment
 9.  AI: Predict risky customers
10.  AI: Enhanced Predictive Billing Assistant
11.  Test Telegram configuration
 0.  Exit
```

### Common Workflows

**Add a new subscriber**
Select `1`, enter username, optional email/phone, choose a package, and set a due date.

**Record a payment**
Select `8`, enter the account ID digits (e.g. `001`), confirm the amount, choose paid/failed/grace period, then pick a new due date if paid.

**Find at-risk customers**
- Option `9` — General model: flags anyone due within 7 days
- Option `10` — Enhanced model: focused 4-day window, prompts to send reminders immediately

**Import existing data**
Select `7` and provide a path to a JSON file matching the export format (see [Data Directory](#data-directory)).

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

---

## Data Directory

The following files are created automatically in the working directory:

| File | Description |
|---|---|
| `OnDemand_subscriptions.db` | Primary SQLite database (subscriptions + billing history) |
| `GuardianStreams_export.json` | Output of the JSON export function |
| `risky_customers.json` | Output of the general risk predictor |
| `payment_risk_report_YYYYMMDD_HHMM.json` | Timestamped report from the enhanced risk predictor |
| `email_detailed.log` | Detailed email send log with redacted content |

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
