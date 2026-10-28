import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.models import (
    Offer, OfferApproval, OfferStatusHistory, Application, JobRequisition
)
from backend.app.schemas.schemas import OfferCreate, OfferApprovalRequest, OfferRespondRequest
from backend.app.rules.business_rules import validate_offer_creation, BusinessRuleViolation
from backend.app.audit.audit_service import log_audit_event


def create_offer(
    db: Session,
    offer_in: OfferCreate,
    actor: str = "Compensation Specialist"
) -> Offer:
    application = db.query(Application).filter(Application.id == offer_in.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    try:
        validate_offer_creation(
            db=db,
            application=application,
            proposed_salary=offer_in.proposed_salary,
            start_date=offer_in.proposed_start_date,
            issue_date=offer_in.issue_date,
            expiry_date=offer_in.expiry_date
        )
    except BusinessRuleViolation as e:
        raise HTTPException(status_code=e.code, detail=e.message)

    count = db.query(Offer).count() + 1
    offer_id = f"OFF-2026-{count:06d}"

    offer = Offer(
        offer_id=offer_id,
        application_id=application.id,
        proposed_salary=offer_in.proposed_salary,
        currency=offer_in.currency,
        salary_period=offer_in.salary_period,
        proposed_start_date=offer_in.proposed_start_date,
        issue_date=offer_in.issue_date,
        expiry_date=offer_in.expiry_date,
        status="Pending Approval",
        approval_status="Pending"
    )
    db.add(offer)
    db.flush()

    # Automatically set application stage to Offer Pending Approval if in Final Review
    if application.stage == "Final Review":
        application.stage = "Offer Pending Approval"

    # Status history
    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status="None",
        to_status="Pending Approval",
        actor=actor,
        reason="Offer created and pending executive approval",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="OFFER_CREATED",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=actor,
        new_state="Pending Approval",
        reason=f"Proposed salary: ${offer_in.proposed_salary:,.2f}"
    )

    db.commit()
    db.refresh(offer)
    return offer




def update_offer_expiry(
    db: Session,
    offer_id: int,
    new_expiry_date: datetime.date,
    actor: str = "Compensation Specialist"
) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if offer.status in ["Accepted", "Declined"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit expiry for an offer that is already '{offer.status}'."
        )

    if new_expiry_date <= offer.issue_date:
        raise HTTPException(
            status_code=400,
            detail="Expiry date must be strictly after the offer issue date."
        )

    old_expiry = offer.expiry_date
    offer.expiry_date = new_expiry_date

    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status=offer.status,
        to_status=offer.status,
        actor=actor,
        reason=f"Extended expiry date from {old_expiry} to {new_expiry_date}",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="OFFER_EXPIRY_UPDATED",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=actor,
        previous_state=str(old_expiry),
        new_state=str(new_expiry_date),
        reason=f"Updated offer expiry to {new_expiry_date}"
    )

    db.commit()
    db.refresh(offer)
    return offer



def approve_offer(
    db: Session,
    offer_id: int,
    approval_in: OfferApprovalRequest
) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if offer.approval_status == "Approved" and approval_in.status == "Approved":
        raise HTTPException(status_code=400, detail=f"Offer {offer.offer_id} is already approved.")

    prev_status = offer.status
    new_status = "Approved" if approval_in.status == "Approved" else "Rejected"

    offer.approval_status = approval_in.status
    offer.status = new_status
    offer.approver = approval_in.approver

    approval_rec = OfferApproval(
        offer_id=offer.id,
        approver=approval_in.approver,
        status=approval_in.status,
        decision_date=datetime.datetime.utcnow(),
        reason=approval_in.reason
    )
    db.add(approval_rec)

    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status=prev_status,
        to_status=new_status,
        actor=approval_in.approver,
        reason=approval_in.reason or f"Offer {approval_in.status}",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type=f"OFFER_{approval_in.status.upper()}",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=approval_in.approver,
        previous_state=prev_status,
        new_state=new_status,
        reason=approval_in.reason
    )

    db.commit()
    db.refresh(offer)
    return offer




def update_offer_expiry(
    db: Session,
    offer_id: int,
    new_expiry_date: datetime.date,
    actor: str = "Compensation Specialist"
) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if offer.status in ["Accepted", "Declined"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit expiry for an offer that is already '{offer.status}'."
        )

    if new_expiry_date <= offer.issue_date:
        raise HTTPException(
            status_code=400,
            detail="Expiry date must be strictly after the offer issue date."
        )

    old_expiry = offer.expiry_date
    offer.expiry_date = new_expiry_date

    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status=offer.status,
        to_status=offer.status,
        actor=actor,
        reason=f"Extended expiry date from {old_expiry} to {new_expiry_date}",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="OFFER_EXPIRY_UPDATED",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=actor,
        previous_state=str(old_expiry),
        new_state=str(new_expiry_date),
        reason=f"Updated offer expiry to {new_expiry_date}"
    )

    db.commit()
    db.refresh(offer)
    return offer



def respond_to_offer(
    db: Session,
    offer_id: int,
    req: OfferRespondRequest,
    actor: str = "Candidate"
) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if offer.status in ["Accepted", "Declined", "Rejected", "Withdrawn", "Expired"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot respond to an offer that is already '{offer.status}'."
        )

    # Check expiry
    today = datetime.date.today()
    if today > offer.expiry_date:
        offer.status = "Expired"
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"Offer {offer.offer_id} expired on {offer.expiry_date}. Acceptance is not permitted."
        )

    # Check if target job role is closed
    if req.response == "Accepted" and offer.application and offer.application.requisition:
        if offer.application.requisition.status != "Open":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot accept offer {offer.offer_id} because the job role '{offer.application.requisition.title}' ({offer.application.requisition.requisition_id}) is closed. Requisitions must be Open to hire candidates."
            )

    if req.response not in ["Accepted", "Declined"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid response '{req.response}'. Must be 'Accepted' or 'Declined'."
        )

    prev_status = offer.status
    offer.status = req.response

    # If accepted, candidate can be marked hired
    if req.response == "Accepted":
        offer.application.stage = "Hired"
        offer.application.status = "Closed"
    elif req.response == "Declined":
        offer.application.stage = "Rejected"
        offer.application.status = "Closed"

    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status=prev_status,
        to_status=req.response,
        actor=actor,
        reason=req.reason or f"Candidate {req.response.lower()} offer",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type=f"OFFER_{req.response.upper()}",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=actor,
        previous_state=prev_status,
        new_state=req.response,
        reason=req.reason
    )

    db.commit()
    db.refresh(offer)
    return offer



def update_offer_expiry(
    db: Session,
    offer_id: int,
    new_expiry_date: datetime.date,
    actor: str = "Compensation Specialist"
) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if offer.status in ["Accepted", "Declined"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit expiry for an offer that is already '{offer.status}'."
        )

    if new_expiry_date <= offer.issue_date:
        raise HTTPException(
            status_code=400,
            detail="Expiry date must be strictly after the offer issue date."
        )

    old_expiry = offer.expiry_date
    offer.expiry_date = new_expiry_date

    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status=offer.status,
        to_status=offer.status,
        actor=actor,
        reason=f"Extended expiry date from {old_expiry} to {new_expiry_date}",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="OFFER_EXPIRY_UPDATED",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=actor,
        previous_state=str(old_expiry),
        new_state=str(new_expiry_date),
        reason=f"Updated offer expiry to {new_expiry_date}"
    )

    db.commit()
    db.refresh(offer)
    return offer



def update_offer_expiry(
    db: Session,
    offer_id: int,
    new_expiry_date: datetime.date,
    actor: str = "Compensation Specialist"
) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    if offer.status in ["Accepted", "Declined"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit expiry for an offer that is already '{offer.status}'."
        )

    if new_expiry_date <= offer.issue_date:
        raise HTTPException(
            status_code=400,
            detail="Expiry date must be strictly after the offer issue date."
        )

    old_expiry = offer.expiry_date
    offer.expiry_date = new_expiry_date

    hist = OfferStatusHistory(
        offer_id=offer.id,
        from_status=offer.status,
        to_status=offer.status,
        actor=actor,
        reason=f"Extended expiry date from {old_expiry} to {new_expiry_date}",
        changed_at=datetime.datetime.utcnow()
    )
    db.add(hist)

    log_audit_event(
        db=db,
        event_type="OFFER_EXPIRY_UPDATED",
        entity_type="Offer",
        entity_id=offer.offer_id,
        actor=actor,
        previous_state=str(old_expiry),
        new_state=str(new_expiry_date),
        reason=f"Updated offer expiry to {new_expiry_date}"
    )

    db.commit()
    db.refresh(offer)
    return offer

