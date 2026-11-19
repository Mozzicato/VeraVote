"""Database models. Mirrors PRD §17.2, with the extra fields the PRD's rules require.

Status / type columns are plain strings; the allowed values live in `enums.py`.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- geography (PRD §5)

class State(Base):
    __tablename__ = "states"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    name: Mapped[str] = mapped_column(String(80))


class LGA(Base):
    __tablename__ = "lgas"
    id: Mapped[int] = mapped_column(primary_key=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), index=True)
    code: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(80))
    state: Mapped[State] = relationship()


class Ward(Base):
    __tablename__ = "wards"
    id: Mapped[int] = mapped_column(primary_key=True)
    lga_id: Mapped[int] = mapped_column(ForeignKey("lgas.id"), index=True)
    code: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(80))
    lga: Mapped[LGA] = relationship()


class PollingUnit(Base):
    __tablename__ = "polling_units"
    id: Mapped[int] = mapped_column(primary_key=True)
    official_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), index=True)
    lga_id: Mapped[int] = mapped_column(ForeignKey("lgas.id"), index=True)
    ward_id: Mapped[int] = mapped_column(ForeignKey("wards.id"), index=True)
    unit_number: Mapped[str] = mapped_column(String(8))
    official_name: Mapped[str] = mapped_column(String(200), index=True)
    location_description: Mapped[str] = mapped_column(Text, default="")
    # Community / landmark names people actually use (PRD §5.3), "|" separated.
    aliases: Mapped[str] = mapped_column(Text, default="")
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    dataset_source: Mapped[str] = mapped_column(String(120))
    dataset_version: Mapped[str] = mapped_column(String(40))
    last_verified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # PRD §5.4: relocations create a new version rather than overwriting.
    superseded_by_id: Mapped[int | None] = mapped_column(ForeignKey("polling_units.id"))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)

    state: Mapped[State] = relationship()
    lga: Mapped[LGA] = relationship()
    ward: Mapped[Ward] = relationship()


# ---------------------------------------------------------------- people (PRD §3, §4)

class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    organisation_type: Mapped[str] = mapped_column(String(40))  # civil_society | observer_group | newsroom | political_party
    verification_status: Mapped[str] = mapped_column(String(20), default="self_declared")
    contact_person: Mapped[str] = mapped_column(String(120), default="")
    contact_details: Mapped[str] = mapped_column(String(200), default="")
    operational_areas: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(30), default="volunteer")
    account_status: Mapped[str] = mapped_column(String(20), default="active")
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    profile: Mapped["ContributorProfile | None"] = relationship(
        back_populates="user", uselist=False, foreign_keys="ContributorProfile.user_id"
    )


class ContributorProfile(Base):
    """VeraVote training status and official status are deliberately separate (PRD §4.6)."""
    __tablename__ = "contributor_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    application_status: Mapped[str] = mapped_column(String(40), default="draft")
    identity_status: Mapped[str] = mapped_column(String(20), default="pending")
    training_modules_completed: Mapped[list] = mapped_column(JSON, default=list)
    training_status: Mapped[str] = mapped_column(String(20), default="not_started")
    assessment_status: Mapped[str] = mapped_column(String(20), default="not_taken")
    assessment_score: Mapped[float | None] = mapped_column(Float)
    code_of_conduct_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preferred_state_id: Mapped[int | None] = mapped_column(ForeignKey("states.id"))
    preferred_lga_id: Mapped[int | None] = mapped_column(ForeignKey("lgas.id"))
    organisation_id: Mapped[int | None] = mapped_column(ForeignKey("organisations.id"))

    # Official status: established independently, never derived from VeraVote training.
    official_role: Mapped[str] = mapped_column(String(30), default="none")  # none | accredited_observer | party_agent
    official_status: Mapped[str] = mapped_column(String(20), default="not_applicable")
    official_reference: Mapped[str | None] = mapped_column(String(120))
    official_verified_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    # Declared by the party agent; never inferred (PRD §3 permission principles).
    party_affiliation: Mapped[str | None] = mapped_column(String(60))

    user: Mapped[User] = relationship(back_populates="profile", foreign_keys=[user_id])
    organisation: Mapped[Organisation | None] = relationship()


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    answers: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------- elections

class Election(Base):
    __tablename__ = "elections"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    election_date: Mapped[str] = mapped_column(String(10))
    election_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="concluded")
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)


class Contest(Base):
    __tablename__ = "contests"
    id: Mapped[int] = mapped_column(primary_key=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"), index=True)
    office: Mapped[str] = mapped_column(String(120))
    constituency: Mapped[str] = mapped_column(String(120))
    election: Mapped[Election] = relationship()
    candidates: Mapped[list["Candidate"]] = relationship(order_by="Candidate.ballot_order")


class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), index=True)
    party: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(120))
    ballot_order: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------- coverage (PRD §6)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    contributor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    polling_unit_id: Mapped[int] = mapped_column(ForeignKey("polling_units.id"), index=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"))
    organisation_id: Mapped[int | None] = mapped_column(ForeignKey("organisations.id"))
    status: Mapped[str] = mapped_column(String(20), default="requested")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    contributor: Mapped[User] = relationship(foreign_keys=[contributor_id])
    polling_unit: Mapped[PollingUnit] = relationship()


# ---------------------------------------------------------------- evidence (PRD §7, §9)

class EvidenceSubmission(Base):
    __tablename__ = "evidence_submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    # PRD §8.2: client-generated ID makes retries idempotent.
    client_submission_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    receipt_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    source_category: Mapped[str] = mapped_column(String(20))  # field | citizen_lead
    contributor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    # Snapshot of classification at submission time (PRD §7.3).
    contributor_classification: Mapped[str] = mapped_column(String(30))
    party_affiliation: Mapped[str | None] = mapped_column(String(60))
    organisation_id: Mapped[int | None] = mapped_column(ForeignKey("organisations.id"))
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id"))
    polling_unit_id: Mapped[int] = mapped_column(ForeignKey("polling_units.id"), index=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"))
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(30))

    original_file_key: Mapped[str | None] = mapped_column(String(200))
    original_filename: Mapped[str | None] = mapped_column(String(200))
    content_type: Mapped[str | None] = mapped_column(String(60))
    file_size: Mapped[int | None] = mapped_column(Integer)
    file_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    source_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    follow_up_contact: Mapped[str | None] = mapped_column(String(200))  # private, never public
    is_forwarded_copy: Mapped[str] = mapped_column(String(10), default="unknown")  # yes | no | unknown

    device_reported_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    server_received_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    captured_offline: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_attempts: Mapped[int] = mapped_column(Integer, default=1)

    submission_status: Mapped[str] = mapped_column(String(30), default="awaiting_review")
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    review_note: Mapped[str] = mapped_column(Text, default="")
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)

    contributor: Mapped[User | None] = relationship(foreign_keys=[contributor_id])
    organisation: Mapped[Organisation | None] = relationship()
    polling_unit: Mapped[PollingUnit] = relationship()
    contest: Mapped[Contest] = relationship()
    fields: Mapped[list["ExtractedField"]] = relationship(
        back_populates="submission", order_by="ExtractedField.position")


class OfficialResultDocument(Base):
    __tablename__ = "official_result_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    polling_unit_id: Mapped[int] = mapped_column(ForeignKey("polling_units.id"), index=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"))
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), index=True)
    source_platform: Mapped[str] = mapped_column(String(60))
    source_reference: Mapped[str] = mapped_column(String(500))
    original_file_key: Mapped[str | None] = mapped_column(String(200))
    file_hash: Mapped[str | None] = mapped_column(String(64))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    version_reference: Mapped[str] = mapped_column(String(60), default="v1")
    supersedes_id: Mapped[int | None] = mapped_column(ForeignKey("official_result_documents.id"))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")
    attached_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True)

    fields: Mapped[list["ExtractedField"]] = relationship(
        back_populates="official_document", order_by="ExtractedField.position")


class ExtractedField(Base):
    """One figure read from a document. The original file is never modified (PRD §7.4, §9.2).

    field_key is `cand:<candidate_id>` or one of: accredited, total_valid, rejected, total_cast.
    """
    __tablename__ = "extracted_fields"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int | None] = mapped_column(ForeignKey("evidence_submissions.id"), index=True)
    official_document_id: Mapped[int | None] = mapped_column(ForeignKey("official_result_documents.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(30))
    label: Mapped[str] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer, default=0)
    extracted_value: Mapped[int | None] = mapped_column(Integer)
    corrected_value: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="proposed")  # proposed | confirmed | corrected | unreadable
    method: Mapped[str] = mapped_column(String(20), default="simulated")
    correction_reason: Mapped[str | None] = mapped_column(Text)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    submission: Mapped[EvidenceSubmission | None] = relationship(back_populates="fields", foreign_keys=[submission_id])
    official_document: Mapped[OfficialResultDocument | None] = relationship(
        back_populates="fields", foreign_keys=[official_document_id]
    )

    @property
    def value(self) -> int | None:
        if self.status == "unreadable":
            return None
        return self.corrected_value if self.corrected_value is not None else self.extracted_value


# ---------------------------------------------------------------- review (PRD §12)

class EvidenceComparison(Base):
    __tablename__ = "evidence_comparisons"
    id: Mapped[int] = mapped_column(primary_key=True)
    polling_unit_id: Mapped[int] = mapped_column(ForeignKey("polling_units.id"), index=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"))
    source_a: Mapped[str] = mapped_column(String(40))  # "submission:12" | "official:3"
    source_b: Mapped[str] = mapped_column(String(40))
    result: Mapped[str] = mapped_column(String(20))  # agree | differ | not_comparable
    discrepancy_details: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Investigation(Base):
    __tablename__ = "investigations"
    __table_args__ = (UniqueConstraint("polling_unit_id", "contest_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    polling_unit_id: Mapped[int] = mapped_column(ForeignKey("polling_units.id"), index=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"))
    assigned_reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | awaiting_approval | closed
    outcome: Mapped[str | None] = mapped_column(String(40))
    findings: Mapped[str] = mapped_column(Text, default="")
    public_summary: Mapped[str] = mapped_column(Text, default="")
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AuditEvent(Base):
    """Append-only, hash-chained log (PRD §14.2 "signed or otherwise protected audit events")."""
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    actor_label: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[str] = mapped_column(String(40), index=True)
    action: Mapped[str] = mapped_column(String(60))
    previous_value: Mapped[dict | None] = mapped_column(JSON)
    new_value: Mapped[dict | None] = mapped_column(JSON)
    polling_unit_id: Mapped[int | None] = mapped_column(ForeignKey("polling_units.id"), index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False)  # appears in the public timeline
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    prev_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64))


class UnitStatus(Base):
    """Last computed public status per polling unit + contest, so changes can be logged."""
    __tablename__ = "unit_statuses"
    polling_unit_id: Mapped[int] = mapped_column(ForeignKey("polling_units.id"), primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(30))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
