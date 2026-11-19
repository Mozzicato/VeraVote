"""Demo-only helpers: the role switcher and a data reset. Disabled outside simulated mode."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import SIMULATED_MODE
from ..db import get_db
from ..models import User
from ..services import classification

router = APIRouter(prefix="/demo", tags=["demo"])

PERSONA = {
    "Amaka Obi": "Citizen (no account needed to browse)",
    "Tunde Bakare": "VeraVote-trained community contributor",
    "Ngozi Eze": "Accredited observer, Transparency Watch",
    "Ibrahim Sani": "Accredited observer, Citizens' Election Forum",
    "Emeka Nwosu": "Accredited observer, Transparency Watch",
    "Halima Yusuf": "Accredited observer, Citizens' Election Forum",
    "Kemi Alade": "Party agent (APX)",
    "Ade Ojo": "Volunteer applicant, mid-training",
    "Funke Adebayo": "Organisation coordinator",
    "Chika Umeh": "Verification officer",
    "Yusuf Garba": "Senior reviewer",
    "Platform Admin": "Platform administrator",
}


def _guard():
    if not SIMULATED_MODE:
        raise HTTPException(404)


@router.get("/users")
def users(db: Session = Depends(get_db)):
    _guard()
    out = []
    for u in db.scalars(select(User).order_by(User.id)):
        cls = classification.classify(u.profile)
        out.append({"id": u.id, "name": u.name, "role": u.role, "persona": PERSONA.get(u.name, u.role),
                    "classification": cls,
                    "organisation_id": u.profile.organisation_id if u.profile else None})
    return out


@router.post("/reset")
def reset():
    _guard()
    from ..seed import reset as do_reset
    do_reset()
    return {"ok": True, "message": "Simulated demo data restored."}
