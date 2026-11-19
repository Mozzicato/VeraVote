"""Simulated reference data for the hackathon demo. NOT real INEC data (PRD §21).

`SHEETS` holds what the simulated result form for each demo polling unit says, keyed by
polling-unit code and candidate party. Simulated extraction reads from here.
"""

DATASET_SOURCE = "VeraVote simulated demo dataset"
DATASET_VERSION = "demo-2026.1"

STATE = {"code": "SIM", "name": "Simulated State (Demo)"}

LGAS = [
    {"code": "01", "name": "Riverbend LGA", "wards": [
        {"code": "01", "name": "Market Square Ward", "units": [
            {"number": "001", "name": "Central Primary School I", "location": "Main hall, Central Primary School, Market Road",
             "aliases": "Central School|Market Road school|Old Market", "lat": 6.5244, "lng": 3.3792},
            {"number": "002", "name": "Central Primary School II", "location": "Classroom block B, Central Primary School",
             "aliases": "Central School block B", "lat": 6.5246, "lng": 3.3795},
            {"number": "003", "name": "Open Space beside Town Mosque", "location": "Open space beside the Central Mosque",
             "aliases": "Town Mosque|Central Mosque", "lat": 6.5251, "lng": 3.3801},
        ]},
        {"code": "02", "name": "Riverside Ward", "units": [
            {"number": "001", "name": "Riverside Community Hall", "location": "Riverside Community Hall, Jetty Road",
             "aliases": "Jetty|Community Hall|Waterside", "lat": 6.5302, "lng": 3.3851},
            {"number": "002", "name": "St. Peter's Anglican Church Premises", "location": "Church compound, Ferry Street",
             "aliases": "St Peters|Ferry Street church", "lat": 6.5310, "lng": 3.3860},
        ]},
    ]},
    {"code": "02", "name": "Hillcrest LGA", "wards": [
        {"code": "01", "name": "Hilltop Ward", "units": [
            {"number": "001", "name": "Hilltop Health Centre", "location": "Forecourt, Hilltop Primary Health Centre",
             "aliases": "Health Centre|Clinic", "lat": 6.6012, "lng": 3.4103},
            {"number": "002", "name": "Hilltop Motor Park", "location": "Shed at Hilltop Motor Park",
             "aliases": "Motor Park|Garage", "lat": 6.6020, "lng": 3.4110},
        ]},
    ]},
]

ELECTION = {"name": "Simulated Governorship Election 2026 (Demo)", "date": "2026-03-14", "type": "governorship"}
CONTEST = {"office": "Governor", "constituency": "Simulated State"}
CANDIDATES = [
    ("APX", "Adaeze Okafor"),
    ("BNP", "Bello Musa"),
    ("CPD", "Chinedu Eze"),
]


def sheet(accredited: int, votes: dict[str, int], rejected: int) -> dict:
    valid = sum(votes.values())
    return {"accredited": accredited, "votes": votes, "rejected": rejected,
            "total_valid": valid, "total_cast": valid + rejected}


# Codes are built as SIM-<lga>-<ward>-<unit>.
SHEETS = {
    # Scenario A: consistent.
    "SIM-01-01-001": sheet(412, {"APX": 182, "BNP": 151, "CPD": 46}, 9),
    # Scenario B: observers agree; official copy differs by 20 for BNP.
    "SIM-01-01-002": sheet(388, {"APX": 140, "BNP": 166, "CPD": 51}, 7),
    # Scenario C: one source only.
    "SIM-01-02-001": sheet(301, {"APX": 98, "BNP": 120, "CPD": 33}, 4),
    # Scenario D: citizen lead.
    "SIM-02-01-001": sheet(276, {"APX": 87, "BNP": 92, "CPD": 61}, 6),
    # Units with no evidence yet still have a sheet so live uploads can be simulated.
    "SIM-01-01-003": sheet(350, {"APX": 130, "BNP": 129, "CPD": 70}, 8),
    "SIM-01-02-002": sheet(290, {"APX": 101, "BNP": 99, "CPD": 52}, 5),
    "SIM-02-01-002": sheet(245, {"APX": 66, "BNP": 110, "CPD": 49}, 3),
}

SCENARIO_B_OFFICIAL_DELTA = {"BNP": 20}  # official document shows BNP +20
