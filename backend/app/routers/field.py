"""Contributor-facing assignments, evidence capture/sync and safety (PRD §6, §7, §8, §14.3)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..common import get_or_404, pu_summary
from ..db import get_db
from ..deps import current_user, require_roles
from ..models import Assignment, Contest, Election, EvidenceSubmission, PollingUnit, User
from ..services import audit, classification, intake

router = APIRouter(tags=["field"])

ACTIVE = ("requested", "approved", "accepted")


def assignment_view(a: Assignment) -> dict:
    return {"id": a.id, "status": a.status, "is_primary": a.is_primary, "election_id": a.election_id,
            "requested_at": a.requested_at, "decided_at": a.decided_at, "polling_unit": pu_summary(a.polling_unit),
            "contributor": {"id": a.contributor.id, "name": a.contributor.name},
            "note": "This assignment is a VeraVote coverage arrangement. It is not INEC accreditation."}


def _require_contributor(user: User) -> str:
    cls = classification.classify(user.profile)
    if cls not in classification.FIELD_CLASSIFICATIONS:
        raise HTTPException(403, "Only approved VeraVote contributors, verified observers or verified party agents "
                                 "can do this. Anyone can still submit a citizen evidence lead.")
    return cls


# ------------------------------------------------------------------ assignments

class AssignmentRequest(BaseModel):
    polling_unit_id: int
    election_id: int


class Decision(BaseModel):
    approve: bool
    note: str = Field(default="", max_length=500)


class Response_(BaseModel):
    accept: bool


@router.get("/assignments/mine")
def my_assignments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Assignment).where(Assignment.contributor_id == user.id).order_by(Assignment.id.desc()))
    return [assignment_view(a) for a in rows]


@router.get("/assignments/availability")
def availability(ward_id: int, election_id: int, db: Session = Depends(get_db),
                 user: User = Depends(current_user)):
    """Units in a ward with how many contributors already cover them (no names: PRD §14.3)."""
    out = []
    for pu in db.scalars(select(PollingUnit).where(PollingUnit.ward_id == ward_id, PollingUnit.active)
                         .order_by(PollingUnit.unit_number)):
        active = db.scalars(select(Assignment).where(Assignment.polling_unit_id == pu.id,
                                                     Assignment.election_id == election_id,
                                                     Assignment.status.in_(ACTIVE))).all()
        out.append({"polling_unit": pu_summary(pu), "active_assignments": len(active),
                    "has_primary": any(a.is_primary and a.status in ("approved", "accepted") for a in active),
                    "mine": next((a.status for a in active if a.contributor_id == user.id), None)})
    return out


@router.post("/assignments/request")
def request_assignment(body: AssignmentRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _require_contributor(user)
    pu = get_or_404(db, PollingUnit, body.polling_unit_id, "Polling unit")
    get_or_404(db, Election, body.election_id, "Election")
    if db.scalar(select(Assignment).where(Assignment.contributor_id == user.id, Assignment.polling_unit_id == pu.id,
                                          Assignment.election_id == body.election_id,
                                          Assignment.status.in_(ACTIVE))):
        raise HTTPException(409, "You already have an active request or assignment for this unit")
    a = Assignment(contributor_id=user.id, polling_unit_id=pu.id, election_id=body.election_id,
                   organisation_id=user.profile.organisation_id)
    db.add(a)
    db.flush()
    audit.record(db, actor=user, entity_type="assignment", entity_id=a.id, action="requested",
                 new={"polling_unit_id": pu.id})
    db.commit()
    db.refresh(a)
    return assignment_view(a)


@router.post("/assignments/{assignment_id}/decide")
def decide(assignment_id: int, body: Decision, db: Session = Depends(get_db),
           user: User = Depends(require_roles("coordinator", "admin"))):
    a = get_or_404(db, Assignment, assignment_id, "Assignment")
    if a.status != "requested":
        raise HTTPException(400, "Only pending requests can be decided")
    if user.role == "coordinator":
        org_id = user.profile.organisation_id if user.profile else None
        if org_id is None or a.organisation_id != org_id:
            raise HTTPException(403, "You can only decide requests from your organisation's members")
    if a.contributor_id == user.id:
        raise HTTPException(403, "You cannot approve your own request")
    if body.approve:
        has_primary = db.scalar(select(Assignment).where(
            Assignment.polling_unit_id == a.polling_unit_id, Assignment.election_id == a.election_id,
            Assignment.is_primary, Assignment.status.in_(("approved", "accepted"))))
        a.is_primary = has_primary is None  # PRD §6.3: one primary; extras allowed when justified
    a.status = "approved" if body.approve else "rejected"
    a.decided_by_id, a.decided_at = user.id, datetime.now(timezone.utc)
    audit.record(db, actor=user, entity_type="assignment", entity_id=a.id, action=a.status,
                 new={"is_primary": a.is_primary, "note": body.note})
    db.commit()
    return assignment_view(a)


@router.post("/assignments/{assignment_id}/respond")
def respond(assignment_id: int, body: Response_, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = get_or_404(db, Assignment, assignment_id, "Assignment")
    if a.contributor_id != user.id:
        raise HTTPException(403, "This is not your assignment")
    if a.status != "approved":
        raise HTTPException(400, "Only approved assignments can be accepted or declined")
    a.status = "accepted" if body.accept else "declined"
    audit.record(db, actor=user, entity_type="assignment", entity_id=a.id, action=a.status)
    db.commit()
    return assignment_view(a)


@router.post("/assignments/{assignment_id}/withdraw")
def withdraw_assignment(assignment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    a = get_or_404(db, Assignment, assignment_id, "Assignment")
    if a.contributor_id != user.id:
        raise HTTPException(403, "This is not your assignment")
    a.status = "withdrawn"
    audit.record(db, actor=user, entity_type="assignment", entity_id=a.id, action="withdrawn")
    db.commit()
    return assignment_view(a)


# ------------------------------------------------------------------ safety

class SafetyReport(BaseModel):
    kind: str = Field(pattern="^(threat|access_denied|asked_to_leave|other)$")
    assignment_id: int | None = None
    withdraw: bool = True
    note: str = Field(default="", max_length=1000)


@router.post("/safety/report")
def safety_report(body: SafetyReport, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Emergency withdrawal / threat report (PRD §14.3). Safety comes before any submission."""
    withdrawn = []
    if body.withdraw:
        q = select(Assignment).where(Assignment.contributor_id == user.id, Assignment.status.in_(ACTIVE))
        if body.assignment_id:
            q = q.where(Assignment.id == body.assignment_id)
        for a in db.scalars(q):
            a.status = "withdrawn"
            withdrawn.append(a.id)
    audit.record(db, actor=user, entity_type="safety_report", entity_id=user.id, action=body.kind,
                 new={"withdrawn_assignments": withdrawn, "note": body.note})
    db.commit()
    return {"withdrawn_assignments": withdrawn,
            "message": "Your report is recorded and the safety team has been notified. Leave the area if you can. "
                       "Your safety matters more than any submission."}


# ------------------------------------------------------------------ evidence

@router.post("/evidence")
async def submit_evidence(
    client_submission_id: str = Form(..., min_length=8, max_length=64),
    polling_unit_id: int = Form(...), contest_id: int = Form(...),
    evidence_type: str = Form("result_sheet_photo"),
    device_reported_time: datetime | None = Form(None), captured_offline: bool = Form(False),
    file: UploadFile = File(...),
    user: User = Depends(current_user), db: Session = Depends(get_db),
):
    """Field evidence upload. Retries with the same client ID return the original receipt (PRD §8.2)."""
    if prev := intake.existing(db, client_submission_id):
        if prev.contributor_id != user.id:
            raise HTTPException(409, "That submission ID is already in use")
        prev.sync_attempts += 1
        audit.record(db, actor=user, entity_type="evidence_submission", entity_id=prev.id, action="sync_retry",
                     new={"attempt": prev.sync_attempts})
        db.commit()
        return intake.receipt(prev, duplicate_retry=True)

    _require_contributor(user)
    pu = get_or_404(db, PollingUnit, polling_unit_id, "Polling unit")
    contest = get_or_404(db, Contest, contest_id, "Contest")
    assignment = db.scalar(select(Assignment).where(
        Assignment.contributor_id == user.id, Assignment.polling_unit_id == pu.id,
        Assignment.election_id == contest.election_id, Assignment.status == "accepted"))
    if assignment is None:
        # PRD §6.3: cannot submit under someone else's assignment, or without one.
        raise HTTPException(403, "You need an accepted assignment for this polling unit. "
                                 "You can still submit a citizen evidence lead.")
    upload = await intake.read_upload(file)
    sub = intake.create(
        db, client_submission_id=client_submission_id, category="field", user=user, pu=pu, contest=contest,
        evidence_type=evidence_type, upload=upload, filename=file.filename, is_forwarded_copy="no",
        device_reported_time=device_reported_time, captured_offline=captured_offline, assignment_id=assignment.id,
    )
    db.commit()
    return intake.receipt(sub)


@router.get("/evidence/mine")
def my_evidence(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(EvidenceSubmission).where(EvidenceSubmission.contributor_id == user.id)
                      .order_by(EvidenceSubmission.id.desc()))
    return [{**intake.receipt(s), "review_note": s.review_note} for s in rows]
