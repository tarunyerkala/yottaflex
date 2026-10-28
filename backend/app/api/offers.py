from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from backend.app.db.database import get_db
from backend.app.models.models import Offer, Application
from backend.app.schemas.schemas import (
    OfferRead, OfferCreate, OfferApprovalRequest, OfferRespondRequest
)
import datetime
from pydantic import BaseModel
from backend.app.services.offer_service import (
    create_offer, approve_offer, respond_to_offer, update_offer_expiry
)

class OfferExpiryUpdate(BaseModel):
    expiry_date: datetime.date

router = APIRouter(prefix="/offers", tags=["Offers"])

def _format_offer(o: Offer) -> dict:
    cand_name = o.application.candidate.full_name if o.application and o.application.candidate else None
    req_title = o.application.requisition.title if o.application and o.application.requisition else None
    min_sal = o.application.requisition.min_salary if o.application and o.application.requisition else None
    max_sal = o.application.requisition.max_salary if o.application and o.application.requisition else None
    return {
        "id": o.id,
        "offer_id": o.offer_id,
        "application_id": o.application_id,
        "proposed_salary": o.proposed_salary,
        "currency": o.currency,
        "salary_period": o.salary_period,
        "proposed_start_date": o.proposed_start_date,
        "issue_date": o.issue_date,
        "expiry_date": o.expiry_date,
        "status": o.status,
        "approval_status": o.approval_status,
        "approver": o.approver,
        "created_at": o.created_at,
        "candidate_name": cand_name,
        "requisition_title": req_title,
        "requisition_salary_min": min_sal,
        "requisition_salary_max": max_sal,
        "requisition_status": o.application.requisition.status if o.application and o.application.requisition else None,
        "requisition_id": o.application.requisition.requisition_id if o.application and o.application.requisition else None
    }

@router.get("", response_model=List[OfferRead])
def list_offers(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Offer).options(
        selectinload(Offer.application).selectinload(Application.candidate),
        selectinload(Offer.application).selectinload(Application.requisition)
    )
    if status:
        query = query.filter(Offer.status == status)
    offers = query.order_by(Offer.id.desc()).offset(offset).limit(limit).all()
    return [_format_offer(o) for o in offers]

@router.get("/{id}", response_model=OfferRead)
def get_offer(id: int, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")
    return _format_offer(offer)

@router.post("", response_model=OfferRead, status_code=201)
def create_new_offer(offer_in: OfferCreate, db: Session = Depends(get_db)):
    offer = create_offer(db, offer_in)
    return _format_offer(offer)

@router.post("/{id}/approve", response_model=OfferRead)
def approve(id: int, req: OfferApprovalRequest, db: Session = Depends(get_db)):
    offer = approve_offer(db, id, req)
    return _format_offer(offer)

@router.post("/{id}/reject", response_model=OfferRead)
def reject(id: int, req: OfferApprovalRequest, db: Session = Depends(get_db)):
    req.status = "Rejected"
    offer = approve_offer(db, id, req)
    return _format_offer(offer)

@router.post("/{id}/respond", response_model=OfferRead)
def respond(id: int, req: OfferRespondRequest, db: Session = Depends(get_db)):
    offer = respond_to_offer(db, id, req)
    return _format_offer(offer)

@router.patch("/{id}/expiry", response_model=OfferRead)
@router.post("/{id}/expiry", response_model=OfferRead)
def update_expiry(id: int, req: OfferExpiryUpdate, db: Session = Depends(get_db)):
    offer = update_offer_expiry(db, id, req.expiry_date)
    return _format_offer(offer)
