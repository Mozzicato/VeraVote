"""Shared helpers for routers."""
import secrets

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Contest, PollingUnit


def get_or_404(db: Session, model, ident, what: str = "Record"):
    obj = db.get(model, ident)
    if obj is None:
        raise HTTPException(404, f"{what} not found")
    return obj


def new_receipt() -> str:
    return "VV-" + secrets.token_hex(4).upper()


def pu_summary(pu: PollingUnit) -> dict:
    return {
        "id": pu.id, "official_code": pu.official_code, "official_name": pu.official_name,
        "unit_number": pu.unit_number, "location_description": pu.location_description,
        "aliases": [a for a in pu.aliases.split("|") if a],
        "ward": {"id": pu.ward.id, "name": pu.ward.name, "code": pu.ward.code},
        "lga": {"id": pu.lga.id, "name": pu.lga.name, "code": pu.lga.code},
        "state": {"id": pu.state.id, "name": pu.state.name, "code": pu.state.code},
        "latitude": pu.latitude, "longitude": pu.longitude, "active": pu.active,
        "dataset_source": pu.dataset_source, "dataset_version": pu.dataset_version,
        "last_verified": pu.last_verified, "is_simulated": pu.is_simulated,
    }


def all_contests(db: Session) -> list[Contest]:
    return list(db.scalars(select(Contest).order_by(Contest.id)))


def contest_summary(c: Contest) -> dict:
    return {"id": c.id, "office": c.office, "constituency": c.constituency,
            "election": {"id": c.election.id, "name": c.election.name, "date": c.election.election_date,
                         "is_simulated": c.election.is_simulated},
            "candidates": [{"id": x.id, "party": x.party, "name": x.name} for x in c.candidates]}
