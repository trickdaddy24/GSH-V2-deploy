from fastapi import APIRouter, Depends, HTTPException
from auth import verify_api_key
from database import add_payment, get_payment_history
from models import PaymentCreate, MessageResponse

router = APIRouter()


@router.get("/{acc_id}", dependencies=[Depends(verify_api_key)])
def payment_history(acc_id: str):
    return get_payment_history(acc_id)


@router.post("", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def record_payment(body: PaymentCreate):
    ok, error = add_payment(
        acc_id=body.subscription_id,
        amount=body.amount,
        status=body.status,
        advance_days=body.advance_days,
        custom_due_date=body.custom_due_date,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Payment recorded for {body.subscription_id}"}
