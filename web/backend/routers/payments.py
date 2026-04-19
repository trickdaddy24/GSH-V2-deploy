from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from auth import verify_api_key
from database import add_payment, get_payment_history, bulk_add_payments
from models import PaymentCreate, BulkPaymentBody, BulkPaymentResult, MessageResponse
from notify import notify_all

router = APIRouter()


@router.post("", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def record_payment(body: PaymentCreate, bg: BackgroundTasks):
    ok, error = add_payment(
        acc_id=body.subscription_id,
        amount=body.amount,
        status=body.status,
        advance_days=body.advance_days,
        custom_due_date=body.custom_due_date,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    bg.add_task(
        notify_all,
        f"💳 Payment recorded\nAccount: {body.subscription_id}\nAmount: ${body.amount:.2f}\nStatus: {body.status}"
    )
    return {"message": f"Payment recorded for {body.subscription_id}"}


@router.post("/bulk", response_model=BulkPaymentResult, dependencies=[Depends(verify_api_key)])
def bulk_payment(body: BulkPaymentBody, bg: BackgroundTasks, preview: bool = Query(False)):
    result = bulk_add_payments(
        amount=body.amount,
        status=body.status,
        advance_days=body.advance_days,
        status_filter=body.status_filter,
        package_filter=body.package_filter,
        account_ids=body.account_ids,
        preview_only=preview,
    )
    if not preview and result["affected"] > 0:
        bg.add_task(
            notify_all,
            f"💳 Bulk payment processed\nRecorded: {result['affected']} accounts\nAmount: ${body.amount:.2f} each\nStatus: {body.status}"
        )
    return result


@router.get("/{acc_id}", dependencies=[Depends(verify_api_key)])
def payment_history(acc_id: str):
    return get_payment_history(acc_id)
