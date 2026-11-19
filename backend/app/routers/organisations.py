"""Organisation accounts and coverage dashboard (PRD §6.4, §11)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..common import get_or_404
from ..db import get_db
from ..deps import current_user
from ..models import (LGA, Assignment, ContributorProfile, Contest, EvidenceSubmission, Organisation, PollingUnit,
                      UnitStatus, User)
from ..services import audit, classification, engine

router = APIRouter(prefix="/organisations", tags=["organisations"])


class OrgRegistration(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    organisation_type: str = Field(pattern="^(civil_society|observer_group|newsroom|political_party|other)$")
    contact_person: str = Field(min_length=2, max_length=120)
    contact_details: str = Field(min_length=3, max_length=200)
    operational_areas: str = Field(default="", max_length=1000)


def _can_view(user: User, org_id: int):
    if user.role in ("admin", "verifier", "senior_reviewer"):
        return
    if user.role == "coordinator" and user.profile and user.profile.organisation_id == org_id:
        return
    raise HTTPException(403, "You can only view your own organisation")


@router.get("")
def list_organisations(db: Session = Depends(get_db)):
    return [{"id": o.id, "name": o.name, "organisation_type": o.organisation_type,
             "verification_status": o.verification_status} for o in db.scalars(select(Organisation))]


@router.post("")
def register(body: OrgRegistration, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """New organisations start as self-declared until VeraVote verifies them (PRD §11.1)."""
    org = Organisation(**body.model_dump(), verification_status="self_declared")
    db.add(org)
    db.flush()
    audit.record(db, actor=user, entity_type="organisation", entity_id=org.id, action="registered")
    db.commit()
    return {"id": org.id, "name": org.name, "verification_status": org.verification_status}


@router.get("/{org_id}/coverage")
def coverage(org_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Honest coverage: a unit counts as 'observed' only when evidence was received, never on assignment alone."""
    org = get_or_404(db, Organisation, org_id, "Organisation")
    _can_view(user, org_id)
    areas = {a.strip().lower() for a in org.operational_areas.split(",") if a.strip()}
    lga_ids = [l.id for l in db.scalars(select(LGA)) if l.name.lower() in areas] if areas else []
    units = db.scalars(select(PollingUnit).where(PollingUnit.lga_id.in_(lga_ids), PollingUnit.active)
                       .order_by(PollingUnit.official_code)).all() if lga_ids else []
    contest = db.scalar(select(Contest).order_by(Contest.id))
    member_ids = [p.user_id for p in db.scalars(select(ContributorProfile).where(
        ContributorProfile.organisation_id == org_id))]

    rows, totals = [], dict(in_scope=len(units), assigned=0, unassigned=0, awaiting_approval=0, accepted=0,
                            evidence_received=0, evidence_pending=0, incomplete=0, discrepancies=0)
    for pu in units:
        assigns = db.scalars(select(Assignment).where(Assignment.polling_unit_id == pu.id,
                                                      Assignment.organisation_id == org_id)).all()
        live = [a for a in assigns if a.status in ("requested", "approved", "accepted")]
        subs = db.scalars(select(EvidenceSubmission).where(
            EvidenceSubmission.polling_unit_id == pu.id, EvidenceSubmission.organisation_id == org_id,
            EvidenceSubmission.submission_status != "rejected")).all()
        us = db.get(UnitStatus, (pu.id, contest.id)) if contest else None
        accepted_assign = [a for a in live if a.status == "accepted"]
        totals["assigned"] += bool(accepted_assign or [a for a in live if a.status == "approved"])
        totals["unassigned"] += not any(a.status in ("approved", "accepted") for a in live)
        totals["awaiting_approval"] += sum(1 for a in live if a.status == "requested")
        totals["accepted"] += len(accepted_assign)
        totals["evidence_received"] += bool(subs)
        totals["evidence_pending"] += bool(accepted_assign) and not subs
        totals["incomplete"] += any(s.extraction_status != "confirmed" for s in subs)
        totals["discrepancies"] += bool(us and us.status == engine.DISCREPANCY)
        rows.append({"polling_unit": {"id": pu.id, "code": pu.official_code, "name": pu.official_name,
                                      "lga": pu.lga.name, "ward": pu.ward.name},
                     "assignments": [{"id": a.id, "status": a.status, "contributor": a.contributor.name,
                                      "is_primary": a.is_primary} for a in live],
                     "submissions": len(subs), "unit_status": us.status if us else engine.NO_EVIDENCE,
                     "observed": bool(subs)})
    return {"organisation": {"id": org.id, "name": org.name, "verification_status": org.verification_status},
            "totals": totals, "units": rows, "members": len(member_ids),
            "note": "A polling unit is counted as observed only once evidence has been received from it."}


@router.get("/{org_id}/members")
def members(org_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _can_view(user, org_id)
    out = []
    for p in db.scalars(select(ContributorProfile).where(ContributorProfile.organisation_id == org_id)):
        if p.user_id == user.id:
            continue
        cls = classification.classify(p)
        out.append({"user_id": p.user_id, "name": p.user.name, "application_status": p.application_status,
                    "classification_label": classification.label(cls, p.party_affiliation),
                    "official_status": p.official_status})
    return out


@router.get("/{org_id}/requests")
def pending_requests(org_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _can_view(user, org_id)
    rows = db.scalars(select(Assignment).where(Assignment.organisation_id == org_id,
                                               Assignment.status == "requested"))
    return [{"id": a.id, "contributor": a.contributor.name, "polling_unit": a.polling_unit.official_name,
             "polling_unit_code": a.polling_unit.official_code, "requested_at": a.requested_at} for a in rows]
