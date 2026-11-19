"""Public evidence explorer and citizen evidence leads (PRD §10, §13). No account needed."""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..common import all_contests, contest_summary, get_or_404, pu_summary
from ..db import get_db
from ..deps import current_user_optional
from ..models import (AuditEvent, Contest, EvidenceSubmission, OfficialResultDocument, PollingUnit, UnitStatus,
                      User)
from ..services import engine, intake
from ..services.storage import storage

router = APIRouter(prefix="/public", tags=["public"])

PUBLIC_EVENT_TEXT = {
    ("evidence_submission", "received"): "Evidence received",
    ("evidence_submission", "accepted"): "Evidence accepted for comparison after review",
    ("evidence_submission", "rejected"): "Evidence reviewed and not used",
    ("evidence_submission", "review_started"): "Verification team started reviewing evidence",
    ("evidence_submission", "info_requested"): "Verification team asked for more information",
    ("evidence_submission", "unresolved_lead"): "Lead kept on file as unresolved",
    ("official_document", "attached"): "Official result document attached",
    ("investigation", "opened"): "Investigation opened",
    ("investigation", "closed"): "Review completed",
    ("investigation", "correction_published"): "Public correction published",
}


def _public_source(s: dict) -> dict:
    """Strip anything that could identify a contributor (PRD §10.2, §14.1)."""
    keep = ("ref", "kind", "id", "classification", "label", "organisation_name", "file_hash", "is_forwarded_copy",
            "status", "received_at", "comparable", "values", "arithmetic_flags", "source_reference",
            "version_reference")
    out = {k: s.get(k) for k in keep}
    out["file_available"] = s["comparable"] and bool(s["file_hash"])
    return out


def _timeline(db: Session, pu_id: int) -> list[dict]:
    events = db.scalars(select(AuditEvent).where(AuditEvent.polling_unit_id == pu_id, AuditEvent.public)
                        .order_by(AuditEvent.timestamp, AuditEvent.id))
    out = []
    for e in events:
        if e.entity_type == "polling_unit_status":
            title, _ = engine.STATUS_TEXT.get((e.new_value or {}).get("status"), ("Status changed", ""))
            text = f"Public status changed to “{title}”"
        else:
            text = PUBLIC_EVENT_TEXT.get((e.entity_type, e.action), e.action.replace("_", " ").capitalize())
        out.append({"at": e.timestamp, "event": text, "by": e.actor_label if e.entity_type != "polling_unit_status"
                    else "VeraVote", "event_hash": e.event_hash})
    return out


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(UnitStatus.status, func.count()).group_by(UnitStatus.status)).all())
    total = db.scalar(select(func.count()).select_from(PollingUnit).where(PollingUnit.active))
    contests = all_contests(db)
    statuses = {(r.polling_unit_id, r.contest_id): r.status for r in db.scalars(select(UnitStatus))}
    first = contests[0].id if contests else None
    # One entry per unit for the coverage strip. A nationwide build would aggregate by LGA instead.
    units = [{"id": p.id, "code": p.official_code, "name": p.official_name, "lga": p.lga.name,
              "status": statuses.get((p.id, first), engine.NO_EVIDENCE)}
             for p in db.scalars(select(PollingUnit).where(PollingUnit.active).order_by(PollingUnit.official_code))]
    return {"polling_units": total, "status_counts": counts, "simulated": True, "units": units,
            "contests": [contest_summary(c) for c in contests]}


@router.get("/polling-units/{pu_id}")
def polling_unit(pu_id: int, db: Session = Depends(get_db)):
    pu = get_or_404(db, PollingUnit, pu_id, "Polling unit")
    contests = []
    for c in all_contests(db):
        r = engine.evaluate(db, pu, c)
        r["sources"] = [_public_source(s) for s in r["sources"]]
        contests.append({"contest": contest_summary(c), **r})
    return {"polling_unit": pu_summary(pu), "contests": contests, "timeline": _timeline(db, pu.id),
            "simulated": pu.is_simulated}


@router.get("/discrepancies")
def discrepancies(db: Session = Depends(get_db)):
    rows = db.scalars(select(UnitStatus).where(UnitStatus.status == engine.DISCREPANCY))
    out = []
    for row in rows:
        pu, c = db.get(PollingUnit, row.polling_unit_id), db.get(Contest, row.contest_id)
        r = engine.evaluate(db, pu, c)
        diffs = [d for cmp in r["comparisons"] if cmp["result"] == "differ" for d in cmp["differences"]]
        out.append({"polling_unit": pu_summary(pu), "contest": contest_summary(c), "status_title": r["status_title"],
                    "explanation": r["explanation"], "largest_difference": max((abs(d["difference"]) for d in diffs),
                                                                               default=0),
                    "fields_affected": sorted({d["label"] for d in diffs}), "since": row.updated_at})
    return out


@router.get("/files/{kind}/{ident}")
def file(kind: str, ident: int, db: Session = Depends(get_db)):
    """Original evidence file, only once it has been accepted for comparison or is an official document."""
    if kind == "submission":
        obj = get_or_404(db, EvidenceSubmission, ident, "Submission")
        if obj.submission_status != "accepted":
            raise HTTPException(404, "This file is not publicly available")
        ctype = obj.content_type
    elif kind == "official":
        obj = get_or_404(db, OfficialResultDocument, ident, "Document")
        ctype = "image/svg+xml" if (obj.original_file_key or "").endswith(".svg") else "image/png"
    else:
        raise HTTPException(404, "Unknown file kind")
    if not obj.original_file_key:
        raise HTTPException(404, "No file")
    return Response(storage.read(obj.original_file_key), media_type=ctype or "application/octet-stream",
                    headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
                             "X-Content-Type-Options": "nosniff", "X-Evidence-SHA256": obj.file_hash or ""})


@router.post("/evidence-leads")
async def evidence_lead(
    polling_unit_id: int = Form(...), contest_id: int = Form(...),
    evidence_type: str = Form(...), description: str = Form(""), source_url: str | None = Form(None),
    follow_up_contact: str | None = Form(None), is_forwarded_copy: str = Form("unknown"),
    accepted_notice: bool = Form(...), client_submission_id: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db), user: User | None = Depends(current_user_optional),
):
    """Citizen evidence lead (PRD §13). Enters a separate queue; never auto-published as verified."""
    if not accepted_notice:
        raise HTTPException(400, "Please accept the evidence-submission notice")
    if evidence_type not in ("result_sheet_photo", "result_poster_photo", "public_link", "other_info"):
        raise HTTPException(400, "Unknown evidence type")
    if is_forwarded_copy not in ("yes", "no", "unknown"):
        raise HTTPException(400, "is_forwarded_copy must be yes, no or unknown")
    if source_url and not source_url.startswith(("http://", "https://")):
        raise HTTPException(400, "Links must start with http:// or https://")
    has_file = file is not None and file.filename
    if not has_file and not source_url and not description.strip():
        raise HTTPException(400, "Add a photo, a link or a description")
    if client_submission_id and (prev := intake.existing(db, client_submission_id)):
        return intake.receipt(prev, duplicate_retry=True)

    pu = get_or_404(db, PollingUnit, polling_unit_id, "Polling unit")
    contest = get_or_404(db, Contest, contest_id, "Contest")
    upload = await intake.read_upload(file) if has_file else None
    sub = intake.create(
        db, client_submission_id=client_submission_id or f"lead-{uuid.uuid4()}", category="citizen_lead",
        user=user, pu=pu, contest=contest, evidence_type=evidence_type, upload=upload,
        filename=file.filename if has_file else None, source_url=source_url, description=description[:2000],
        follow_up_contact=(follow_up_contact or None) and follow_up_contact[:200],
        is_forwarded_copy=is_forwarded_copy,
    )
    db.commit()
    return intake.receipt(sub)


@router.get("/receipts/{code}")
def receipt_status(code: str, db: Session = Depends(get_db)):
    sub = db.scalar(select(EvidenceSubmission).where(EvidenceSubmission.receipt_code == code.upper()))
    if sub is None:
        raise HTTPException(404, "No submission with that reference")
    return intake.receipt(sub)
