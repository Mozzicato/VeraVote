"""Reset the database and load the simulated demo (PRD §21 scenarios A–D).

Run:  python -m app.seed
"""
import secrets
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from . import demo_data
from .db import Base, SessionLocal, engine
from .models import (Assignment, Candidate, Contest, ContributorProfile, Election, EvidenceSubmission, LGA,
                     OfficialResultDocument, Organisation, PollingUnit, State, User, Ward)
from .services import audit, classification, engine as status_engine, extraction
from .services.storage import storage

ELECTION_DAY = datetime(2026, 3, 14, 15, 0, tzinfo=timezone.utc)


def new_receipt() -> str:
    return "VV-" + secrets.token_hex(4).upper()


def sheet_svg(pu: PollingUnit, contest: Contest, values: dict[str, int], variant: str) -> bytes:
    """A rendered *simulated* EC8A-style form. Clearly watermarked; not a real INEC document."""
    rows = [(lbl, values.get(key, "")) for key, lbl in extraction.field_spec(contest)]
    lines = "".join(
        f'<text x="40" y="{210 + i * 44}" font-size="20">{escape(lbl)}</text>'
        f'<rect x="470" y="{184 + i * 44}" width="150" height="36" fill="none" stroke="#555"/>'
        f'<text x="545" y="{210 + i * 44}" font-size="22" text-anchor="middle" font-family="Courier New">{v}</text>'
        for i, (lbl, v) in enumerate(rows)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{260 + len(rows) * 44}" font-family="Arial">
<rect width="100%" height="100%" fill="#fbf8ef"/>
<text x="340" y="50" font-size="24" text-anchor="middle" font-weight="bold">SIMULATED RESULT FORM (EC8A-STYLE)</text>
<text x="340" y="80" font-size="15" text-anchor="middle" fill="#a00">DEMO DATA — NOT AN INEC DOCUMENT</text>
<text x="40" y="125" font-size="17">Polling unit: {escape(pu.official_name)}</text>
<text x="40" y="150" font-size="17">Code: {pu.official_code} · Contest: {escape(contest.office)}</text>
{lines}
<text x="40" y="{235 + len(rows) * 44}" font-size="12" fill="#777">capture: {escape(variant)}</text>
<text x="340" y="{(260 + len(rows) * 44) // 2}" font-size="60" fill="#c00" fill-opacity="0.08" text-anchor="middle"
 transform="rotate(-25 340 {(260 + len(rows) * 44) // 2})">SIMULATED</text>
</svg>"""
    return svg.encode()


def _user(db, name, phone, role, **profile) -> User:
    u = User(name=name, phone=phone, role=role, phone_verified=True)
    db.add(u)
    db.flush()
    if profile:
        db.add(ContributorProfile(user_id=u.id, **profile))
        db.flush()
        db.refresh(u)
    return u


APPROVED = dict(application_status="approved", identity_status="verified", training_status="completed",
                training_modules_completed=["m1", "m2", "m3", "m4", "m5"], assessment_status="passed",
                assessment_score=0.9, code_of_conduct_accepted_at=ELECTION_DAY - timedelta(days=30))


def _submit(db, *, user: User | None, pu, contest, election, values, variant, status="accepted",
            confirmed=True, minutes=0, category="field", evidence_type="result_sheet_photo",
            description="", forwarded="no") -> EvidenceSubmission:
    data = sheet_svg(pu, contest, values, variant)
    key, digest = storage.put_original(data, ".svg")
    profile = user.profile if user else None
    cls = classification.classify(profile)
    sub = EvidenceSubmission(
        client_submission_id=f"seed-{variant}", receipt_code=new_receipt(), source_category=category,
        contributor_id=user.id if user else None, contributor_classification=cls,
        party_affiliation=profile.party_affiliation if profile and cls == classification.PARTY_AGENT else None,
        organisation_id=profile.organisation_id if profile else None, polling_unit_id=pu.id,
        election_id=election.id, contest_id=contest.id, evidence_type=evidence_type,
        original_file_key=key, original_filename=f"{variant}.svg", content_type="image/svg+xml",
        file_size=len(data), file_hash=digest, description=description, is_forwarded_copy=forwarded,
        device_reported_time=ELECTION_DAY + timedelta(minutes=minutes),
        server_received_time=ELECTION_DAY + timedelta(minutes=minutes + 3),
        submission_status=status,
    )
    db.add(sub)
    db.flush()
    audit.record(db, actor=user, entity_type="evidence_submission", entity_id=sub.id, action="received",
                 new={"receipt": sub.receipt_code, "file_hash": digest, "classification": cls},
                 polling_unit_id=pu.id, public=True, actor_label=classification.SHORT_LABELS[cls])
    if confirmed:
        extraction.attach_fields(db, owner=sub, contest=contest, values=values)
    else:
        extraction.run_for_submission(db, sub)
    return sub


def _official(db, *, pu, contest, election, values, by: User) -> OfficialResultDocument:
    data = sheet_svg(pu, contest, values, f"official-{pu.official_code}")
    key, digest = storage.put_original(data, ".svg")
    doc = OfficialResultDocument(
        polling_unit_id=pu.id, election_id=election.id, contest_id=contest.id,
        source_platform="IReV (simulated)", source_reference=f"simulated://irev/{pu.official_code}/ec8a",
        original_file_key=key, file_hash=digest, retrieved_at=ELECTION_DAY + timedelta(hours=6),
        attached_by_id=by.id,
    )
    db.add(doc)
    db.flush()
    extraction.attach_fields(db, owner=doc, contest=contest, values=values)
    audit.record(db, actor=by, entity_type="official_document", entity_id=doc.id, action="attached",
                 new={"source": doc.source_platform, "file_hash": digest}, polling_unit_id=pu.id, public=True,
                 actor_label="Verification team")
    return doc


def seed(db: Session) -> None:
    state = State(**demo_data.STATE)
    db.add(state)
    db.flush()
    units: dict[str, PollingUnit] = {}
    for lg in demo_data.LGAS:
        lga = LGA(state_id=state.id, code=lg["code"], name=lg["name"])
        db.add(lga)
        db.flush()
        for wd in lg["wards"]:
            ward = Ward(lga_id=lga.id, code=wd["code"], name=wd["name"])
            db.add(ward)
            db.flush()
            for u in wd["units"]:
                code = f"SIM-{lg['code']}-{wd['code']}-{u['number']}"
                pu = PollingUnit(
                    official_code=code, state_id=state.id, lga_id=lga.id, ward_id=ward.id, unit_number=u["number"],
                    official_name=u["name"], location_description=u["location"], aliases=u["aliases"],
                    latitude=u["lat"], longitude=u["lng"], dataset_source=demo_data.DATASET_SOURCE,
                    dataset_version=demo_data.DATASET_VERSION, last_verified=ELECTION_DAY - timedelta(days=60),
                )
                db.add(pu)
                units[code] = pu
    election = Election(name=demo_data.ELECTION["name"], election_date=demo_data.ELECTION["date"],
                        election_type=demo_data.ELECTION["type"])
    db.add(election)
    db.flush()
    contest = Contest(election_id=election.id, **demo_data.CONTEST)
    db.add(contest)
    db.flush()
    for i, (party, name) in enumerate(demo_data.CANDIDATES):
        db.add(Candidate(contest_id=contest.id, party=party, name=name, ballot_order=i))
    db.flush()
    db.refresh(contest)

    org1 = Organisation(name="Transparency Watch Network (simulated)", organisation_type="observer_group",
                        verification_status="verified", contact_person="Funke Adebayo",
                        contact_details="coordinator@example.org", operational_areas="Riverbend LGA")
    org2 = Organisation(name="Citizens' Election Forum (simulated)", organisation_type="civil_society",
                        verification_status="verified", contact_person="Musa Danjuma",
                        contact_details="forum@example.org", operational_areas="Riverbend LGA, Hillcrest LGA")
    db.add_all([org1, org2])
    db.flush()

    def observer(org):
        return dict(APPROVED, official_role="accredited_observer", official_status="verified",
                    official_reference="SIM-ACCR-" + secrets.token_hex(3).upper(), organisation_id=org.id)

    amaka = _user(db, "Amaka Obi", "+2348000000001", "citizen")
    tunde = _user(db, "Tunde Bakare", "+2348000000002", "volunteer", **APPROVED)
    ngozi = _user(db, "Ngozi Eze", "+2348000000003", "volunteer", **observer(org1))
    ibrahim = _user(db, "Ibrahim Sani", "+2348000000004", "volunteer", **observer(org2))
    emeka = _user(db, "Emeka Nwosu", "+2348000000005", "volunteer", **observer(org1))
    halima = _user(db, "Halima Yusuf", "+2348000000006", "volunteer", **observer(org2))
    kemi = _user(db, "Kemi Alade", "+2348000000007", "volunteer",
                 **dict(APPROVED, official_role="party_agent", official_status="verified",
                        official_reference="SIM-AGENT-APX-0071", party_affiliation="APX"))
    _user(db, "Ade Ojo", "+2348000000008", "volunteer", application_status="training_pending",
          identity_status="verified", training_status="in_progress", training_modules_completed=["m1", "m2"])
    funke = _user(db, "Funke Adebayo", "+2348000000009", "coordinator")
    chika = _user(db, "Chika Umeh", "+2348000000010", "verifier")
    _user(db, "Yusuf Garba", "+2348000000011", "senior_reviewer")
    _user(db, "Platform Admin", "+2348000000012", "admin")
    db.add(ContributorProfile(user_id=funke.id, organisation_id=org1.id, application_status="approved",
                              identity_status="verified"))

    a, b, c, d, e = (units[k] for k in ("SIM-01-01-001", "SIM-01-01-002", "SIM-01-02-001", "SIM-02-01-001",
                                         "SIM-01-01-003"))
    for user, pu, org in [(ngozi, a, org1), (ibrahim, a, org2), (emeka, b, org1), (halima, b, org2),
                          (tunde, c, None), (kemi, e, None)]:
        db.add(Assignment(contributor_id=user.id, polling_unit_id=pu.id, election_id=election.id,
                          organisation_id=org.id if org else None, status="accepted",
                          is_primary=user not in (ibrahim, halima), decided_by_id=funke.id,
                          decided_at=ELECTION_DAY - timedelta(days=7)))
    # Assigned but no evidence yet: shows that "assigned" is never counted as "observed".
    db.add(Assignment(contributor_id=emeka.id, polling_unit_id=units["SIM-01-02-002"].id, election_id=election.id,
                      organisation_id=org1.id, status="requested"))
    db.flush()
    for u in (ngozi, ibrahim, emeka, halima, tunde, kemi):
        db.refresh(u)

    sv = lambda pu, delta=None: extraction.sheet_values(contest, demo_data.SHEETS[pu.official_code], delta)

    # Scenario A — two independent observers agree with the official document.
    _submit(db, user=ngozi, pu=a, contest=contest, election=election, values=sv(a), variant="A-ngozi", minutes=12)
    _submit(db, user=ibrahim, pu=a, contest=contest, election=election, values=sv(a), variant="A-ibrahim", minutes=15)
    _official(db, pu=a, contest=contest, election=election, values=sv(a), by=chika)

    # Scenario B — observers agree with each other; official document differs by 20 votes.
    _submit(db, user=emeka, pu=b, contest=contest, election=election, values=sv(b), variant="B-emeka", minutes=20)
    _submit(db, user=halima, pu=b, contest=contest, election=election, values=sv(b), variant="B-halima", minutes=22)
    _official(db, pu=b, contest=contest, election=election, values=sv(b, demo_data.SCENARIO_B_OFFICIAL_DELTA), by=chika)

    # Scenario C — a single source, no second record and no official document.
    _submit(db, user=tunde, pu=c, contest=contest, election=election, values=sv(c), variant="C-tunde", minutes=30)

    # Scenario D — a citizen photographs a publicly displayed result sheet.
    _submit(db, user=amaka, pu=d, contest=contest, election=election, values=sv(d), variant="D-amaka", minutes=45,
            category="citizen_lead", evidence_type="result_poster_photo", status="awaiting_review", confirmed=False,
            description="Photo of the result sheet pasted on the wall after counting.", forwarded="no")

    # Queue item for the correction demo: party-agent upload with a proposed (partly misread) extraction.
    _submit(db, user=kemi, pu=e, contest=contest, election=election, values=sv(e), variant="E-kemi", minutes=50,
            status="awaiting_review", confirmed=False)

    db.flush()
    for pu in units.values():
        status_engine.refresh(db, pu, contest)
    db.commit()


def reset() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    reset()
    print("Seeded simulated demo data.")
