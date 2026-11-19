"""Electoral geography and polling-unit discovery (PRD §5.3)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..common import pu_summary
from ..db import get_db
from ..models import LGA, PollingUnit, State, Ward

router = APIRouter(tags=["geography"])


@router.get("/states")
def states(db: Session = Depends(get_db)):
    return [{"id": s.id, "code": s.code, "name": s.name} for s in db.scalars(select(State).order_by(State.name))]


@router.get("/lgas")
def lgas(state_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(LGA).where(LGA.state_id == state_id).order_by(LGA.code))
    return [{"id": l.id, "code": l.code, "name": l.name} for l in rows]


@router.get("/wards")
def wards(lga_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(Ward).where(Ward.lga_id == lga_id).order_by(Ward.code))
    return [{"id": w.id, "code": w.code, "name": w.name} for w in rows]


@router.get("/polling-units")
def polling_units(ward_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(PollingUnit).where(PollingUnit.ward_id == ward_id, PollingUnit.active)
                      .order_by(PollingUnit.unit_number))
    return [pu_summary(p) for p in rows]


@router.get("/polling-units/search")
def search(q: str = Query(min_length=2, max_length=80), db: Session = Depends(get_db)):
    """Search by official code, official name, community/landmark alias, ward or LGA name.

    Returns every candidate so the user can confirm the right unit (PRD §5.3).
    """
    term = f"%{q.strip().lower()}%"
    stmt = (select(PollingUnit).join(Ward, PollingUnit.ward_id == Ward.id).join(LGA, PollingUnit.lga_id == LGA.id)
            .where(PollingUnit.active, or_(
                func.lower(PollingUnit.official_code).like(term), func.lower(PollingUnit.official_name).like(term),
                func.lower(PollingUnit.aliases).like(term), func.lower(Ward.name).like(term),
                func.lower(LGA.name).like(term),
            )).order_by(PollingUnit.official_code).limit(50))
    results = []
    needle = q.strip().lower()
    for p in db.scalars(stmt):
        matched = next((a for a in p.aliases.split("|") if a and needle in a.lower()), None)
        results.append({**pu_summary(p), "matched_alias": matched})
    return results
