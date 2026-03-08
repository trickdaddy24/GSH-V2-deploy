from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from auth import verify_api_key
from database import (
    get_all_subscribers, get_subscriber_by_id, create_subscriber,
    update_subscriber, deactivate_subscriber, reactivate_subscriber,
    delete_subscriber, export_subscribers, import_subscribers,
    bulk_update_due_dates,
)
from models import (
    SubscriberCreate, SubscriberUpdate, SubscriberList,
    MessageResponse, BulkDueDateUpdate, BulkUpdateResult,
)

router = APIRouter()


@router.get("", response_model=SubscriberList, dependencies=[Depends(verify_api_key)])
def list_subscribers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    package: Optional[str] = Query(None),
    sort_by: str = Query("id"),
    sort_dir: str = Query("asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    include_inactive: bool = Query(False),
):
    return get_all_subscribers(
        search=search,
        status_filter=status,
        package_filter=package,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
        include_inactive=include_inactive,
    )


@router.get("/{acc_id}", dependencies=[Depends(verify_api_key)])
def get_subscriber(acc_id: str):
    sub = get_subscriber_by_id(acc_id)
    if not sub:
        raise HTTPException(status_code=404, detail=f"Account {acc_id} not found")
    return sub


@router.post("", status_code=201, dependencies=[Depends(verify_api_key)])
def add_subscriber(body: SubscriberCreate):
    acc_id, error = create_subscriber(
        username=body.username,
        email=body.email,
        phone=body.phone,
        package_id=body.package_id,
        due_date=body.due_date,
        custom_price=body.custom_price,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"id": acc_id, "message": f"Account {acc_id} created"}


@router.patch("/{acc_id}", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def edit_subscriber(acc_id: str, body: SubscriberUpdate):
    fields = body.model_dump(exclude_none=True)
    ok, error = update_subscriber(acc_id, fields)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} updated"}


@router.post("/{acc_id}/deactivate", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def deactivate(acc_id: str):
    ok, error = deactivate_subscriber(acc_id)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} deactivated"}


@router.post("/{acc_id}/reactivate", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def reactivate(acc_id: str):
    ok, error = reactivate_subscriber(acc_id)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} reactivated"}


@router.delete("/{acc_id}", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
def delete(acc_id: str):
    ok, error = delete_subscriber(acc_id)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"message": f"Account {acc_id} permanently deleted"}


@router.get("/export/json", dependencies=[Depends(verify_api_key)])
def export():
    return export_subscribers()


@router.post("/import/json", dependencies=[Depends(verify_api_key)])
def import_json(data: list):
    return import_subscribers(data)


@router.post("/bulk/due-dates", response_model=BulkUpdateResult, dependencies=[Depends(verify_api_key)])
def bulk_due_dates(body: BulkDueDateUpdate, preview: bool = Query(False)):
    result = bulk_update_due_dates(
        advance_days=body.advance_days,
        account_ids=body.account_ids,
        status_filter=body.status_filter,
        package_filter=body.package_filter,
        preview_only=preview,
    )
    return result
