"""Append-only, hash-chained audit log.

Each event stores the hash of the previous event, so any later edit or deletion of a row
breaks the chain and is detectable with `verify_chain`. This is the MVP's form of
"signed or otherwise protected audit events" (PRD §14.2).
"""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditEvent, User

GENESIS = "0" * 64


def _digest(prev_hash: str, payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256((prev_hash + body).encode()).hexdigest()


def _payload(e: AuditEvent) -> dict:
    return {
        "actor_id": e.actor_id, "actor_label": e.actor_label, "entity_type": e.entity_type,
        "entity_id": e.entity_id, "action": e.action, "previous_value": e.previous_value,
        "new_value": e.new_value, "polling_unit_id": e.polling_unit_id, "public": e.public,
        "timestamp": _utc_naive(e.timestamp).isoformat(timespec="microseconds"),
    }


def _utc_naive(ts: datetime) -> datetime:
    # SQLite returns naive UTC, PostgreSQL returns aware; normalise both before hashing.
    return ts.astimezone(timezone.utc).replace(tzinfo=None) if ts.tzinfo else ts


def record(
    db: Session, *, actor: User | None, entity_type: str, entity_id, action: str,
    previous=None, new=None, polling_unit_id: int | None = None, public: bool = False,
    actor_label: str | None = None,
) -> AuditEvent:
    last = db.scalar(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1))
    prev_hash = last.event_hash if last else GENESIS
    event = AuditEvent(
        actor_id=actor.id if actor else None,
        actor_label=actor_label or (f"{actor.role}:{actor.id}" if actor else "system"),
        entity_type=entity_type, entity_id=str(entity_id), action=action,
        previous_value=previous, new_value=new, polling_unit_id=polling_unit_id, public=public,
        timestamp=datetime.now(timezone.utc), prev_hash=prev_hash, event_hash="",
    )
    event.event_hash = _digest(prev_hash, _payload(event))
    db.add(event)
    db.flush()
    return event


def verify_chain(db: Session) -> tuple[bool, int | None]:
    """Returns (ok, id_of_first_broken_event)."""
    prev = GENESIS
    for e in db.scalars(select(AuditEvent).order_by(AuditEvent.id)):
        if e.prev_hash != prev or _digest(prev, _payload(e)) != e.event_hash:
            return False, e.id
        prev = e.event_hash
    return True, None
