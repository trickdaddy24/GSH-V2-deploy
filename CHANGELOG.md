# Changelog

All notable changes to GuardianStreams Billing System are documented here.

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
