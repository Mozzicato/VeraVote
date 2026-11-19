"""Contributor classification (PRD §4.6).

VeraVote training NEVER turns into INEC accreditation. Official roles count only once a
reviewer has checked them against the official process, and they expire/revoke separately.
"""
from ..models import ContributorProfile

CITIZEN = "citizen"
TRAINED = "trained_community"
OBSERVER = "accredited_observer"
PARTY_AGENT = "party_agent"
OFFICIAL = "official_document"

FIELD_CLASSIFICATIONS = {TRAINED, OBSERVER, PARTY_AGENT}

LABELS = {
    CITIZEN: "Citizen evidence lead",
    TRAINED: "VeraVote-trained community contributor (not INEC-accredited)",
    OBSERVER: "INEC-accredited observer",
    PARTY_AGENT: "Party agent",
    OFFICIAL: "Official result document",
}

SHORT_LABELS = {
    CITIZEN: "Citizen lead",
    TRAINED: "Trained contributor",
    OBSERVER: "Accredited observer",
    PARTY_AGENT: "Party agent",
    OFFICIAL: "Official document",
}


def classify(profile: ContributorProfile | None) -> str:
    if profile is None:
        return CITIZEN
    if profile.official_status == "verified" and profile.official_role in (OBSERVER, PARTY_AGENT):
        return profile.official_role
    if profile.application_status == "approved":
        return TRAINED
    return CITIZEN


def label(classification: str, party: str | None = None) -> str:
    if classification == PARTY_AGENT and party:
        return f"Party agent ({party})"
    return LABELS.get(classification, classification)
