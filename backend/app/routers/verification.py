"""Verification workspace (PRD §9.2, §12). Staff only. Every change is audited."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..common import contest_summary, get_or_404, pu_summary
from ..db import get_db
from ..deps import require_roles
from ..models import (AuditEvent, Contest, ContributorProfile, EvidenceSubmission, ExtractedField, Investigation,
                      OfficialResultDocument, PollingUnit, UnitStatus, User)
from ..services import arithmetic, audit, classification, engine, extraction
from ..services.storage import storage

router = APIRouter(prefix="/verification", tags=["verification"])
staff = require_roles("verifier", "senior_reviewer", "admin")
senior = require_roles("senior_reviewer", "admin")

SENSITIVE_OUTCOMES = {"discrepancy_confirmed", "referred"}
OUTCOMES = {"discrepancy_confirmed", "discrepancy_unresolved", "insufficient_evidence", "referred",
            "consistent", "no_discrepancy_found"}


def _field_view(f: ExtractedField) -> dict:
    return {"id": f.id, "key": f.field_key, "label": f.label, "extracted_value": f.extracted_value,
            "corrected_value": f.corrected_value, "value": f.value, "confidence": f.confidence, "status": f.status,
            "method": f.method, "correction_reason": f.correction_reason,
            "needs_attention": f.status == "proposed" and f.confidence < extraction.LOW_CONFIDENCE}


def _queue_item(db: Session, s: EvidenceSubmission) -> dict:
    us = db.get(UnitStatus, (s.polling_unit_id, s.contest_id))
    values = {f.field_key: f.value for f in s.fields}
    return {
        "id": s.id, "receipt_code": s.receipt_code, "category": s.source_category,
        "classification": s.contributor_classification,
        "classification_label": classification.label(s.contributor_classification, s.party_affiliation),
        "evidence_type": s.evidence_type, "status": s.submission_status, "extraction_status": s.extraction_status,
        "server_received_time": s.server_received_time, "captured_offline": s.captured_offline,
        "polling_unit": {"id": s.polling_unit.id, "code": s.polling_unit.official_code,
                         "name": s.polling_unit.official_name, "lga": s.polling_unit.lga.name,
                         "ward": s.polling_unit.ward.name},
        "contest_id": s.contest_id, "unit_status": us.status if us else None,
        "low_confidence_fields": sum(1 for f in s.fields if f.status == "proposed"
                                     and f.confidence < extraction.LOW_CONFIDENCE),
        "arithmetic_flags": len(arithmetic.check(values)) if values else 0,
    }


@router.get("/queue")
def queue(state_id: int | None = None, lga_id: int | None = None, ward_id: int | None = None,
          polling_unit_id: int | None = None, contest_id: int | None = None, category: str | None = None,
          classification_: str | None = None, evidence_type: str | None = None, status: str | None = None,
          discrepancy_only: bool = False, db: Session = Depends(get_db), user: User = Depends(staff)):
    q = select(EvidenceSubmission).join(PollingUnit, EvidenceSubmission.polling_unit_id == PollingUnit.id)
    for col, val in [(PollingUnit.state_id, state_id), (PollingUnit.lga_id, lga_id), (PollingUnit.ward_id, ward_id),
                     (EvidenceSubmission.polling_unit_id, polling_unit_id),
                     (EvidenceSubmission.contest_id, contest_id),
                     (EvidenceSubmission.source_category, category),
                     (EvidenceSubmission.contributor_classification, classification_),
                     (EvidenceSubmission.evidence_type, evidence_type),
                     (EvidenceSubmission.submission_status, status)]:
        if val is not None:
            q = q.where(col == val)
    items = [_queue_item(db, s) for s in db.scalars(q.order_by(EvidenceSubmission.server_received_time.desc()))]
    if discrepancy_only:
        items = [i for i in items if i["unit_status"] == engine.DISCREPANCY]
    return items


@router.get("/submissions/{sub_id}")
def submission_detail(sub_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    s = get_or_404(db, EvidenceSubmission, sub_id, "Submission")
    values = {f.field_key: f.value for f in s.fields}
    history = db.scalars(select(AuditEvent).where(AuditEvent.entity_type == "evidence_submission",
                                                  AuditEvent.entity_id == str(s.id)).order_by(AuditEvent.id))
    unit = engine.evaluate(db, s.polling_unit, s.contest)
    return {
        **_queue_item(db, s),
        "contributor": None if not s.contributor else {"id": s.contributor.id, "name": s.contributor.name},
        "organisation": None if not s.organisation else {"id": s.organisation.id, "name": s.organisation.name},
        "file_sha256": s.file_hash, "file_size": s.file_size, "content_type": s.content_type,
        "file_url": f"/verification/files/submission/{s.id}" if s.original_file_key else None,
        "integrity_ok": storage.verify(s.original_file_key, s.file_hash) if s.original_file_key else None,
        "source_url": s.source_url, "description": s.description, "follow_up_contact": s.follow_up_contact,
        "is_forwarded_copy": s.is_forwarded_copy, "device_reported_time": s.device_reported_time,
        "sync_attempts": s.sync_attempts, "review_note": s.review_note,
        "fields": [_field_view(f) for f in s.fields], "arithmetic": arithmetic.check(values) if values else [],
        "contest": contest_summary(s.contest), "polling_unit_full": pu_summary(s.polling_unit),
        "unit": unit, "is_own_submission": s.contributor_id == user.id,
        "history": [{"at": e.timestamp, "action": e.action, "by": e.actor_label, "new": e.new_value,
                     "previous": e.previous_value} for e in history],
    }


@router.get("/files/{kind}/{ident}")
def staff_file(kind: str, ident: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    obj = get_or_404(db, EvidenceSubmission if kind == "submission" else OfficialResultDocument, ident, "File")
    if not obj.original_file_key:
        raise HTTPException(404, "No file")
    # PRD §7.4: access to sensitive evidence is logged.
    audit.record(db, actor=user, entity_type=f"{kind}_file", entity_id=ident, action="viewed")
    db.commit()
    ctype = getattr(obj, "content_type", None) or (
        "image/svg+xml" if obj.original_file_key.endswith(".svg") else "application/octet-stream")
    return Response(storage.read(obj.original_file_key), media_type=ctype,
                    headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
                             "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


def _not_own(s: EvidenceSubmission, user: User):
    if s.contributor_id == user.id:
        raise HTTPException(403, "You cannot review your own evidence")


class FieldEdit(BaseModel):
    id: int
    value: int | None = Field(default=None, ge=0, le=10_000_000)
    unreadable: bool = False
    reason: str | None = Field(default=None, max_length=500)


class FieldEdits(BaseModel):
    fields: list[FieldEdit]


@router.post("/submissions/{sub_id}/fields")
def edit_fields(sub_id: int, body: FieldEdits, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Confirm or correct extracted figures. The original file and extracted value are kept (PRD §9.2)."""
    s = get_or_404(db, EvidenceSubmission, sub_id, "Submission")
    _not_own(s, user)
    if s.extraction_status == "confirmed":
        raise HTTPException(400, "Extraction is already confirmed; open a correction through an investigation")
    by_id = {f.id: f for f in s.fields}
    for edit in body.fields:
        f = by_id.get(edit.id)
        if f is None:
            raise HTTPException(400, f"Field {edit.id} does not belong to this submission")
        before = {"value": f.value, "status": f.status}
        if edit.unreadable:
            if not edit.reason:
                raise HTTPException(400, f"Say why “{f.label}” is unreadable")
            f.status, f.corrected_value, f.correction_reason = "unreadable", None, edit.reason
        elif edit.value is None:
            raise HTTPException(400, f"Enter a value for “{f.label}” or mark it unreadable")
        elif edit.value != f.extracted_value:
            if not edit.reason:
                raise HTTPException(400, f"Give a reason for correcting “{f.label}”")
            f.status, f.corrected_value, f.correction_reason = "corrected", edit.value, edit.reason
        else:
            f.status, f.corrected_value, f.correction_reason = "confirmed", None, None
        f.reviewed_by_id = user.id
        audit.record(db, actor=user, entity_type="extracted_field", entity_id=f.id, action=f"field_{f.status}",
                     previous=before, new={"value": f.value, "status": f.status, "reason": f.correction_reason},
                     polling_unit_id=s.polling_unit_id)
    db.commit()
    values = {f.field_key: f.value for f in s.fields}
    return {"fields": [_field_view(f) for f in s.fields], "arithmetic": arithmetic.check(values)}


class ExtractionAction(BaseModel):
    action: str = Field(pattern="^(confirm|reject)$")
    note: str = Field(default="", max_length=1000)


@router.post("/submissions/{sub_id}/extraction")
def extraction_action(sub_id: int, body: ExtractionAction, db: Session = Depends(get_db),
                      user: User = Depends(staff)):
    s = get_or_404(db, EvidenceSubmission, sub_id, "Submission")
    _not_own(s, user)
    if not s.fields:
        raise HTTPException(400, "There are no extracted figures to confirm")
    if body.action == "confirm":
        pending = [f.label for f in s.fields if f.status == "proposed" and f.confidence < extraction.LOW_CONFIDENCE]
        if pending:
            raise HTTPException(400, "Check these low-confidence fields first: " + ", ".join(pending))
        missing = [f.label for f in s.fields if f.status != "unreadable" and f.value is None]
        if missing:
            raise HTTPException(400, "Enter or mark unreadable: " + ", ".join(missing))
        for f in s.fields:
            if f.status == "proposed":
                f.status, f.reviewed_by_id = "confirmed", user.id
        s.extraction_status = "confirmed"
    else:
        s.extraction_status = "rejected"
    audit.record(db, actor=user, entity_type="evidence_submission", entity_id=s.id,
                 action=f"extraction_{s.extraction_status}", new={"note": body.note}, polling_unit_id=s.polling_unit_id)
    engine.refresh(db, s.polling_unit, s.contest, actor=user)
    db.commit()
    return submission_detail(sub_id, db, user)


class SubmissionDecision(BaseModel):
    decision: str = Field(pattern="^(start_review|accept|reject|request_info|unresolved_lead)$")
    note: str = Field(default="", max_length=1000)


DECISION_STATUS = {"start_review": "under_review", "accept": "accepted", "reject": "rejected",
                   "request_info": "info_requested", "unresolved_lead": "unresolved_lead"}
DECISION_ACTION = {"start_review": "review_started", "accept": "accepted", "reject": "rejected",
                   "request_info": "info_requested", "unresolved_lead": "unresolved_lead"}


@router.post("/submissions/{sub_id}/decision")
def decide_submission(sub_id: int, body: SubmissionDecision, db: Session = Depends(get_db),
                      user: User = Depends(staff)):
    """Review outcome for one submission (PRD §7.5, §12.3). A promoted citizen lead keeps its citizen label."""
    s = get_or_404(db, EvidenceSubmission, sub_id, "Submission")
    _not_own(s, user)
    if body.decision == "accept" and s.extraction_status != "confirmed":
        raise HTTPException(400, "Confirm the extracted figures before accepting the evidence for comparison")
    if body.decision in ("reject", "request_info", "unresolved_lead") and not body.note.strip():
        raise HTTPException(400, "Add a note explaining this decision")
    before = s.submission_status
    s.submission_status = DECISION_STATUS[body.decision]
    s.review_note = body.note
    audit.record(db, actor=user, entity_type="evidence_submission", entity_id=s.id,
                 action=DECISION_ACTION[body.decision], previous={"status": before},
                 new={"status": s.submission_status, "note": body.note}, polling_unit_id=s.polling_unit_id,
                 public=body.decision != "request_info", actor_label="Verification team")
    engine.refresh(db, s.polling_unit, s.contest, actor=user)
    db.commit()
    return submission_detail(sub_id, db, user)


# ------------------------------------------------------------------ official documents (simulated IReV)

class OfficialDoc(BaseModel):
    polling_unit_id: int
    contest_id: int
    source_reference: str = Field(min_length=3, max_length=500)
    version_reference: str = Field(default="v1", max_length=60)
    values: dict[str, int]


@router.post("/official-documents")
def attach_official(body: OfficialDoc, db: Session = Depends(get_db), user: User = Depends(staff)):
    """Attach an official result document. MVP: manual entry of a SIMULATED IReV record (PRD §9.6)."""
    from ..seed import sheet_svg  # renderer for the simulated document image

    pu = get_or_404(db, PollingUnit, body.polling_unit_id, "Polling unit")
    contest = get_or_404(db, Contest, body.contest_id, "Contest")
    keys = {k for k, _ in extraction.field_spec(contest)}
    if unknown := set(body.values) - keys:
        raise HTTPException(400, f"Unknown fields: {', '.join(sorted(unknown))}")
    previous = db.scalar(select(OfficialResultDocument).where(
        OfficialResultDocument.polling_unit_id == pu.id, OfficialResultDocument.contest_id == contest.id,
        OfficialResultDocument.is_current))
    data = sheet_svg(pu, contest, body.values, f"official-{body.version_reference}")
    key, digest = storage.put_original(data, ".svg")
    doc = OfficialResultDocument(polling_unit_id=pu.id, election_id=contest.election_id, contest_id=contest.id,
                                 source_platform="IReV (simulated)", source_reference=body.source_reference,
                                 original_file_key=key, file_hash=digest, version_reference=body.version_reference,
                                 supersedes_id=previous.id if previous else None, attached_by_id=user.id)
    if previous:
        previous.is_current = False  # PRD §19: IReV document changes after publication — keep both versions
    db.add(doc)
    db.flush()
    extraction.attach_fields(db, owner=doc, contest=contest, values=body.values)
    audit.record(db, actor=user, entity_type="official_document", entity_id=doc.id,
                 action="replaced" if previous else "attached",
                 previous={"document_id": previous.id} if previous else None,
                 new={"version": body.version_reference, "file_hash": digest}, polling_unit_id=pu.id, public=True,
                 actor_label="Verification team")
    result = engine.refresh(db, pu, contest, actor=user)
    db.commit()
    return {"document_id": doc.id, "superseded_document_id": previous.id if previous else None,
            "unit_status": result["status"]}


# ------------------------------------------------------------------ unit review and investigations

@router.get("/units/{pu_id}/{contest_id}")
def unit_detail(pu_id: int, contest_id: int, db: Session = Depends(get_db), user: User = Depends(staff)):
    pu = get_or_404(db, PollingUnit, pu_id, "Polling unit")
    contest = get_or_404(db, Contest, contest_id, "Contest")
    inv = db.scalar(select(Investigation).where(Investigation.polling_unit_id == pu.id,
                                                Investigation.contest_id == contest.id))
    return {"polling_unit": pu_summary(pu), "contest": contest_summary(contest),
            "evaluation": engine.evaluate(db, pu, contest),
            "investigation": None if inv is None else {
                "id": inv.id, "status": inv.status, "outcome": inv.outcome, "findings": inv.findings,
                "public_summary": inv.public_summary, "assigned_reviewer_id": inv.assigned_reviewer_id,
                "approved_by_id": inv.approved_by_id, "updated_at": inv.updated_at}}


class InvestigationAction(BaseModel):
    action: str = Field(pattern="^(open|record|close|reopen)$")
    findings: str = Field(default="", max_length=5000)
    outcome: str | None = None
    public_summary: str = Field(default="", max_length=1000)


@router.post("/units/{pu_id}/{contest_id}/investigation")
def investigation(pu_id: int, contest_id: int, body: InvestigationAction, db: Session = Depends(get_db),
                  user: User = Depends(staff)):
    pu = get_or_404(db, PollingUnit, pu_id, "Polling unit")
    contest = get_or_404(db, Contest, contest_id, "Contest")
    inv = db.scalar(select(Investigation).where(Investigation.polling_unit_id == pu.id,
                                                Investigation.contest_id == contest.id))
    if body.action == "open":
        if inv and inv.status != "closed":
            raise HTTPException(400, "An investigation is already open")
        if inv is None:
            inv = Investigation(polling_unit_id=pu.id, contest_id=contest.id)
            db.add(inv)
        inv.status, inv.assigned_reviewer_id, inv.outcome = "open", user.id, None
        if body.findings:
            inv.findings = body.findings
        db.flush()
        audit.record(db, actor=user, entity_type="investigation", entity_id=inv.id, action="opened",
                     polling_unit_id=pu.id, public=True, actor_label="Verification team")
    else:
        if inv is None:
            raise HTTPException(400, "Open an investigation first")
        before = {"status": inv.status, "outcome": inv.outcome, "findings": inv.findings}
        if body.action == "record":
            inv.findings = body.findings
            action = "findings_recorded"
        elif body.action == "reopen":
            if user.role not in ("senior_reviewer", "admin"):
                raise HTTPException(403, "Only a senior reviewer can reopen a completed review")
            inv.status, action = "open", "reopened"
        else:
            if body.outcome not in OUTCOMES:
                raise HTTPException(400, "Choose an outcome")
            if not body.public_summary.strip():
                raise HTTPException(400, "Write a plain-language public summary")
            inv.findings = body.findings or inv.findings
            inv.outcome, inv.public_summary = body.outcome, body.public_summary
            needs_senior = body.outcome in SENSITIVE_OUTCOMES and user.role not in ("senior_reviewer", "admin")
            inv.status = "awaiting_approval" if needs_senior else "closed"
            if not needs_senior:
                inv.approved_by_id = user.id
            action = "submitted_for_approval" if needs_senior else "closed"
        audit.record(db, actor=user, entity_type="investigation", entity_id=inv.id, action=action, previous=before,
                     new={"status": inv.status, "outcome": inv.outcome, "findings": inv.findings},
                     polling_unit_id=pu.id, public=action in ("closed", "reopened"), actor_label="Verification team")
    engine.refresh(db, pu, contest, actor=user)
    db.commit()
    return unit_detail(pu_id, contest_id, db, user)


@router.post("/investigations/{inv_id}/approve")
def approve_investigation(inv_id: int, db: Session = Depends(get_db), user: User = Depends(senior)):
    inv = get_or_404(db, Investigation, inv_id, "Investigation")
    if inv.status != "awaiting_approval":
        raise HTTPException(400, "This investigation is not awaiting approval")
    if inv.assigned_reviewer_id == user.id:
        raise HTTPException(403, "A different senior reviewer must approve this outcome")
    inv.status, inv.approved_by_id = "closed", user.id
    audit.record(db, actor=user, entity_type="investigation", entity_id=inv.id, action="closed",
                 new={"outcome": inv.outcome, "approved_by": user.id}, polling_unit_id=inv.polling_unit_id,
                 public=True, actor_label="Senior reviewer")
    pu, contest = db.get(PollingUnit, inv.polling_unit_id), db.get(Contest, inv.contest_id)
    engine.refresh(db, pu, contest, actor=user)
    db.commit()
    return unit_detail(pu.id, contest.id, db, user)


@router.get("/investigations")
def list_investigations(status: str | None = None, db: Session = Depends(get_db), user: User = Depends(staff)):
    q = select(Investigation).order_by(Investigation.updated_at.desc())
    if status:
        q = q.where(Investigation.status == status)
    out = []
    for inv in db.scalars(q):
        pu = db.get(PollingUnit, inv.polling_unit_id)
        out.append({"id": inv.id, "status": inv.status, "outcome": inv.outcome, "contest_id": inv.contest_id,
                    "polling_unit": {"id": pu.id, "code": pu.official_code, "name": pu.official_name},
                    "updated_at": inv.updated_at})
    return out


# ------------------------------------------------------------------ official status checks

class OfficialStatusDecision(BaseModel):
    status: str = Field(pattern="^(verified|rejected|expired|revoked)$")
    note: str = Field(default="", max_length=500)


@router.get("/contributors")
def contributors(official_status: str | None = None, db: Session = Depends(get_db), user: User = Depends(staff)):
    q = select(ContributorProfile)
    if official_status:
        q = q.where(ContributorProfile.official_status == official_status)
    out = []
    for p in db.scalars(q):
        cls = classification.classify(p)
        out.append({"user_id": p.user_id, "name": p.user.name, "application_status": p.application_status,
                    "classification": cls, "classification_label": classification.label(cls, p.party_affiliation),
                    "official_role": p.official_role, "official_status": p.official_status,
                    "official_reference": p.official_reference, "party": p.party_affiliation,
                    "organisation": p.organisation.name if p.organisation else None})
    return out


@router.post("/contributors/{user_id}/official-status")
def decide_official_status(user_id: int, body: OfficialStatusDecision, db: Session = Depends(get_db),
                           user: User = Depends(staff)):
    """Record the result of checking a claim against the official INEC / party process."""
    p = get_or_404(db, ContributorProfile, user_id, "Contributor")
    if p.official_role == "none":
        raise HTTPException(400, "This contributor has not claimed an official role")
    if user_id == user.id:
        raise HTTPException(403, "You cannot verify your own status")
    before = {"status": p.official_status}
    p.official_status, p.official_verified_by_id = body.status, user.id
    audit.record(db, actor=user, entity_type="official_status", entity_id=user_id, action=body.status,
                 previous=before, new={"status": body.status, "note": body.note})
    db.commit()
    cls = classification.classify(p)
    return {"user_id": user_id, "official_status": p.official_status, "classification": cls,
            "classification_label": classification.label(cls, p.party_affiliation)}


# ------------------------------------------------------------------ audit

@router.get("/audit")
def audit_log(polling_unit_id: int | None = None, entity_type: str | None = None, limit: int = 200,
              db: Session = Depends(get_db), user: User = Depends(staff)):
    q = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(min(limit, 1000))
    if polling_unit_id:
        q = q.where(AuditEvent.polling_unit_id == polling_unit_id)
    if entity_type:
        q = q.where(AuditEvent.entity_type == entity_type)
    return [{"id": e.id, "at": e.timestamp, "actor": e.actor_label, "entity_type": e.entity_type,
             "entity_id": e.entity_id, "action": e.action, "previous": e.previous_value, "new": e.new_value,
             "event_hash": e.event_hash} for e in db.scalars(q)]


@router.get("/audit/verify")
def audit_verify(db: Session = Depends(get_db), user: User = Depends(staff)):
    ok, broken = audit.verify_chain(db)
    return {"intact": ok, "first_broken_event_id": broken}
