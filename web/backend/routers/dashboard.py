from fastapi import APIRouter, Depends
from auth import verify_api_key
from database import get_dashboard_stats
from models import DashboardStats

router = APIRouter()


@router.get("", response_model=DashboardStats, dependencies=[Depends(verify_api_key)])
def dashboard():
    return get_dashboard_stats()
