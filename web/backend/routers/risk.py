from fastapi import APIRouter, Depends
from auth import verify_api_key
from database import get_customer_data
from risk import run_general_risk, run_enhanced_risk
from models import RiskReport

router = APIRouter()


@router.get("/general", response_model=RiskReport, dependencies=[Depends(verify_api_key)])
def general_risk():
    customers = get_customer_data()
    return run_general_risk(customers)


@router.get("/enhanced", response_model=RiskReport, dependencies=[Depends(verify_api_key)])
def enhanced_risk():
    customers = get_customer_data()
    return run_enhanced_risk(customers)
