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
    email: Optional[str]
    phone: Optional[str]
    package: str
    price: float
    due_date: str
    status: str
    display_status: str
    creation_date: Optional[str]
    grace_period_used: bool
    is_active: bool


class SubscriberList(BaseModel):
    items: List[Subscriber]
    total: int
    page: int
    page_size: int


# ── Payments ───────────────────────────────────────────────

class PaymentCreate(BaseModel):
    subscription_id: str
    amount: float
    status: str                      # paid | failed | grace_period
    advance_days: Optional[int] = None
    custom_due_date: Optional[str] = None


class Payment(BaseModel):
    id: int
    subscription_id: str
    payment_date: str
    amount: float
    status: str


# ── Dashboard ──────────────────────────────────────────────

class StatusBreakdown(BaseModel):
    paid: int = 0
    active: int = 0
    pending: int = 0
    initial: int = 0
    delinquent: int = 0


class RecentPayment(BaseModel):
    payment_date: str
    amount: float
    status: str
    username: str
    account_id: str


class DelinquentAccount(BaseModel):
    id: str
    username: str
    due_date: str


class DueSoonAccount(BaseModel):
    id: str
    username: str
    due_date: str


class DashboardStats(BaseModel):
    total_active: int
    total_inactive: int
    monthly_revenue: float
    status_breakdown: StatusBreakdown
    delinquent_count: int
    due_soon_count: int
    delinquent_accounts: List[DelinquentAccount]
    due_soon_accounts: List[DueSoonAccount]
    recent_payments: List[RecentPayment]


# ── Risk ───────────────────────────────────────────────────

class RiskPrediction(BaseModel):
    id: str
    username: str
    risk_score: int
    risk_level: str
    reasons: List[str]
    suggested_actions: List[str]
    due_date: str
    due_in_days: Optional[int] = None


class RiskReport(BaseModel):
    predictions: List[RiskPrediction]
    generated_at: str
    total: int
    high_count: int
    medium_count: int


# ── Bulk Operations ────────────────────────────────────────

class BulkDueDateUpdate(BaseModel):
    account_ids: Optional[List[str]] = None   # None = all active
    status_filter: Optional[str] = None
    package_filter: Optional[str] = None
    advance_days: int


class BulkUpdateResult(BaseModel):
    updated: int
    preview: List[Dict[str, Any]]
    confirmed: bool


# ── Generic ────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class BackupResponse(BaseModel):
    filename: str
    size_kb: float
