import logging
import os
import sqlite3
import traceback

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import CONFIG
from database import migrate_db
from routers import dashboard, subscribers, payments, risk, notifications
import auth_router
from heartbeat import run_heartbeat

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gsh_backend.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("gsh")

_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
print("=" * 60)
print(f"[GSH] Starting backend...")
print(f"[GSH] CWD              : {os.getcwd()}")
print(f"[GSH] .env path        : {_env_file}")
print(f"[GSH] .env exists      : {os.path.exists(_env_file)}")
print(f"[GSH] DB_PATH env      : {os.getenv('DB_PATH', '(not set)')}")
print(f"[GSH] Resolved DB_NAME : {CONFIG['DB_NAME']}")
print(f"[GSH] Absolute DB path : {os.path.abspath(CONFIG['DB_NAME'])}")
print(f"[GSH] DB file exists   : {os.path.exists(os.path.abspath(CONFIG['DB_NAME']))}")
print("=" * 60)

migrate_db()

@asynccontextmanager
async def lifespan(app_: FastAPI):
    task = asyncio.create_task(run_heartbeat())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="GuardianStreams Billing API",
    version="1.0.0",
    description="REST API for the GuardianStreams subscription management system.",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "https://gsh.stunna.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router,    prefix="/api/auth",           tags=["Auth"])
app.include_router(dashboard.router,      prefix="/api/dashboard",      tags=["Dashboard"])
app.include_router(subscribers.router,    prefix="/api/subscribers",    tags=["Subscribers"])
app.include_router(payments.router,       prefix="/api/payments",       tags=["Payments"])
app.include_router(risk.router,           prefix="/api/risk",           tags=["Risk"])
app.include_router(notifications.router,  prefix="/api/notifications",  tags=["Notifications"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/debug")
def debug():
    db_path = CONFIG["DB_NAME"]
    abs_path = os.path.abspath(db_path)
    exists = os.path.exists(abs_path)
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    info = {
        "db_path_configured": db_path,
        "db_path_absolute": abs_path,
        "db_exists": exists,
        "env_DB_PATH": os.getenv("DB_PATH", "(not set — using default)"),
        "env_file_exists": os.path.exists(env_file),
        "env_file_path": env_file,
        "cwd": os.getcwd(),
    }
    if exists:
        try:
            conn = sqlite3.connect(abs_path)
            c = conn.cursor()
            info["row_count"] = c.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
            info["active_count"] = c.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active=1").fetchone()[0]
            info["columns"] = [r[1] for r in c.execute("PRAGMA table_info(subscriptions)")]
            conn.close()
        except Exception as e:
            info["db_error"] = str(e)
    return info


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
