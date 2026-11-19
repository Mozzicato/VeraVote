"""Evidence comparison and status engine (PRD §9.4, §9.5, §10).

Everything here describes the *condition of the evidence*. Nothing here decides whether a
result is true, valid or fraudulent.
"""
from itertools import combinations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import (Contest, EvidenceComparison, EvidenceSubmission, Investigation, OfficialResultDocument,
                      PollingUnit, UnitStatus, User)
from . import arithmetic, audit, classification
from .extraction import field_spec

NO_EVIDENCE = "no_evidence"
RECEIVED = "evidence_received"
UNDER_REVIEW = "under_review"
CONSISTENT = "consistent_evidence"
DISCREPANCY = "discrepancy_detected"
INSUFFICIENT = "insufficient_evidence"
COMPLETED = "review_completed"

# PRD §10.3: plain language first.
STATUS_TEXT = {
    NO_EVIDENCE: ("No evidence yet",
                  "We have not received any usable evidence for this polling unit yet."),
    RECEIVED: ("Evidence received",
               "We have received evidence for this polling unit. It has not been reviewed yet."),
    UNDER_REVIEW: ("Under review",
                   "Our verification team is examining the evidence for this polling unit."),
    CONSISTENT: ("Records agree",
                 "The reviewed records we have for this polling unit show the same figures."),
    DISCREPANCY: ("Records differ",
                  "These result documents show different figures. Our verification team is examining the difference."),
    INSUFFICIENT: ("Not enough evidence to compare",
                   "We currently have only one usable record. We cannot yet compare it with another independent source."),
    COMPLETED: ("Review completed",
                "Our verification team has finished its documented review of this polling unit."),
}

DISCLAIMER = ("These labels describe the evidence VeraVote holds. They are not a ruling on whether the "
              "election result is legally valid, and VeraVote does not declare winners.")


def _submission_source(s: EvidenceSubmission) -> dict:
    comparable = s.submission_status == "accepted" and s.extraction_status == "confirmed"
    values = {f.field_key: f.value for f in s.fields} if comparable else {}
    return {
        "ref": f"submission:{s.id}", "kind": "submission", "id": s.id,
        "classification": s.contributor_classification,
        "label": classification.label(s.contributor_classification, s.party_affiliation),
        "contributor_id": s.contributor_id, "organisation_id": s.organisation_id,
        "organisation_name": s.organisation.name if s.organisation else None,
        "file_hash": s.file_hash, "is_forwarded_copy": s.is_forwarded_copy,
        "status": s.submission_status, "extraction_status": s.extraction_status,
        "received_at": s.server_received_time, "comparable": comparable, "values": values,
        "arithmetic_flags": arithmetic.check(values) if comparable else [],
    }


def _official_source(d: OfficialResultDocument) -> dict:
    comparable = d.is_current and d.extraction_status == "confirmed"
    values = {f.field_key: f.value for f in d.fields} if comparable else {}
    return {
        "ref": f"official:{d.id}", "kind": "official", "id": d.id,
        "classification": classification.OFFICIAL,
        "label": f"Official result document, {d.source_platform}",
        "contributor_id": None, "organisation_id": None, "organisation_name": None,
        "file_hash": d.file_hash, "is_forwarded_copy": "no", "status": "current" if d.is_current else "superseded",
        "extraction_status": d.extraction_status, "received_at": d.retrieved_at, "comparable": comparable,
        "values": values, "arithmetic_flags": arithmetic.check(values) if comparable else [],
        "source_reference": d.source_reference, "version_reference": d.version_reference,
    }


def _documents(sources: list[dict]) -> list[dict]:
    """Group comparable sources into distinct original documents (same file hash = same document)."""
    docs: dict[str, dict] = {}
    for s in sources:
        if not s["comparable"]:
            continue
        key = s["ref"] if s["kind"] == "official" or not s["file_hash"] else f"file:{s['file_hash']}"
        label = f"{s['label']}, {s['organisation_name']}" if s.get("organisation_name") else s["label"]
        doc = docs.setdefault(key, {"key": key, "kind": s["kind"], "sources": [], "values": s["values"],
                                    "contributors": set(), "organisations": set(), "forwarded": False,
                                    "label": label})
        doc["sources"].append(s["ref"])
        if s["contributor_id"]:
            doc["contributors"].add(s["contributor_id"])
        if s["organisation_id"]:
            doc["organisations"].add(s["organisation_id"])
        doc["forwarded"] |= s["is_forwarded_copy"] == "yes"
    return list(docs.values())


def _independent(a: dict, b: dict) -> bool:
    if "official" in (a["kind"], b["kind"]):
        return True
    if a["forwarded"] or b["forwarded"]:
        return False
    return not (a["contributors"] & b["contributors"]) and not (a["organisations"] & b["organisations"])


def _compare(a: dict, b: dict, labels: dict[str, str]) -> dict:
    diffs, compared = [], 0
    for key, lbl in labels.items():
        va, vb = a["values"].get(key), b["values"].get(key)
        if va is None or vb is None:
            continue
        compared += 1
        if va != vb:
            diffs.append({"field_key": key, "label": lbl, "a": va, "b": vb, "difference": vb - va})
    result = "not_comparable" if compared == 0 else ("differ" if diffs else "agree")
    return {"a": a["key"], "b": b["key"], "a_label": a["label"], "b_label": b["label"], "result": result,
            "independent": _independent(a, b), "fields_compared": compared, "differences": diffs}


def _independence(sources: list[dict], docs: list[dict]) -> dict:
    subs = [s for s in sources if s["kind"] == "submission" and s["status"] != "rejected"]
    hashes = [s["file_hash"] for s in subs if s["file_hash"]]
    contributors = {s["contributor_id"] for s in subs if s["contributor_id"]}
    orgs = {s["organisation_id"] for s in subs if s["organisation_id"]}
    notes = []
    for h in set(hashes):
        if (n := hashes.count(h)) > 1:
            notes.append(f"{n} submissions share an identical file fingerprint, so they count as one document.")
    forwarded = sum(1 for s in subs if s["is_forwarded_copy"] == "yes")
    if forwarded:
        notes.append(f"{forwarded} submission(s) were declared as forwarded copies, not first-hand captures.")
    by_org: dict[int, int] = {}
    for s in subs:
        if s["organisation_id"]:
            by_org[s["organisation_id"]] = by_org.get(s["organisation_id"], 0) + 1
    for org_id, n in by_org.items():
        if n > 1:
            name = next(s["organisation_name"] for s in subs if s["organisation_id"] == org_id)
            notes.append(f"{n} submissions come from contributors of the same organisation ({name}).")

    independent_docs = 0
    for d in docs:
        if all(_independent(d, other) for other in docs if other is not d) or len(docs) == 1:
            independent_docs += 1
    return {
        "submissions": len(subs),
        "distinct_contributors": len(contributors),
        "distinct_organisations": len(orgs),
        "distinct_documents": len(set(hashes)) + sum(1 for s in subs if not s["file_hash"]),
        "official_documents": sum(1 for s in sources if s["kind"] == "official" and s["status"] == "current"),
        "comparable_documents": len(docs),
        "notes": notes,
    }


def evaluate(db: Session, pu: PollingUnit, contest: Contest) -> dict:
    subs = db.scalars(select(EvidenceSubmission).where(
        EvidenceSubmission.polling_unit_id == pu.id, EvidenceSubmission.contest_id == contest.id,
    ).order_by(EvidenceSubmission.id)).all()
    officials = db.scalars(select(OfficialResultDocument).where(
        OfficialResultDocument.polling_unit_id == pu.id, OfficialResultDocument.contest_id == contest.id,
    ).order_by(OfficialResultDocument.id)).all()
    investigation = db.scalar(select(Investigation).where(
        Investigation.polling_unit_id == pu.id, Investigation.contest_id == contest.id))

    sources = [_submission_source(s) for s in subs] + [_official_source(d) for d in officials]
    labels = dict(field_spec(contest))
    docs = _documents(sources)
    comparisons = [_compare(a, b, labels) for a, b in combinations(docs, 2)]
    live = [s for s in sources if s["status"] not in ("rejected", "superseded")]

    has_discrepancy = any(c["result"] == "differ" for c in comparisons)
    independent_agreement = any(c["result"] == "agree" and c["independent"] for c in comparisons)
    pending_leads = [s for s in live if s["classification"] == classification.CITIZEN and not s["comparable"]]
    in_review = any(s["status"] == "under_review" for s in live) or (
        investigation is not None and investigation.status != "closed")

    if investigation is not None and investigation.status == "closed":
        status = COMPLETED
    elif not live:
        status = NO_EVIDENCE
    elif has_discrepancy:
        status = DISCREPANCY
    elif in_review:
        status = UNDER_REVIEW
    elif independent_agreement:
        status = CONSISTENT
    elif docs:
        status = INSUFFICIENT
    else:
        status = RECEIVED

    title, explanation = STATUS_TEXT[status]
    extra = []
    if status == DISCREPANCY:
        extra.append("A difference in the records is not, by itself, proof of wrongdoing. Human review is required.")
    if pending_leads:
        extra.append(f"{len(pending_leads)} citizen-submitted lead(s) are pending verification and are not yet counted.")
    if status == COMPLETED and investigation.public_summary:
        extra.append(investigation.public_summary)
    flags = [{"source": s["ref"], "label": s["label"], **f} for s in sources for f in s["arithmetic_flags"]]
    if flags:
        extra.append("At least one record does not add up and has been flagged for review.")

    return {
        "status": status, "status_title": title, "explanation": explanation, "notes": extra,
        "disclaimer": DISCLAIMER, "fields": [{"key": k, "label": l} for k, l in field_spec(contest)],
        "sources": sources, "documents": [{**d, "contributors": len(d["contributors"]),
                                           "organisations": len(d["organisations"])} for d in docs],
        "comparisons": comparisons, "independence": _independence(sources, docs),
        "arithmetic_flags": flags,
        "investigation": None if investigation is None else {
            "id": investigation.id, "status": investigation.status, "outcome": investigation.outcome,
            "public_summary": investigation.public_summary,
        },
    }


def refresh(db: Session, pu: PollingUnit, contest: Contest, actor: User | None = None) -> dict:
    """Recompute, persist comparisons, and log public status changes to the audit trail."""
    result = evaluate(db, pu, contest)
    db.execute(delete(EvidenceComparison).where(
        EvidenceComparison.polling_unit_id == pu.id, EvidenceComparison.contest_id == contest.id))
    for c in result["comparisons"]:
        db.add(EvidenceComparison(polling_unit_id=pu.id, contest_id=contest.id, source_a=c["a"], source_b=c["b"],
                                  result=c["result"], discrepancy_details=c["differences"]))
    current = db.get(UnitStatus, (pu.id, contest.id))
    previous = current.status if current else None
    if previous != result["status"]:
        if current:
            current.status = result["status"]
        else:
            db.add(UnitStatus(polling_unit_id=pu.id, contest_id=contest.id, status=result["status"]))
        audit.record(db, actor=actor, entity_type="polling_unit_status", entity_id=f"{pu.id}:{contest.id}",
                     action="status_changed", previous={"status": previous}, new={"status": result["status"]},
                     polling_unit_id=pu.id, public=True)
    db.flush()
    return result
