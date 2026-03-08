from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import dashboard, subscribers, payments, risk, notifications

app = FastAPI(
    title="GuardianStreams Billing API",
    version="1.0.0",
    description="REST API for the GuardianStreams subscription management system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router,      prefix="/api/dashboard",      tags=["Dashboard"])
app.include_router(subscribers.router,    prefix="/api/subscribers",    tags=["Subscribers"])
app.include_router(payments.router,       prefix="/api/payments",       tags=["Payments"])
app.include_router(risk.router,           prefix="/api/risk",           tags=["Risk"])
app.include_router(notifications.router,  prefix="/api/notifications",  tags=["Notifications"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
