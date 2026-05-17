# Changelog

All notable changes to GuardianStreams Billing System are documented here.

---

## [2.7.0] — 2026-05-17

### Changed
- **Frontend redesign → "Operator" direction** — dense data-console aesthetic: IBM Plex Sans/Mono, sharp corners, mono tabular numerals, Aurora theme (purple/dark) via a `--op-*` CSS-variable system (`src/styles/operator.css`).
- **Login** rebuilt to the Operator console layout (status bar, two-panel grid, footer); same `login(username,password)` flow. Pre-auth side panel is static system info (no fabricated metrics).
- **Layout** converted from sidebar to an Operator top-bar + horizontal tab nav + status footer; theme toggle + logout unchanged.
- **Dashboard** restyled to the Operator console — all data still bound to the real API (`getDashboard`/`getNotificationStatus` + real backup/Telegram/bulk mutations); no mock panels.
- Shared `ui` primitives (Button/Card/Input/Badge), `StatCard`, `StatusBadge` repointed to Operator classes with unchanged prop APIs — other pages inherit the look; full per-page restyle is phase 2.

### Notes
- Presentation-only: no changes to auth, API, routing, or react-query. Operator is dark-first; a light palette + ThemeContext wiring is a deferred follow-up.

## [2.6.0] — 2026-04-19

### Added
- **Daily delinquent summary email** — sent to `admin@stunna.xyz` daily at 4:10 AM Eastern via asyncio background task; each delinquent subscriber gets an HTML card with account info, days overdue, amount due, a website link, and a Telegram deep link
- **`notify_email_html()`** — new function in `notify.py` for sending HTML emails via Gmail SMTP with plain-text fallback
- **Telegram deep-link payment flow** — `/start pay_*` handler in the webhook; tapping `https://t.me/{bot}?start=pay_{acc_id}` sends the due-notice with inline 💳 Record Payment button directly to the user
- **Bot username cache** — fetched once at module load via `getMe` and used to build deep-link URLs in the daily email

### Fixed
- **Due date calculation** — recording a payment for an overdue subscriber now advances from today (not the old past due date)

---

## [2.5.0] — 2026-04-19

### Added
- **Button color variants** — new `green` (Edit), `slate` (Delete), `violet` (Record Payment), `teal` (Send Due Notice) variants added to Button component and applied in SubscriberDetail
- **Status filter persistence** — Subscribers page status filter saved to `sessionStorage`; survives in-session navigation, resets on tab close
- **Telegram payment flow** — "Send Due Notice" button on subscriber detail page sends a Telegram message with an inline "💳 Record Payment" button; tapping the button starts a two-step reply flow where the bot confirms the amount and records the payment automatically
- **Bulk delinquent notices** — Dashboard shows delinquent subscriber count with a "Send Due Notices to All Delinquent" button; Subscribers page shows a "Send Due Notices" button in the filter toolbar when filtered to delinquent status
- **Telegram webhook router** — new `/api/telegram/webhook` endpoint (no auth) handles Telegram callback queries and message replies; `/api/telegram/webhook/set` registers the webhook URL

---

## [2.4.0] — 2026-04-18

### Fixed
- **Subscriber search** — search now matches account IDs in addition to usernames (e.g. searching "001" finds "dtv.001")

### Added
- **Bulk payment** — record the same payment for multiple subscribers at once from the Dashboard; supports status/package filters; preview mode shows affected count before applying; Telegram notification sent on completion
- **Heartbeat** — backend sends a random Telegram "still alive" message every 20–28 hours via asyncio background task
- **Payment notifications** — Telegram/Discord/Pushover notification sent when a payment is recorded (via BackgroundTasks)
- **Edit notifications** — Telegram/Discord/Pushover notification sent when a subscriber is edited

### Changed
- Token cleanup: `border-gray-300`/`text-gray-700` remnants in SubscriberDetail replaced with `gsh.*` tokens

---

## [2.3.0] — 2026-04-18

### Changed
- Replaced `brand.*` sky-blue Tailwind tokens with `gsh.*` design token namespace
- Dark mode: Saltbox-inspired deep navy palette (`#1a1f2e` bg, `#242938` cards, `#2e3650` borders)
- Light mode: clean white/off-white Stripe-like palette
- Accent color: LoginX Electric Purple `#8A4DFF` (buttons, active nav, stat values)
- Active nav indicator: neon cyan left border `#00E0FF` in dark mode
- Badges: lavender `#BFA4FF` default tint (dark), purple `#8A4DFF` tint (light)
- Code blocks: Saltbox-style near-black `#0d1117` background (dark), `#f6f8fa` (light)
- Re-themed: Layout, Card, Button, Badge, Input, StatCard, Login, all pages

---

## [2.2.6] - 2026-03-08

### Fixed
- **Import broken (422 error)** — `data: list` in FastAPI route was not recognised as a request body; changed to `List[Any] = Body(...)` so JSON arrays are correctly parsed
- **Import silently failed** — frontend `catch` block only handled `SyntaxError`; API errors were swallowed after the axios toast; now all error paths show an appropriate toast
- **`null` creation_date skipped** — `dict.get()` returns `None` (not the default) when the key exists but is `null`; fixed with `sub.get("creation_date") or default`
- **Import result feedback** — 0 imported shows error toast with first skip reason; partial import shows info toast and logs all skip reasons to console; full success shows count

### Changed
- `import_subscribers()` returns `skip_reasons` list explaining why each entry was skipped
- Import validates `price is None` separately so `price=0` is accepted

---

## [2.2.5] - 2026-03-08

### Added
- **Test buttons** on every notification service card in Settings
  - Telegram — sends `🧪 Test from GuardianStreams Web` via Bot API
  - Discord — posts test message to webhook
  - Pushover — sends test push notification
  - Email — sends test email to the configured username address via SMTP
  - Buttons disabled when service is toggled off; success/failure shown as toast
- `POST /api/notifications/test/discord` endpoint
- `POST /api/notifications/test/pushover` endpoint
- `POST /api/notifications/test/email` endpoint

---

## [2.2.4] - 2026-03-08

### Added
- **Settings page** (`/settings`) — configure and enable/disable all four notification services from the UI
  - **Telegram** — toggle, Bot Token, Chat ID
  - **Discord** — toggle, Webhook URL
  - **Pushover** — toggle, API Token, User Key
  - **Email (SMTP)** — toggle, SMTP server/port, username, password, from address/name
  - All credential fields have show/hide toggle; password fields skip update if left blank
  - Changes write directly to `.env` and update in-memory config immediately (no restart needed)
- `GET /api/notifications/settings` — returns current notification config (all fields)
- `PATCH /api/notifications/settings` — updates one or more service configs, writes to `.env`
- Settings nav item added to sidebar

---

## [2.2.3] - 2026-03-08

### Fixed
- **Invalid due date format** — added `%Y-%m-%d` (ISO 8601) to `DATE_INPUT_FORMATS` in `config.py` so dates from the HTML date picker (`2026-03-08`) are accepted by the backend

---

## [2.2.2] - 2026-03-08

### Added
- **Bulk Update page** (`/bulk-update`) — advance due dates across all or filtered accounts by any number of days; shows affected count preview before applying; filterable by status and package
- **Export / Import JSON** — Export button on Subscribers page downloads all active subscribers as a dated `.json` file; Import button uploads a JSON array and shows imported/skipped counts via toast
- **Send Reminders button** on Risk page — triggers Telegram notifications for all at-risk accounts in the current mode (General or Enhanced); only appears when at-risk accounts exist
- **Sortable columns** on Subscribers table — click any column header (ID, Username, Price, Due Date, Status) to sort; click again to reverse; sort indicators shown
- **Package dropdown** on Add Subscriber and Edit forms — replaced free-text package ID input with a dropdown showing all packages with prices; Custom package reveals a price field
- **Status filter fix** — Subscribers filter dropdown now shows actual database statuses (Active, Paid, Initial, Pending, Delinquent) instead of incorrect display labels
- **Subscriber count** shown inline next to page title
- `web/frontend/src/lib/constants.ts` — shared `PACKAGES` and `STATUSES` constants used across all forms and filters
- `/api/dashboard/packages` endpoint — returns package list from backend config
- `/api/risk/send-reminders` endpoint — runs risk analysis and sends Telegram reminders for at-risk accounts

### Changed
- `web/frontend/src/components/Layout.tsx` — added Bulk Update nav item, updated version to v2.2.2

---

## [2.2.1] - 2026-03-08

### Added
- **Backend startup diagnostics** — prints DB path, `.env` status, and whether the DB file exists on every startup
- **`/api/debug` endpoint** — returns configured DB path, absolute path, `.env` status, row counts, and column list; useful for diagnosing missing data
- **Global exception handler** — all unhandled backend errors are caught, logged to `gsh_backend.log`, and returned as JSON `{"detail": ..., "type": ...}` instead of crashing silently
- **Frontend error toasts** — any failed API call now shows a red toast notification (bottom-right) with the error detail; toasts auto-dismiss after 6 seconds
- **`ToastContext`** (`web/frontend/src/lib/ToastContext.tsx`) — global toast provider wired into `main.tsx`; `useToast()` hook available in any component
- **Axios response interceptor** — captures all API errors and routes them to the toast system automatically

### Changed
- `web/backend/main.py` — added logging setup, startup print block, global exception handler, `/api/debug` route
- `web/frontend/src/lib/api.ts` — added `registerToast()` and axios error interceptor
- `web/frontend/src/App.tsx` — registers toast function with API client on mount
- `web/frontend/src/main.tsx` — wrapped app with `ToastProvider`

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
