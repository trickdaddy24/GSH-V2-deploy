from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ── Subscribers ────────────────────────────────────────────

class SubscriberCreate(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    package_id: str
    due_date: str
    custom_price: Optional[float] = None


class SubscriberUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    due_date: Optional[str] = None
    package_id: Optional[str] = None
    custom_price: Optional[float] = None


class Subscriber(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    package_id: str
    package_name: str
    price: float
    due_date: str
    status: str                        # resolved display status
    days_until_due: Optional[int] = None
    last_payment: Optional[str] = None
    is_active: int                     # 0 or 1


class SubscriberList(BaseModel):
    subscribers: List[Subscriber]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Payments ───────────────────────────────────────────────

class PaymentCreate(BaseModel):
    subscription_id: str
    amount: float
    status: str                        # paid | failed | grace_period
    advance_days: Optional[int] = None
    custom_due_date: Optional[str] = None


class Payment(BaseModel):
    id: int
    subscription_id: str
    payment_date: str
    amount: float
    status: str
    new_due_date: Optional[str] = None


# ── Dashboard ──────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_subscribers: int
    active_subscribers: int
    inactive_subscribers: int
    due_today: int
    overdue: int
    revenue_this_month: float
    revenue_last_month: float


# ── Risk ───────────────────────────────────────────────────

class RiskPrediction(BaseModel):
    id: str
    username: str
    risk_score: int
    risk_level: str
    flags: List[str]
    suggested_actions: List[str]
    days_overdue: Optional[int] = None


class RiskReport(BaseModel):
    predictions: List[RiskPrediction]
    generated_at: str
    model: str
    threshold_days: int
    total_at_risk: int
    high_count: int
    medium_count: int


# ── Bulk Operations ────────────────────────────────────────

class BulkDueDateUpdate(BaseModel):
    account_ids: Optional[List[str]] = None
    status_filter: Optional[str] = None
    package_filter: Optional[str] = None
    advance_days: int


class BulkUpdateResult(BaseModel):
    preview: bool
    affected: int
    accounts: List[str]


# ── Generic ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class BackupResponse(BaseModel):
    filename: str
    size_kb: float
