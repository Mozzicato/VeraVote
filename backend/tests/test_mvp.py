"""End-to-end checks of the PRD §21 demo scenarios and §24 Definition of Done."""
from tests.conftest import as_user, png


def unit_id(client, code):
    return client.get("/polling-units/search", params={"q": code}).json()[0]["id"]


def unit_status(client, code):
    page = client.get(f"/public/polling-units/{unit_id(client, code)}").json()
    return page["contests"][0]


def contest_id(client):
    return client.get("/public/summary").json()["contests"][0]["id"]


# ---------------------------------------------------------------- scenarios A–D

def test_scenario_a_consistent(client):
    c = unit_status(client, "SIM-01-01-001")
    assert c["status"] == "consistent_evidence"
    assert c["independence"]["distinct_contributors"] == 2
    assert c["independence"]["distinct_organisations"] == 2
    assert c["independence"]["official_documents"] == 1


def test_scenario_b_discrepancy_without_fraud_language(client):
    c = unit_status(client, "SIM-01-01-002")
    assert c["status"] == "discrepancy_detected"
    diffs = [d for cmp in c["comparisons"] if cmp["result"] == "differ" for d in cmp["differences"]]
    assert {abs(d["difference"]) for d in diffs} == {20}
    text = (c["explanation"] + " ".join(c["notes"]) + c["disclaimer"]).lower()
    assert "human review" in text
    assert "fraud" not in text and "rigged" not in text


def test_scenario_c_insufficient(client):
    c = unit_status(client, "SIM-01-02-001")
    assert c["status"] == "insufficient_evidence"
    assert "only one usable record" in c["explanation"]


def test_scenario_d_citizen_lead_pending(client):
    c = unit_status(client, "SIM-02-01-001")
    assert c["status"] == "evidence_received"
    assert any("pending verification" in n for n in c["notes"])
    assert c["sources"][0]["classification"] == "citizen"


def test_simulated_labelling(client):
    s = client.get("/public/summary").json()
    assert s["simulated"] is True
    assert "Simulated" in s["contests"][0]["election"]["name"]
    pu = client.get(f"/public/polling-units/{unit_id(client, 'SIM-01-01-001')}").json()
    assert "simulated" in pu["contests"][0]["sources"][-1]["label"].lower()


# ---------------------------------------------------------------- public access & privacy

def test_search_by_landmark_alias(client):
    results = client.get("/polling-units/search", params={"q": "mosque"}).json()
    assert [r["official_code"] for r in results] == ["SIM-01-01-003"]
    assert results[0]["matched_alias"] == "Town Mosque"


def test_public_page_hides_contributor_identity(client):
    page = client.get(f"/public/polling-units/{unit_id(client, 'SIM-02-01-001')}").json()
    blob = str(page)
    assert "Amaka" not in blob and "contributor_id" not in blob and "follow_up_contact" not in blob


def test_pending_lead_file_not_public(client):
    page = client.get(f"/public/polling-units/{unit_id(client, 'SIM-02-01-001')}").json()
    sid = page["contests"][0]["sources"][0]["id"]
    assert client.get(f"/public/files/submission/{sid}").status_code == 404


def test_citizen_lead_without_account(client):
    pu = unit_id(client, "SIM-02-01-002")
    r = client.post("/public/evidence-leads", data={
        "polling_unit_id": pu, "contest_id": contest_id(client), "evidence_type": "result_poster_photo",
        "accepted_notice": "true", "description": "Poster at the gate", "follow_up_contact": "080-private",
    }, files={"file": ("poster.png", png(b"lead"), "image/png")})
    assert r.status_code == 200, r.text
    receipt = r.json()
    assert receipt["receipt_code"].startswith("VV-") and len(receipt["file_sha256"]) == 64
    assert receipt["classification"] == "citizen"
    assert client.get(f"/public/receipts/{receipt['receipt_code']}").status_code == 200
    c = unit_status(client, "SIM-02-01-002")
    assert c["status"] == "evidence_received"
    assert "080-private" not in str(c)


def test_upload_rejects_disguised_file(client):
    r = client.post("/public/evidence-leads", data={
        "polling_unit_id": unit_id(client, "SIM-02-01-002"), "contest_id": contest_id(client),
        "evidence_type": "result_sheet_photo", "accepted_notice": "true",
    }, files={"file": ("x.png", b"<svg onload=alert(1)>", "image/png")})
    assert r.status_code == 415


# ---------------------------------------------------------------- volunteer journey

def test_volunteer_journey_never_grants_accreditation(client):
    states = client.get("/states").json()
    lga = client.get("/lgas", params={"state_id": states[0]["id"]}).json()[0]
    r = client.post("/volunteers/apply", json={"name": "New Person", "phone": "+2348099999999",
                                               "state_id": states[0]["id"], "lga_id": lga["id"],
                                               "accept_code_of_conduct": True})
    assert r.status_code == 200
    h = as_user(r.json()["user"]["id"])
    assert client.post("/volunteers/verify-phone", json={"code": "000000"}, headers=h).status_code == 400
    client.post("/volunteers/verify-phone", json={"code": "123456"}, headers=h)
    assert client.get("/volunteers/assessment", headers=h).status_code == 400  # training first
    for m in client.get("/volunteers/training", headers=h).json():
        client.post(f"/volunteers/training/{m['id']}/complete", headers=h)
    from app.services.training import QUESTIONS
    wrong = client.post("/volunteers/assessment", headers=h, json={"answers": {}}).json()
    assert wrong["passed"] is False and wrong["attempts_left"] == 2
    ok = client.post("/volunteers/assessment", headers=h,
                     json={"answers": {q["id"]: q["answer"] for q in QUESTIONS}}).json()
    assert ok["passed"] is True
    assert ok["classification"] == "trained_community"
    assert "not INEC-accredited" in ok["classification_label"]

    # Claiming accreditation does not change classification until a reviewer checks it.
    me = client.post("/volunteers/official-status", headers=h,
                     json={"role": "accredited_observer", "reference": "ABC-123"}).json()
    assert me["classification"] == "trained_community" and me["official"]["status"] == "claimed"


def test_duplicate_phone_rejected(client):
    r = client.post("/volunteers/apply", json={"name": "Dup", "phone": "+2348000000002", "state_id": 1,
                                               "lga_id": 1, "accept_code_of_conduct": True})
    assert r.status_code == 409


def test_official_status_verification(client, users):
    h = as_user(users["ade"])
    client.post("/volunteers/official-status", headers=h, json={"role": "party_agent", "reference": "P-1",
                                                                "party": "BNP"})
    r = client.post(f"/verification/contributors/{users['ade']}/official-status",
                    headers=as_user(users["chika"]), json={"status": "verified"}).json()
    assert r["classification"] == "party_agent" and r["classification_label"] == "Party agent (BNP)"


# ---------------------------------------------------------------- field evidence, offline sync

def test_field_upload_requires_assignment_and_is_idempotent(client, users):
    cid = contest_id(client)
    pu_c = unit_id(client, "SIM-01-02-001")
    form = {"client_submission_id": "client-abc-123", "polling_unit_id": pu_c, "contest_id": cid,
            "captured_offline": "true", "device_reported_time": "2026-03-14T15:40:00Z"}
    # Ngozi is not assigned to this unit.
    r = client.post("/evidence", data=form, files={"file": ("a.png", png(b"1"), "image/png")},
                    headers=as_user(users["ngozi"]))
    assert r.status_code == 403
    # Amaka is a citizen: field upload refused, lead route still open.
    r = client.post("/evidence", data=form, files={"file": ("a.png", png(b"1"), "image/png")},
                    headers=as_user(users["amaka"]))
    assert r.status_code == 403
    # Tunde is assigned.
    first = client.post("/evidence", data=form, files={"file": ("a.png", png(b"1"), "image/png")},
                        headers=as_user(users["tunde"])).json()
    retry = client.post("/evidence", data=form, files={"file": ("a.png", png(b"1"), "image/png")},
                        headers=as_user(users["tunde"])).json()
    assert retry["receipt_code"] == first["receipt_code"] and retry["duplicate_retry"] is True
    assert first["captured_offline"] is True
    assert "not independently verified" in first["device_time_note"]
    assert len(client.get("/evidence/mine", headers=as_user(users["tunde"])).json()) == 2  # seed + this


# ---------------------------------------------------------------- verification engine

def _kemi_submission(client, users):
    q = client.get("/verification/queue", headers=as_user(users["chika"]),
                   params={"status": "awaiting_review", "category": "field"}).json()
    return next(i for i in q if i["polling_unit"]["code"] == "SIM-01-01-003")


def test_correction_flow_and_comparison(client, users):
    h = as_user(users["chika"])
    item = _kemi_submission(client, users)
    detail = client.get(f"/verification/submissions/{item['id']}", headers=h).json()
    assert detail["integrity_ok"] is True
    low = [f for f in detail["fields"] if f["needs_attention"]]
    assert len(low) == 1  # simulated misread

    # Cannot accept before extraction confirmed; cannot confirm with unchecked low-confidence field.
    assert client.post(f"/verification/submissions/{item['id']}/decision", headers=h,
                       json={"decision": "accept"}).status_code == 400
    assert client.post(f"/verification/submissions/{item['id']}/extraction", headers=h,
                       json={"action": "confirm"}).status_code == 400

    from app import demo_data
    from app.services.extraction import sheet_values
    from app.db import SessionLocal
    from app.models import Contest
    with SessionLocal() as db:
        true_vals = sheet_values(db.get(Contest, detail["contest_id"]), demo_data.SHEETS["SIM-01-01-003"])
    f = low[0]
    # Correction requires a reason.
    assert client.post(f"/verification/submissions/{item['id']}/fields", headers=h,
                       json={"fields": [{"id": f["id"], "value": true_vals[f["key"]]}]}).status_code == 400
    r = client.post(f"/verification/submissions/{item['id']}/fields", headers=h, json={"fields": [
        {"id": f["id"], "value": true_vals[f["key"]], "reason": "Digits transposed by extraction"}]}).json()
    corrected = next(x for x in r["fields"] if x["id"] == f["id"])
    assert corrected["status"] == "corrected" and corrected["extracted_value"] != corrected["value"]
    assert r["arithmetic"] == []

    client.post(f"/verification/submissions/{item['id']}/extraction", headers=h, json={"action": "confirm"})
    client.post(f"/verification/submissions/{item['id']}/decision", headers=h, json={"decision": "accept"})
    assert unit_status(client, "SIM-01-01-003")["status"] == "insufficient_evidence"

    # Official document that agrees → consistent; a replacement version that differs → discrepancy.
    pu = unit_id(client, "SIM-01-01-003")
    body = {"polling_unit_id": pu, "contest_id": detail["contest_id"], "source_reference": "sim://irev/1",
            "values": true_vals}
    assert client.post("/verification/official-documents", headers=h, json=body).json()["unit_status"] == \
        "consistent_evidence"
    changed = dict(true_vals)
    cand = next(k for k in changed if k.startswith("cand:"))
    changed[cand] += 15
    changed["total_valid"] += 15
    changed["total_cast"] += 15
    r = client.post("/verification/official-documents", headers=h,
                    json={**body, "values": changed, "version_reference": "v2"}).json()
    assert r["unit_status"] == "discrepancy_detected" and r["superseded_document_id"]


def test_arithmetic_flag_is_review_flag_not_misconduct(client):
    from app.services import arithmetic
    flags = arithmetic.check({"cand:1": 10, "cand:2": 5, "total_valid": 16, "rejected": 1, "total_cast": 17,
                              "accredited": 12})
    assert {f["check"] for f in flags} == {"candidate_sum", "cast_exceeds_accredited"}
    assert all("fraud" not in f["message"].lower() for f in flags)


def test_cannot_review_own_evidence(client, users):
    # A verifier who submits a citizen lead must not be able to review it.
    h = as_user(users["chika"])
    lead = client.post("/public/evidence-leads", headers=h, data={
        "polling_unit_id": unit_id(client, "SIM-02-01-002"), "contest_id": contest_id(client),
        "evidence_type": "other_info", "description": "I saw something", "accepted_notice": "true"}).json()
    r = client.post(f"/verification/submissions/{lead['submission_id']}/decision", headers=h,
                    json={"decision": "reject", "note": "x"})
    assert r.status_code == 403


def test_same_file_counts_as_one_document(client, users):
    pu = unit_id(client, "SIM-01-02-002")
    for _ in range(2):
        client.post("/public/evidence-leads", data={
            "polling_unit_id": pu, "contest_id": contest_id(client), "evidence_type": "result_poster_photo",
            "accepted_notice": "true", "is_forwarded_copy": "yes"},
            files={"file": ("same.png", png(b"same"), "image/png")})
    ind = unit_status(client, "SIM-01-02-002")["independence"]
    assert ind["submissions"] == 2 and ind["distinct_documents"] == 1
    assert any("identical file fingerprint" in n for n in ind["notes"])


def test_sensitive_outcome_needs_senior_approval(client, users):
    v, s = as_user(users["chika"]), as_user(users["yusuf"])
    pu, cid = unit_id(client, "SIM-01-01-002"), contest_id(client)
    client.post(f"/verification/units/{pu}/{cid}/investigation", headers=v, json={"action": "open"})
    assert unit_status(client, "SIM-01-01-002")["status"] == "discrepancy_detected"
    r = client.post(f"/verification/units/{pu}/{cid}/investigation", headers=v, json={
        "action": "close", "outcome": "discrepancy_confirmed", "findings": "Two observers match; IReV +20 BNP.",
        "public_summary": "Two independent observer photos agree with each other but differ from the official "
                          "copy by 20 votes for one candidate. Referred to partner organisations."}).json()
    assert r["investigation"]["status"] == "awaiting_approval"
    assert client.post(f"/verification/investigations/{r['investigation']['id']}/approve",
                       headers=v).status_code == 403
    client.post(f"/verification/investigations/{r['investigation']['id']}/approve", headers=s)
    c = unit_status(client, "SIM-01-01-002")
    assert c["status"] == "review_completed"
    assert any("20 votes" in n for n in c["notes"])


# ---------------------------------------------------------------- coverage & audit

def test_coverage_never_counts_assigned_as_observed(client, users):
    funke = as_user(users["funke"])
    orgs = client.get("/organisations").json()
    cov = client.get(f"/organisations/{orgs[0]['id']}/coverage", headers=funke).json()
    assert cov["totals"]["in_scope"] == 5
    assert cov["totals"]["evidence_received"] == 2
    observed = [u for u in cov["units"] if u["observed"]]
    assert all(u["submissions"] > 0 for u in observed)
    # Coordinator cannot see another organisation.
    assert client.get(f"/organisations/{orgs[1]['id']}/coverage", headers=funke).status_code == 403


def test_audit_chain_detects_tampering(client, users):
    h = as_user(users["chika"])
    assert client.get("/verification/audit/verify", headers=h).json()["intact"] is True
    from app.db import SessionLocal
    from app.models import AuditEvent
    with SessionLocal() as db:
        e = db.get(AuditEvent, 3)
        e.new_value = {"tampered": True}
        db.commit()
    r = client.get("/verification/audit/verify", headers=h).json()
    assert r == {"intact": False, "first_broken_event_id": 3}


def test_public_cannot_reach_staff_endpoints(client, users):
    assert client.get("/verification/queue").status_code == 401
    assert client.get("/verification/queue", headers=as_user(users["tunde"])).status_code == 403
