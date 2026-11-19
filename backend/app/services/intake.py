"""Evidence intake shared by field submissions and citizen leads (PRD §7.2, §8.2, §13)."""
from datetime import datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..common import new_receipt
from ..config import MAX_UPLOAD_BYTES
from ..models import Contest, EvidenceSubmission, PollingUnit, User
from . import audit, classification, engine, extraction
from .storage import storage

# Detect the real type from the file's first bytes rather than trusting the client.
MAGIC = [
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"%PDF-", "application/pdf", ".pdf"),
]


def sniff(data: bytes) -> tuple[str, str]:
    for magic, ctype, ext in MAGIC:
        if data.startswith(magic):
            return ctype, ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    raise HTTPException(415, "Upload a JPEG, PNG, WebP image or a PDF")


async def read_upload(file: UploadFile) -> tuple[bytes, str, str]:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    if not data:
        raise HTTPException(400, "The file is empty")
    ctype, ext = sniff(data)
    # Malware scanning hook (PRD §14.2) goes here before the file is stored.
    return data, ctype, ext


def existing(db: Session, client_submission_id: str) -> EvidenceSubmission | None:
    return db.scalar(select(EvidenceSubmission).where(
        EvidenceSubmission.client_submission_id == client_submission_id))


def create(
    db: Session, *, client_submission_id: str, category: str, user: User | None, pu: PollingUnit,
    contest: Contest, evidence_type: str, upload: tuple[bytes, str, str] | None, filename: str | None,
    source_url: str | None = None, description: str = "", follow_up_contact: str | None = None,
    is_forwarded_copy: str = "unknown", device_reported_time: datetime | None = None,
    captured_offline: bool = False, assignment_id: int | None = None,
) -> EvidenceSubmission:
    profile = user.profile if user else None
    cls = classification.CITIZEN if category == "citizen_lead" else classification.classify(profile)
    key = digest = ctype = None
    size = None
    if upload:
        data, ctype, ext = upload
        key, digest = storage.put_original(data, ext)
        size = len(data)

    sub = EvidenceSubmission(
        client_submission_id=client_submission_id, receipt_code=new_receipt(), source_category=category,
        contributor_id=user.id if user else None, contributor_classification=cls,
        party_affiliation=profile.party_affiliation if profile and cls == classification.PARTY_AGENT else None,
        organisation_id=profile.organisation_id if profile and category == "field" else None,
        assignment_id=assignment_id, polling_unit_id=pu.id, election_id=contest.election_id, contest_id=contest.id,
        evidence_type=evidence_type, original_file_key=key, original_filename=(filename or "")[:200] or None,
        content_type=ctype, file_size=size, file_hash=digest, source_url=source_url, description=description,
        follow_up_contact=follow_up_contact, is_forwarded_copy=is_forwarded_copy,
        device_reported_time=device_reported_time, captured_offline=captured_offline,
        submission_status="awaiting_review",
    )
    db.add(sub)
    db.flush()
    db.refresh(sub)

    dupes = []
    if digest:
        dupes = [s.receipt_code for s in db.scalars(select(EvidenceSubmission).where(
            EvidenceSubmission.file_hash == digest, EvidenceSubmission.id != sub.id))]
    audit.record(db, actor=user, entity_type="evidence_submission", entity_id=sub.id, action="received",
                 new={"receipt": sub.receipt_code, "file_hash": digest, "classification": cls,
                      "captured_offline": captured_offline, "identical_file_receipts": dupes},
                 polling_unit_id=pu.id, public=True, actor_label=classification.SHORT_LABELS[cls])
    if upload and ctype and ctype.startswith("image/"):
        extraction.run_for_submission(db, sub)
    engine.refresh(db, pu, contest, actor=user)
    return sub


def receipt(sub: EvidenceSubmission, duplicate_retry: bool = False) -> dict:
    """The submission receipt (PRD §7.2 step 9). Device time is labelled as unverified."""
    return {
        "receipt_code": sub.receipt_code, "submission_id": sub.id,
        "client_submission_id": sub.client_submission_id,
        "polling_unit": {"id": sub.polling_unit.id, "code": sub.polling_unit.official_code,
                         "name": sub.polling_unit.official_name},
        "contest_id": sub.contest_id, "classification": sub.contributor_classification,
        "classification_label": classification.label(sub.contributor_classification, sub.party_affiliation),
        "file_sha256": sub.file_hash, "file_size": sub.file_size,
        "server_received_time": sub.server_received_time,
        "device_reported_time": sub.device_reported_time,
        "device_time_note": "Device-reported time comes from the phone's clock and is not independently verified.",
        "captured_offline": sub.captured_offline, "status": sub.submission_status,
        "duplicate_retry": duplicate_retry,
        "hash_note": ("The SHA-256 fingerprint lets anyone check this file has not changed since we received it. "
                      "It does not prove where or when the photo was taken."),
    }
