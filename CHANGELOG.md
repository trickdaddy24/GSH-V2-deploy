# Changelog

All notable changes to GuardianStreams Billing System are documented here.

---

## [2.2.0] - 2026-03-08

### Added
- **Web Interface** — Full FastAPI + React web UI inside `web/`
  - `web/backend/` — FastAPI REST API with 5 routers (`/api/dashboard`, `/api/subscribers`, `/api/payments`, `/api/risk`, `/api/notifications`), Pydantic v2 models, optional `X-API-Key` authentication, shares the CLI's SQLite database via `DB_PATH` env var
  - `web/backend/database.py` — All DB operations extracted from the CLI, returns dicts instead of printing
  - `web/backend/risk.py` — Risk engine (`calculate_risk_score`, `suggest_actions`, `run_general_risk`, `run_enhanced_risk`) usable independently of the CLI
  - `web/frontend/` — React 18 + Vite + TypeScript + Tailwind CSS dark UI
  - **Dashboard page** — Stat cards (totals, revenue, overdue), notification status panel, one-click DB backup and Telegram test
  - **Subscribers page** — Paginated sortable table with live search, status filter, inactive toggle, inline Add form
  - **Subscriber Detail page** — View/edit account info, deactivate/reactivate/delete, full payment history, record new payment
  - **Payments page** — Payment history lookup by account ID
  - **Risk page** — Toggle between General (7-day) and Enhanced (4-day) risk models, per-account flag and action cards
  - `web/README.md` — Setup and run instructions for both backend and frontend

### Changed
- `pyproject.toml` version bumped to `2.2.0`
- `README.md` updated with web interface overview, features, usage, and version history

---

## [2.1.0] - 2026-03-08

### Added
- `show_dashboard()` — live summary screen showing subscriber counts, revenue, status breakdown, delinquent accounts, upcoming dues, and recent payments; displayed automatically on startup and available as menu option 1
- `search_customer()` — partial username search returning all matching accounts including inactive ones
- `deactivate_customer()` — soft deactivate (sets `is_active = 0`, hides from all views, data preserved), reactivate, or hard delete with `DELETE` confirmation prompt
- `bulk_update_due_dates()` — advance due dates across all or filtered accounts by 30/60/90/custom days; shows preview before applying
- `backup_database()` — copies the SQLite `.db` file to a timestamped backup in the working directory
- `.gitignore` — excludes `.env`, `*.db`, `*_backup_*.db`, `*.log`, generated JSON reports, `__pycache__`, `venv/`
- `.env.example` — template with all supported environment variables and inline setup instructions

### Changed
- `is_active INTEGER DEFAULT 1` column added to `subscriptions` table; `init_db()` migrates existing databases automatically
- `_fetch_subscriptions()` accepts `include_inactive` parameter; defaults to active-only
- `get_customer_data()` filters to active subscribers only (`WHERE is_active = 1`)
- `record_payment()` and `edit_customer()` reject inactive accounts
- `export_to_json()` exports active subscribers only
- `view_subscription_by_id()` shows active/inactive label and works for both states
- `add_user()` and `import_from_json()` explicitly set `is_active = 1` on insert
- Menu expanded from 11 to 16 options
- Version bumped to `2.1.0`

---

## [2.0.0] - 2026-03-08

### Added
- `calculate_risk_score()` — standalone helper for reusable risk scoring logic
- `suggest_actions()` — standalone helper for generating action recommendations based on risk score and customer contact info
- "Total subscriptions: N" footer in the View All Users screen
- `CREATE INDEX` on `billing_history(subscription_id)` for faster payment lookups

### Changed
- `predict_risky_customers()` refactored to use `calculate_risk_score()` and `suggest_actions()` helpers
- All magic numbers replaced with named constants (`RISK_HIGH`, `DELINQUENT_DAYS`, `PAID_DAYS`, etc.)
- `send_email()` now uses `smtplib.SMTP` as a context manager (safer connection handling)
- `create_payment_reminder_email()` now returns all three values: subject, plain-text body, and HTML body
- `send_customer_reminders()` passes HTML body to email for rich formatting
- `view_users_with_filters()` filters against computed `display_status` (not raw stored status) — fixes incorrect filter results
- `_fetch_subscriptions()` uses SQL window function (`ROW_NUMBER`) to resolve display status in a single query — eliminates N+1 queries
- `get_customer_data()` uses optimized JOINs for late payment counts — eliminates N+1 queries
- Logging setup moved to a dedicated section; email logger uses private `_email_logger` name
- Codebase organized into labeled sections: Database, Validation, Notification, Customer Management, Payment, Import/Export, Risk Prediction, Email Reminders, Web API, Main Menu

### Removed
- All commented-out dead code from intermediate development versions
- Redundant duplicate function definitions

---

## [1.0.2] - Prior Release

- HTML email support added to `send_email()`
- `send_with_retry()` with exponential backoff
- Grace period tracking (`grace_period_used` column)
- `creation_date` column with auto-migration for existing databases
- Import/export to JSON (`GuardianStreams_export.json`)
- Enhanced risk predictor (4-day imminent window) with reminder sending
- Pushover notification support added

## [1.0.1] - Prior Release

- Payment history tracking via `billing_history` table
- `record_payment()` with due date advancement options (+30/60/90/custom days)
- Risk prediction saved to `risky_customers.json`
- Discord and Telegram notification support

## [1.0.0] - Initial Release

- SQLite-backed subscription management
- Add, view, edit, and filter customers
- Package tiers: OnDemand, Grandfather, Silver, Gold, Platinum, Custom
- Status system: initial, paid, pending, delinquent, active
- Basic email notification support
