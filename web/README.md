# GSH Web Interface

FastAPI + React web interface for the GuardianStreams Hub subscription manager.

## Architecture

```
web/
├── backend/     FastAPI REST API (Python)
└── frontend/    React + Vite + TypeScript + Tailwind (dark UI)
```

The backend shares the same SQLite database as the CLI tool via the `DB_PATH`
environment variable, so no data migration is needed.

---

## Backend Setup

### Requirements
- Python 3.10+
- Packages: `fastapi`, `uvicorn[standard]`, `python-dotenv`, `requests`

### Mac / Linux

```bash
cd web/backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp ../../.env.example .env
# Edit .env — set DB_PATH and optionally ADMIN_API_KEY

python main.py
# → http://localhost:8898
# → http://localhost:8898/docs  (Swagger UI)
```

### Windows

```powershell
cd web\backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy ..\..\\.env.example .env
# Edit .env — set DB_PATH and optionally ADMIN_API_KEY

python main.py
# → http://localhost:8898
# → http://localhost:8898/docs  (Swagger UI)
```

### Environment Variables

| Variable         | Default                              | Description                     |
|------------------|--------------------------------------|---------------------------------|
| `DB_PATH`        | `../../OnDemand_subscriptions.db`    | Path to the SQLite database     |
| `ADMIN_API_KEY`  | *(empty — auth disabled)*            | API key for `X-API-Key` header  |
| `TELEGRAM_*`     | —                                    | Inherited from root `.env`      |

---

## Frontend Setup

### Requirements
- Node.js 18+ and npm (or pnpm / bun)

### Mac / Linux

```bash
cd web/frontend

npm install

# Optional: set API key if backend auth is enabled
echo "VITE_API_KEY=your_key_here" > .env.local

npm run dev
# → http://localhost:5173  (proxies /api → localhost:8898)
```

### Windows

```powershell
cd web\frontend

npm install

# Optional: set API key if backend auth is enabled
echo VITE_API_KEY=your_key_here > .env.local

npm run dev
# → http://localhost:5173  (proxies /api → localhost:8898)
```

### Production Build (both platforms)

```bash
npm run build
# Output: web/frontend/dist/
# Serve dist/ with any static file server or Nginx
```

---

## API Reference

The backend exposes a full OpenAPI spec at `http://localhost:8898/docs`.

| Router          | Prefix                 | Key Endpoints                                    |
|-----------------|------------------------|--------------------------------------------------|
| Dashboard       | `/api/dashboard`       | `GET /`                                          |
| Subscribers     | `/api/subscribers`     | CRUD + deactivate/reactivate + bulk due-dates    |
| Payments        | `/api/payments`        | `GET /{id}`, `POST /`                            |
| Risk            | `/api/risk`            | `GET /general`, `GET /enhanced`                  |
| Notifications   | `/api/notifications`   | `GET /status`, `POST /test/telegram`, `POST /backup` |

---

## Authentication

When `ADMIN_API_KEY` is set, every request must include:

```
X-API-Key: your_key_here
```

The frontend reads `VITE_API_KEY` from `.env.local` and includes it automatically.

If `ADMIN_API_KEY` is not set, all endpoints are open (suitable for local-only use).

---

## Pages

| Route                    | Description                             |
|--------------------------|-----------------------------------------|
| `/dashboard`             | Stats overview, backup, test telegram   |
| `/subscribers`           | Paginated table with search + filters   |
| `/subscribers/:accId`    | Detail view, edit, deactivate, payments |
| `/payments`              | Payment history lookup by account ID    |
| `/risk`                  | General (7-day) and Enhanced (4-day)    |
