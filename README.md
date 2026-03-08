# GuardianStreams Billing System

A command-line billing management tool for streaming service subscriptions. Handles customer onboarding, payment recording, subscription status tracking, risk prediction, and multi-channel payment reminders.

---

## Overview

GuardianStreams Billing System is a self-contained CLI application backed by a local SQLite database. It is designed for small-to-medium streaming service operators who need a simple but capable tool to manage subscriber billing without a full SaaS platform. All data stays local. Notifications are sent via configurable external services.

---

## Features

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

### Common Workflows

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
