from fastapi import APIRouter, Depends
from auth import verify_api_key
from config import CONFIG
from database import get_dashboard_stats
from models import DashboardStats

router = APIRouter()


@router.get("", response_model=DashboardStats, dependencies=[Depends(verify_api_key)])
def dashboard():
    return get_dashboard_stats()


@router.get("/packages", dependencies=[Depends(verify_api_key)])
def packages():
    return [
        {"id": k, "name": v[0], "price": v[1]}
        for k, v in CONFIG["PACKAGES"].items()
    ]
