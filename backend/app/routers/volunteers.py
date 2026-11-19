"""Volunteer application, identity (simulated), training and assessment (PRD §4)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import ASSESSMENT_PASS_MARK
from ..db import get_db
from ..deps import current_user
from ..models import AssessmentAttempt, ContributorProfile, LGA, Organisation, State, User
from ..services import audit, classification, training

router = APIRouter(prefix="/volunteers", tags=["volunteers"])

SIMULATED_OTP = "123456"
MAX_ATTEMPTS = 3

NEXT_STEP = {
    "identity_verification_pending": "Verify your phone number",
    "training_pending": "Complete the five training modules",
    "assessment_pending": "Take the assessment",
    "approved": "Request a polling-unit assignment",
    "rejected": "Your application was not approved",
    "suspended": "Your account is suspended. Contact support.",
    "withdrawn": "You withdrew your application",
}


class Application(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    email: str | None = Field(default=None, max_length=200)
    state_id: int
    lga_id: int
    accept_code_of_conduct: bool


class OTP(BaseModel):
    code: str


class Answers(BaseModel):
    answers: dict[str, int]


class OfficialClaim(BaseModel):
    role: str = Field(pattern="^(accredited_observer|party_agent)$")
    reference: str = Field(min_length=3, max_length=120)
    organisation_id: int | None = None
    party: str | None = Field(default=None, max_length=60)


def _profile(user: User) -> ContributorProfile:
    if user.profile is None:
        raise HTTPException(400, "You have not applied to be a volunteer")
    return user.profile


def status_view(user: User) -> dict:
    p = user.profile
    cls = classification.classify(p)
    return {
        "user": {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role,
                 "phone_verified": user.phone_verified},
        "application_status": p.application_status if p else None,
        "next_step": NEXT_STEP.get(p.application_status, "") if p else "Apply to become a volunteer",
        "identity_status": p.identity_status if p else None,
        "training_status": p.training_status if p else None,
        "training_modules_completed": p.training_modules_completed if p else [],
        "assessment_status": p.assessment_status if p else None,
        "assessment_score": p.assessment_score if p else None,
        "classification": cls, "classification_label": classification.label(cls, p.party_affiliation if p else None),
        "official": None if not p else {
            "role": p.official_role, "status": p.official_status, "reference": p.official_reference,
            "party": p.party_affiliation,
            "note": "Official accreditation is established through INEC's own process. VeraVote training does not "
                    "grant it.",
        },
        "organisation": None if not p or not p.organisation else {"id": p.organisation.id, "name": p.organisation.name},
        "can_submit_field_evidence": cls in classification.FIELD_CLASSIFICATIONS,
    }


@router.post("/apply")
def apply(body: Application, db: Session = Depends(get_db)):
    if not body.accept_code_of_conduct:
        raise HTTPException(400, "You must accept the volunteer code of conduct")
    if db.scalar(select(User).where(User.phone == body.phone)):
        # PRD §19: two accounts with the same phone number.
        raise HTTPException(409, "This phone number is already registered")
    lga = db.get(LGA, body.lga_id)
    if not db.get(State, body.state_id) or not lga or lga.state_id != body.state_id:
        raise HTTPException(400, "Choose a valid state and LGA")
    user = User(name=body.name.strip(), phone=body.phone, email=body.email, role="volunteer")
    db.add(user)
    db.flush()
    db.add(ContributorProfile(user_id=user.id, application_status="identity_verification_pending",
                              preferred_state_id=body.state_id, preferred_lga_id=body.lga_id,
                              code_of_conduct_accepted_at=datetime.now(timezone.utc)))
    audit.record(db, actor=user, entity_type="volunteer_application", entity_id=user.id, action="submitted")
    db.commit()
    db.refresh(user)
    return {**status_view(user), "simulated_otp_hint": f"Demo mode: the code is {SIMULATED_OTP}"}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return status_view(user)


@router.post("/verify-phone")
def verify_phone(body: OTP, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = _profile(user)
    if body.code != SIMULATED_OTP:
        raise HTTPException(400, "That code is not correct")
    user.phone_verified = True
    p.identity_status = "verified"
    if p.application_status == "identity_verification_pending":
        p.application_status = "training_pending"
        p.training_status = "in_progress"
    audit.record(db, actor=user, entity_type="volunteer_application", entity_id=user.id,
                 action="identity_verified", new={"method": "phone_otp_simulated"})
    db.commit()
    return status_view(user)


@router.get("/training")
def training_modules(user: User = Depends(current_user)):
    done = set(user.profile.training_modules_completed if user.profile else [])
    return [{**m, "completed": m["id"] in done} for m in training.MODULES]


@router.post("/training/{module_id}/complete")
def complete_module(module_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = _profile(user)
    if p.identity_status != "verified":
        raise HTTPException(400, "Verify your phone number first")
    if module_id not in {m["id"] for m in training.MODULES}:
        raise HTTPException(404, "Unknown module")
    done = list(dict.fromkeys([*p.training_modules_completed, module_id]))
    p.training_modules_completed = done
    if len(done) == len(training.MODULES):
        p.training_status = "completed"
        if p.application_status == "training_pending":
            p.application_status = "assessment_pending"
    db.commit()
    return status_view(user)


@router.get("/assessment")
def assessment(user: User = Depends(current_user)):
    p = _profile(user)
    if p.training_status != "completed":
        raise HTTPException(400, "Complete all training modules first")
    return {"pass_mark": ASSESSMENT_PASS_MARK, "questions": training.public_questions(),
            "code_of_conduct_reminder": "By submitting you confirm you will stay neutral, never interfere, and "
                                        "put your safety first."}


@router.post("/assessment")
def submit_assessment(body: Answers, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = _profile(user)
    if p.training_status != "completed":
        raise HTTPException(400, "Complete all training modules first")
    if p.application_status == "approved":
        raise HTTPException(400, "You have already passed")
    attempts = len(db.scalars(select(AssessmentAttempt).where(AssessmentAttempt.user_id == user.id)).all())
    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(400, "You have used all assessment attempts. A reviewer will contact you.")
    score, passed, wrong = training.score(body.answers)
    db.add(AssessmentAttempt(user_id=user.id, score=score, passed=passed, answers=body.answers))
    p.assessment_score = score
    p.assessment_status = "passed" if passed else "failed"
    if passed:
        p.application_status = "approved"
    audit.record(db, actor=user, entity_type="volunteer_application", entity_id=user.id,
                 action="assessment_passed" if passed else "assessment_failed", new={"score": score})
    db.commit()
    return {**status_view(user), "score": score, "passed": passed, "incorrect": wrong,
            "attempts_left": MAX_ATTEMPTS - attempts - 1}


@router.post("/official-status")
def claim_official_status(body: OfficialClaim, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Record a claim of INEC accreditation or party authorisation. It counts only after a reviewer checks it."""
    p = _profile(user)
    if body.role == "party_agent" and not body.party:
        raise HTTPException(400, "Party agents must state the party they represent")
    if body.organisation_id and not db.get(Organisation, body.organisation_id):
        raise HTTPException(400, "Unknown organisation")
    previous = {"role": p.official_role, "status": p.official_status}
    p.official_role, p.official_status, p.official_reference = body.role, "claimed", body.reference
    p.party_affiliation = body.party if body.role == "party_agent" else None
    if body.organisation_id:
        p.organisation_id = body.organisation_id
    audit.record(db, actor=user, entity_type="official_status", entity_id=user.id, action="claimed",
                 previous=previous, new={"role": body.role, "reference": body.reference})
    db.commit()
    return status_view(user)


@router.post("/withdraw")
def withdraw(user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = _profile(user)
    p.application_status = "withdrawn"
    audit.record(db, actor=user, entity_type="volunteer_application", entity_id=user.id, action="withdrawn")
    db.commit()
    return status_view(user)
