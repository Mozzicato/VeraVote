"""Result-form extraction.

The MVP uses *controlled simulated extraction* (PRD §21 D): figures come from the simulated
demo sheet for the polling unit, and one field (picked from the file hash) is deliberately
misread with low confidence so the human-correction flow can be demonstrated. A real OCR
engine (PaddleOCR / Tesseract) plugs in by implementing `propose_values`.

Extraction output is always a *proposal*. It never touches the original file.
"""
from sqlalchemy.orm import Session

from .. import demo_data
from ..models import Contest, EvidenceSubmission, ExtractedField, OfficialResultDocument, PollingUnit

LOW_CONFIDENCE = 0.8  # fields below this are sent for human review (PRD §9.1 step 9)


def field_spec(contest: Contest) -> list[tuple[str, str]]:
    """Ordered (field_key, label) pairs for a contest's result form."""
    spec = [("accredited", "Number of accredited voters")]
    spec += [(f"cand:{c.id}", f"{c.name} ({c.party})") for c in contest.candidates]
    spec += [("total_valid", "Total valid votes"), ("rejected", "Rejected votes"), ("total_cast", "Total votes cast")]
    return spec


def sheet_values(contest: Contest, sheet: dict, party_delta: dict[str, int] | None = None) -> dict[str, int]:
    delta = party_delta or {}
    values = {"accredited": sheet["accredited"], "rejected": sheet["rejected"]}
    total = 0
    for c in contest.candidates:
        v = sheet["votes"][c.party] + delta.get(c.party, 0)
        values[f"cand:{c.id}"] = v
        total += v
    values["total_valid"] = total
    values["total_cast"] = total + sheet["rejected"]
    return values


def _misread(value: int) -> int:
    """A plausible OCR slip: swap the last two digits, or turn a 1 into a 7."""
    s = str(value)
    if len(s) >= 2 and s[-1] != s[-2]:
        return int(s[:-2] + s[-1] + s[-2])
    return int(s.replace("1", "7", 1)) if "1" in s else value + 10


def propose_values(pu: PollingUnit, contest: Contest, file_hash: str | None) -> list[dict]:
    spec = field_spec(contest)
    sheet = demo_data.SHEETS.get(pu.official_code)
    if sheet is None:
        # No simulated sheet: reviewer enters figures manually from the original.
        return [{"key": k, "label": l, "value": None, "confidence": 0.0, "method": "manual"} for k, l in spec]

    values = sheet_values(contest, sheet)
    slip_index = int(file_hash[:2], 16) % len(spec) if file_hash else -1
    proposals = []
    for i, (key, lbl) in enumerate(spec):
        value, conf = values[key], 0.93 + (i % 3) * 0.02
        if i == slip_index:
            value, conf = _misread(value), 0.52
        proposals.append({"key": key, "label": lbl, "value": value, "confidence": round(conf, 2), "method": "simulated"})
    return proposals


def run_for_submission(db: Session, sub: EvidenceSubmission) -> None:
    if sub.fields:
        return  # extraction already exists; never re-run over reviewed figures
    for pos, p in enumerate(propose_values(sub.polling_unit, sub.contest, sub.file_hash)):
        db.add(ExtractedField(submission_id=sub.id, field_key=p["key"], label=p["label"], position=pos,
                              extracted_value=p["value"], confidence=p["confidence"], method=p["method"]))
    sub.extraction_status = "proposed"
    db.flush()
    db.refresh(sub)


def attach_fields(db: Session, *, owner: EvidenceSubmission | OfficialResultDocument, contest: Contest,
                  values: dict[str, int], status: str = "confirmed", method: str = "simulated") -> None:
    """Directly attach known figures (seed data, or an official document entered by a reviewer)."""
    is_sub = isinstance(owner, EvidenceSubmission)
    for pos, (key, lbl) in enumerate(field_spec(contest)):
        db.add(ExtractedField(
            submission_id=owner.id if is_sub else None,
            official_document_id=None if is_sub else owner.id,
            field_key=key, label=lbl, position=pos, extracted_value=values.get(key),
            confidence=0.97, status=status, method=method,
        ))
    owner.extraction_status = "confirmed" if status in ("confirmed", "corrected") else "proposed"
    db.flush()
    db.refresh(owner)
