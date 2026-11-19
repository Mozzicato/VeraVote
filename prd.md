# VERAVOTE
## Product Requirements Document (PRD)

**Product:** VeraVote  
**Category:** Election evidence, verification and public transparency platform  
**Geographic scope:** Nigeria — 36 states and the Federal Capital Territory  
**Primary platform:** Mobile-first Progressive Web App (PWA)  
**Product stage:** Hackathon MVP with nationwide-capable architecture  
**Version:** 1.0  
**Status:** Proposed product specification

---

# 1. Executive Summary

## 1.1 Product vision

VeraVote is an independent election evidence platform that enables Nigerians to contribute, preserve, examine and verify evidence relating to polling-unit election results.

The platform connects ordinary citizens, trained community volunteers, accredited election observers, party agents, civil society organisations, verification teams, journalists and the general public.

Its central purpose is to establish a transparent, traceable record of what was observed at polling units and compare that evidence against subsequently published official result documents.

VeraVote does not conduct elections, replace INEC, certify election results or independently declare winners.

It provides an additional, independently managed evidence layer through which discrepancies can be identified, investigated and understood.

## 1.2 Problem statement

Election transparency depends on more than the eventual publication of results.

There is a period between the announcement and documentation of polling-unit results and the time when those records become publicly accessible. Evidence collected independently during this period can help establish what was observed before subsequent collation and publication.

However, election evidence is often fragmented across:
- Photographs stored on personal phones.
- WhatsApp groups.
- Individual observers.
- Political party agents.
- Civil society organisations.
- Newsrooms and journalists.
- Official result publication platforms.

These records can be difficult to locate, authenticate, compare and reconcile.

Ordinary citizens also lack a straightforward way to understand what evidence exists for their polling unit and whether competing records have been examined.

VeraVote addresses this problem through a structured evidence network and a publicly accessible evidence registry.

## 1.3 Product objectives

1. Enable nationwide registration of individual community contributors.
2. Provide a structured training and assessment process.
3. Distinguish community contributors, trained contributors, accredited observers and authorised party agents.
4. Enable safe and structured evidence collection.
5. Support offline evidence capture and delayed synchronisation.
6. Maintain a traceable history of every evidence submission.
7. Compare independent records against one another and official result documents.
8. Make discrepancies understandable and accessible to the public.
9. Allow citizens to contribute evidence leads without requiring formal observer status.
10. Provide civil society organisations with tools to coordinate and review evidence.

## 1.4 Core product principle

**VeraVote verifies the provenance and consistency of evidence. It does not automatically certify the truth of an election result.**

---

# 2. Target Users and Personas

The product must work for users with different levels of technical experience, connectivity, literacy and institutional authority.

## 2.1 Ordinary citizen — Amaka

**Profile:** A Nigerian voter who wants to understand what happened at her polling unit.

Needs:
- Find her polling unit without knowing its official code.
- Search by community, ward, LGA or familiar landmark.
- View available result-sheet evidence.
- Understand the difference between observer evidence and official records.
- Submit a photograph or other relevant evidence as a lead.
- Check whether a discrepancy is being investigated.

Constraints:
- May use a low-end Android phone.
- May have limited mobile data.
- May not be comfortable with maps.
- May have limited digital literacy.
- May not know how election result forms work.

Product response:
- Simple public interface.
- Text-first pages.
- Local-language support.
- Optional audio explanations.
- No mandatory account for viewing public evidence.
- No requirement to upload evidence to use the platform.

## 2.2 Community volunteer

**Profile:** A Nigerian citizen who wants to contribute to election transparency.

Needs:
- Apply to join the VeraVote network.
- Complete identity checks.
- Learn election observation fundamentals.
- Take an assessment.
- Receive a contributor status.
- Request a polling-unit assignment.
- Submit evidence within permitted boundaries.
- Track submission and review status.

Constraints:
- May have no organisational affiliation.
- May not be familiar with election regulations.
- May live far from an assigned polling unit.
- May face poor connectivity or safety concerns.

Product response:
- Open application.
- Structured training.
- Practical assessment.
- Clearly defined contributor privileges.
- Safe assignment and withdrawal mechanisms.

Important distinction: VeraVote training and verification do not constitute official INEC accreditation.

## 2.3 Accredited election observer

**Profile:** An individual formally designated through an INEC-accredited observer group.

Needs:
- Establish their observer status.
- Associate their submission with their actual observer organisation.
- Capture polling-unit evidence.
- Maintain a traceable record of submissions.
- Submit evidence offline.
- Receive feedback from verification teams.

## 2.4 Party agent

**Profile:** A person authorised by a registered political party or candidate to act as a polling agent.

Needs:
- Establish their authorisation.
- Submit party-agent evidence.
- Identify their political-party affiliation within the evidence record.
- Preserve evidence and track its review.

Party agents and independent observers must remain distinct contributor categories.

## 2.5 Civil society organisation coordinator

**Profile:** A representative of a registered civil society organisation coordinating election observation activities.

Needs:
- Register an organisation.
- Manage its field contributors.
- Allocate polling-unit coverage.
- Monitor submission progress.
- Identify uncovered locations.
- Review evidence and escalate discrepancies.

## 2.6 Verification officer

**Profile:** A trained VeraVote team member responsible for examining submitted evidence.

Needs:
- Review original evidence.
- Compare extracted figures with source documents.
- Examine conflicting submissions.
- Request clarification.
- Record investigation decisions.
- Maintain an auditable history.

## 2.7 Public researcher / journalist

Needs:
- Search polling-unit evidence.
- Examine original source documents where disclosure is safe and lawful.
- Compare official and independent records.
- Export or reference evidence.
- Understand the methodology behind each public status.

---

# 3. User Roles and Permissions

VeraVote must operate a role-based access-control system.

| Role | Main permissions |
|---|---|
| Public visitor | Search and view public evidence |
| Citizen contributor | Submit evidence leads |
| VeraVote community volunteer | Complete training and submit permitted evidence |
| Trained field contributor | Submit designated field evidence |
| Accredited observer | Submit evidence under verified observer status |
| Party agent | Submit authorised party-agent evidence |
| Organisation coordinator | Manage organisation members and assignments |
| Verification officer | Review and reconcile submissions |
| Senior reviewer | Approve review outcomes and resolve escalations |
| Platform administrator | Manage users, roles, configurations and access |

### Permission principles

- Users receive only the permissions required for their role.
- Organisation coordinators cannot modify evidence submitted by their members.
- Contributors cannot approve their own evidence.
- Verification officers cannot silently delete or overwrite original evidence.
- Administrators cannot alter published review history without generating an audit event.
- Public users cannot access private contributor information.
- Political affiliation is not inferred from a person's identity or behaviour.

---

# 4. Volunteer Recruitment and Verification

## 4.1 Open nationwide registration

Any eligible individual may apply to become a VeraVote community volunteer, subject to published eligibility and safety requirements.

The application must not require membership of a civil society organisation.

## 4.2 Application workflow

1. Applicant opens the volunteer registration page.
2. Provides basic personal and contact information.
3. Selects their state, LGA and preferred area of participation.
4. Completes the identity verification process.
5. Accepts the volunteer code of conduct.
6. Completes the election observation training.
7. Takes the knowledge assessment.
8. Completes a practical result-sheet assessment.
9. Receives an application decision.

Application states:

- Draft
- Submitted
- Identity verification pending
- Training pending
- Assessment pending
- Approved
- Rejected
- Suspended
- Withdrawn

## 4.3 Identity verification

VeraVote must establish that contributors are genuine, unique individuals.

Potential verification methods:
- Phone number verification using OTP.
- Government identity verification through a lawful provider, where justified.
- Duplicate-account detection.
- Manual review of suspicious applications.

Identity data must not be unnecessarily exposed to other contributors or the public.

VeraVote must not collect NIN or PVC details merely because they are convenient. Any such collection requires a documented legal basis, necessity assessment and security controls.

## 4.4 Training programme

Training modules:

**Module 1 — Understanding Nigerian elections**
- Electoral structure.
- Polling units and wards.
- Roles of INEC officials.
- Roles of observers and party agents.

**Module 2 — Election observation ethics**
- Neutrality.
- Non-interference.
- Personal safety.
- Confidentiality.
- Respect for voters and officials.

**Module 3 — Result documentation**
- Understanding EC8A.
- Identifying polling-unit information.
- Reading candidate figures.
- Understanding rejected and valid votes.
- Identifying incomplete or illegible forms.

**Module 4 — Evidence collection**
- Photographing complete documents.
- Avoiding obstruction.
- Preserving original images.
- Avoiding alterations.
- Submitting evidence securely.

**Module 5 — VeraVote usage**
- Evidence submission.
- Offline mode.
- Synchronisation.
- Submission receipts.
- Reporting safety concerns.

## 4.5 Assessment

Applicants must complete:

- Knowledge questions.
- Practical result-sheet interpretation.
- A simulated evidence-submission exercise.
- A code-of-conduct acknowledgement.

The assessment must have a configurable pass mark.

A proposed starting threshold is 80%, subject to pilot testing.

## 4.6 Contributor classification

VeraVote maintains separate classifications:

1. Citizen evidence contributor.
2. VeraVote-trained community contributor.
3. INEC-accredited election observer.
4. Authorised political party agent.

The system must never convert a VeraVote-trained contributor into an INEC-accredited observer automatically.

Official accreditation must be independently established using the applicable INEC process.

A contributor may have a VeraVote training status and a separate official accreditation status.

---

# 5. Nationwide Electoral Geography

## 5.1 Geographic structure

The system must support Nigeria's electoral hierarchy:

Country → State/FCT → LGA/Area Council → Registration Area/Ward → Polling Unit.

Each polling unit must be associated with an authoritative INEC identifier.

## 5.2 Polling-unit directory

The platform must maintain a structured polling-unit database.

Required fields:

- Polling-unit identifier.
- State code.
- State name.
- LGA code.
- LGA name.
- Ward/registration-area code.
- Ward name.
- Polling-unit number.
- Official polling-unit name.
- Official location description.
- Coordinates, where available.
- Dataset source.
- Dataset version.
- Last verified date.
- Active/inactive status.

VeraVote must not assume it has a live INEC API. The initial implementation should support importing an authorised, authoritative polling-unit dataset.

## 5.3 Polling-unit discovery

Users must be able to locate a polling unit through:

- Official polling-unit code.
- State, LGA, ward and unit selection.
- Search by official name.
- Community or landmark aliases.
- Optional GPS-assisted discovery.
- External link to INEC's official locator.

GPS is a discovery aid, not proof of polling-unit assignment.

If several units match a search, the system must show the candidates and allow the user to confirm.

## 5.4 Location changes

Polling-unit relocation or reassignment must not silently overwrite historical records.

The system must:
- Preserve the old location record.
- Create a new version.
- Record the effective date.
- Record the source of the change.
- Link the old and new records where authoritative confirmation exists.

---

# 6. Polling-Unit Coverage Management

## 6.1 Coverage model

The coverage system divides electoral geography into manageable units.

National → State → LGA → Ward → Polling Unit.

Volunteers may request coverage assignments, while organisation coordinators and authorised VeraVote administrators can allocate them.

## 6.2 Assignment workflow

1. Contributor selects a preferred area.
2. System shows available polling units.
3. Contributor requests an assignment.
4. Assignment rules check existing coverage.
5. Coordinator or authorised system workflow approves the request.
6. Contributor receives assignment details.
7. Contributor can accept, decline or withdraw.

## 6.3 Assignment rules

- A polling unit may have one primary contributor.
- Additional contributors may be assigned when coverage needs justify it.
- A unit with multiple contributors must retain each contributor's independent identity and source history.
- A contributor cannot submit under an assignment belonging to another person.
- Assignments must not imply official INEC accreditation.
- Party agents and independent observers must retain their respective classifications.

## 6.4 Coverage dashboard

The organisation dashboard must display:

- Total polling units in scope.
- Assigned polling units.
- Unassigned polling units.
- Contributors awaiting approval.
- Contributors who have accepted assignments.
- Evidence received.
- Evidence pending.
- Units with incomplete submissions.

Coverage must be displayed honestly.

A polling unit is not considered observed merely because a volunteer has been assigned to it.

---

# 7. Evidence Collection

## 7.1 Primary evidence type

The first supported evidence type is a photograph or scanned copy of the completed polling-unit result form, especially Form EC8A where applicable.

Other evidence types may be added later.

## 7.2 Evidence submission workflow

1. Contributor selects their assigned polling unit.
2. Contributor selects the relevant election and contest.
3. Contributor captures or selects the result-sheet image.
4. System checks image quality.
5. Contributor confirms the submission.
6. System creates a local submission record.
7. Evidence is stored locally if offline.
8. When connectivity returns, the image is uploaded.
9. Server generates a receipt and records the server-received time.
10. Evidence enters the review queue.

## 7.3 Submission metadata

Each submission should contain:

- Unique submission ID.
- Election ID.
- Polling-unit ID.
- Contributor ID.
- Contributor classification at submission time.
- Organisation ID, where applicable.
- Evidence category.
- Original image.
- SHA-256 file hash.
- Device-reported capture time, where available.
- Server-received time.
- Offline/online submission indicator.
- Upload and synchronisation history.
- Review status.

Device-reported time must not be represented as independently verified capture time.

A SHA-256 hash establishes file integrity relative to a recorded fingerprint. It does not prove that the photograph is authentic, unaltered before upload, or captured at the stated location or time.

## 7.4 Evidence preservation

- Original files must be retained.
- Processing must produce separate derived files.
- OCR must never overwrite original images.
- Evidence must have versioned metadata.
- Deletion must be restricted and audited.
- Access to sensitive evidence must be logged.
- Published evidence must be linked to its source submission.

## 7.5 Citizen evidence leads

Ordinary citizens must be able to submit evidence even if they are not registered observers.

Examples:
- Photograph of a result sheet displayed publicly.
- Photograph of an official result poster.
- A link to a publicly available document.
- Information about an apparently conflicting result record.

Citizen evidence leads must enter a separate review queue.

They must not automatically receive the same classification as an accredited observer or authorised party agent.

The verification team may:
- Request additional information.
- Compare the submission against existing records.
- Contact the contributor, where safe and appropriate.
- Promote it to a reviewed evidence record.
- Reject it as unusable.
- Retain it as an unresolved lead.

---

# 8. Offline-First Functionality

Offline functionality is essential for nationwide deployment.

## 8.1 Requirements

The application must allow contributors to:

- Open previously downloaded assignments.
- View essential polling-unit details.
- Capture result-sheet images.
- Complete basic submission metadata.
- Save submissions locally.
- Resume incomplete uploads.
- Synchronise when internet access returns.

## 8.2 Synchronisation

Each locally created submission must receive a unique client-generated identifier.

The server must use that identifier to prevent duplicate submissions during retries.

The application must distinguish:

- Locally saved.
- Waiting for connectivity.
- Uploading.
- Received by server.
- Processing.
- Failed.
- Rejected.

The server-received time must be recorded independently of the device clock.

Offline records must not be described as having a server-verified submission time until synchronisation occurs.

## 8.3 Device limitations

The application should:
- Compress upload copies without altering original evidence.
- Support interrupted uploads.
- Avoid large background downloads.
- Display available storage warnings.
- Allow contributors to retry synchronisation.
- Protect locally stored evidence where technically feasible.

---

# 9. Evidence Extraction and Verification Engine

This is VeraVote's central technical component.

## 9.1 Document processing

When a result sheet is uploaded:

1. Store the original document.
2. Generate a file fingerprint.
3. Detect document orientation and quality.
4. Run OCR.
5. Extract polling-unit identifiers.
6. Extract candidate names and figures.
7. Extract relevant totals.
8. Store extracted fields separately from the original.
9. Send uncertain fields for human review.

## 9.2 Human confirmation

OCR output is a proposed interpretation, not a verified result.

A reviewer must be able to:
- View the original document.
- View extracted fields.
- Correct incorrect figures.
- Mark unreadable fields.
- Record the reason for a correction.
- Confirm or reject the extraction.

Every correction must be recorded in the audit trail.

## 9.3 Arithmetic validation

Where the document structure supports it, the system checks:

- Candidate vote totals.
- Total valid votes.
- Rejected votes.
- Total votes cast.
- Relevant accreditation figures.
- Consistency between component totals and declared totals.

Arithmetic inconsistencies must trigger a review flag.

The system must not assume that every arithmetic anomaly proves misconduct.

## 9.4 Source comparison

The engine compares:

- Multiple observer submissions.
- Party-agent submissions.
- Trained contributor submissions.
- Citizen evidence leads.
- Official IReV documents.
- Other approved documentary sources.

Comparison must consider:

- Polling-unit identity.
- Election and contest.
- Candidate mapping.
- Figures.
- Document versions.
- Submission provenance.
- Source independence.

## 9.5 Source independence

Multiple photographs do not necessarily represent multiple independent sources.

For example:
- Three people photographing the same result poster may provide three records of one source document.
- Two contributors may belong to the same organisation.
- A photograph may have been forwarded rather than captured independently.

The system must distinguish:
- Number of submissions.
- Number of distinct contributors.
- Number of distinct organisations.
- Number of distinct original documents.
- Known source relationships.
- Independence assessment.

## 9.6 IReV comparison

The initial platform should support manual upload or authorised import of official result documents.

For every official document, store:
- Source platform.
- Source URL or reference.
- Polling-unit ID.
- Retrieval time.
- Original document.
- File fingerprint.
- Document version or replacement history, where available.

Do not claim live IReV integration unless an approved and functioning integration exists.

---

# 10. Evidence Status and Public Transparency

The platform must use carefully defined evidence statuses.

## 10.1 Public evidence statuses

**No evidence available**

No usable evidence has been received.

**Evidence received**

At least one submission exists but has not completed review.

**Under review**

A verification officer is examining the evidence.

**Consistent evidence**

Reviewed sources agree on the relevant figures within the stated comparison scope.

**Discrepancy detected**

Two or more relevant records contain conflicting information.

**Insufficient evidence**

The available material cannot support a reliable comparison.

**Review completed**

The verification team has completed the documented review.

These labels describe evidence conditions, not the legal validity of an election.

## 10.2 Public polling-unit page

Every public polling-unit page should contain:

- Official polling-unit identity.
- Election and contest.
- Available result figures.
- Evidence sources.
- Source classifications.
- Number of distinct contributors.
- Number of distinct organisations, where disclosable.
- Official IReV document reference, where available.
- Discrepancy summary.
- Review status.
- Timeline of important evidence events.
- Link to available source documents.
- Explanation of methodology.

Personal information of contributors must remain private unless there is an independently justified and lawful reason to disclose it.

## 10.3 Plain-language explanations

Technical messages must be translated into understandable language.

Example:

Instead of:
"Discrepancy detected between independent evidence sources."

Display:
"These result documents show different figures. Our verification team is examining the difference."

Instead of:
"Insufficient corroboration."

Display:
"We currently have only one usable record. We cannot yet compare it with another independent source."

---

# 11. Organisation Dashboard

## 11.1 Organisation registration

Organisations may apply to create a VeraVote organisation account.

Required information:
- Organisation name.
- Registration information where applicable.
- Contact person.
- Official contact details.
- Intended operational areas.
- Organisation type.
- Verification documents.

VeraVote must distinguish self-declared organisations from organisations whose identity and authority have been verified.

## 11.2 Organisation capabilities

- Manage members.
- Invite contributors.
- Review contributor applications.
- Allocate coverage.
- Monitor submission progress.
- View outstanding evidence.
- Review assigned polling-unit records.
- Escalate discrepancies.
- Export authorised reports.

An organisation must not be able to change a contributor's official INEC accreditation status.

## 11.3 Coverage reports

Reports should include:
- Assigned units.
- Unassigned units.
- Submissions received.
- Submissions awaiting review.
- Missing result documents.
- Units with discrepancies.
- Contributor participation.
- Review completion rates.

---

# 12. Verification and Investigation Workflow

## 12.1 Review queue

Verification officers need a central workspace with filters for:

- State.
- LGA.
- Ward.
- Polling unit.
- Election.
- Contest.
- Contributor type.
- Evidence type.
- Submission date.
- Review status.
- Discrepancy type.

## 12.2 Investigation workflow

1. Submission enters the review queue.
2. Reviewer examines the original.
3. OCR extraction is checked.
4. Other relevant submissions are identified.
5. Source relationships are examined.
6. Official records are retrieved or attached.
7. Differences are documented.
8. Reviewer records findings.
9. Senior reviewer approves sensitive outcomes where required.
10. Public status is updated.

## 12.3 Review outcomes

- Evidence accepted for comparison.
- Evidence rejected.
- Additional information requested.
- Discrepancy confirmed.
- Discrepancy unresolved.
- Insufficient evidence.
- Referred for further investigation.

## 12.4 Corrections and appeals

A contributor must be able to request correction of a factual error in their submission metadata.

A review decision must be challengeable through a documented process.

Previous decisions must remain visible in the internal audit history.

Public corrections must clearly identify what changed and when.

---

# 13. Public Citizen Evidence Submission

## 13.1 Purpose

Give citizens a way to contribute useful information without falsely presenting every citizen as an accredited observer.

## 13.2 Workflow

1. Citizen opens the public submission page.
2. Selects the polling unit.
3. Selects the type of evidence.
4. Uploads a photograph or document, or provides a public source link.
5. Adds an optional explanation.
6. Provides a contact method if they want follow-up.
7. Accepts the evidence-submission notice.
8. Receives a submission reference.

## 13.3 Restrictions

- Citizen evidence is not automatically published as verified.
- Public submissions cannot alter official result figures.
- Personal details are not displayed publicly.
- Malicious or duplicate submissions can be restricted.
- The system must preserve the distinction between original source and forwarded copy.
- Users must not be encouraged to trespass, interfere or place themselves in danger to obtain evidence.

---

# 14. Security, Privacy and Safety

Security and volunteer protection are core product requirements.

## 14.1 Privacy

VeraVote must:
- Collect only necessary personal information.
- Explain the purpose of every sensitive data field.
- Restrict access to identity documents.
- Encrypt sensitive information in transit and at rest.
- Keep public contributor profiles private by default.
- Provide data access and correction workflows.
- Define data retention and deletion schedules.
- Conduct a privacy impact assessment before large-scale deployment.

## 14.2 Security

- Secure authentication.
- Role-based access control.
- Strong administrative account protection.
- Rate limiting.
- Secure file uploads.
- Malware scanning.
- Signed or otherwise protected audit events.
- Encrypted backups.
- Monitoring for suspicious activity.
- Incident response procedures.

## 14.3 Volunteer safety

The platform must:
- Never require a contributor to confront officials, party agents or security personnel.
- Provide an emergency withdrawal mechanism.
- Avoid publicly displaying live volunteer locations.
- Avoid unnecessary public disclosure of assignment details.
- Allow contributors to report threats.
- Avoid pressuring contributors to obtain evidence where access is restricted.
- Provide guidance on lawful observation and safe conduct.

A contributor's safety takes priority over obtaining a submission.

## 14.4 Legal compliance

The product must be reviewed against:
- Electoral Act 2026.
- Applicable INEC election regulations and observer guidelines.
- Nigeria Data Protection Act 2023.
- Applicable laws governing photography, privacy and access to polling units.

The platform must not represent VeraVote as an official INEC platform or an accreditation authority.

---

# 15. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Public polling-unit search | P0 |
| FR-002 | Volunteer registration | P0 |
| FR-003 | Contributor identity verification workflow | P0 |
| FR-004 | Training and assessment | P1 |
| FR-005 | Contributor classification | P0 |
| FR-006 | Polling-unit assignment | P0 |
| FR-007 | Evidence capture and upload | P0 |
| FR-008 | Offline evidence storage | P0 |
| FR-009 | Submission receipt generation | P0 |
| FR-010 | Original evidence preservation | P0 |
| FR-011 | OCR extraction | P0 |
| FR-012 | Human correction of OCR | P0 |
| FR-013 | Arithmetic validation | P0 |
| FR-014 | Multi-source comparison | P0 |
| FR-015 | IReV document comparison | P0 |
| FR-016 | Public evidence explorer | P0 |
| FR-017 | Citizen evidence leads | P0 |
| FR-018 | Organisation dashboard | P1 |
| FR-019 | Investigation workflow | P0 |
| FR-020 | Audit log | P0 |
| FR-021 | SMS/USSD integration | P2 |
| FR-022 | Local-language audio guidance | P2 |
| FR-023 | Advanced source-independence analysis | P1 |
| FR-024 | Public data export/API | P2 |

Priority definitions:

- P0: Essential for the core product.
- P1: Important for the complete product.
- P2: Later enhancement.

---

# 16. Non-Functional Requirements

## 16.1 Performance

- Public search results should load quickly on low-bandwidth connections.
- The public interface should prioritise text over large images.
- Image uploads should support compression and resumable transfer.
- Common polling-unit queries should be indexed.

## 16.2 Availability

The production platform should target 99.5% monthly availability initially, with improved reliability targets before a major election.

## 16.3 Scalability

The architecture must support:
- All 36 states and FCT.
- All 774 LGAs/Area Councils.
- Nationwide polling-unit datasets.
- Large election-day submission bursts.
- Concurrent public evidence searches.
- Delayed offline synchronisation.

Capacity must be load-tested rather than assumed.

## 16.4 Accessibility

- Mobile-first responsive layout.
- Readable typography.
- Clear colour contrast.
- Simple language.
- Keyboard accessibility.
- Screen-reader-friendly labels.
- Low-bandwidth operation.
- English initially, with a roadmap for Pidgin, Hausa, Yoruba and Igbo.

## 16.5 Reliability

- Idempotent submission uploads.
- Retryable processing jobs.
- Duplicate-upload detection.
- Database backups.
- Storage integrity checks.
- Recovery procedures.
- Auditable status transitions.

---

# 17. Technical Architecture

## 17.1 Proposed stack

| Component | Technology |
|---|---|
| Frontend | Next.js |
| Application type | Progressive Web App |
| Backend | Python FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Evidence storage | Cloudflare R2 |
| Authentication | Secure session-based authentication |
| Offline storage | IndexedDB |
| Background jobs | Redis-backed worker or equivalent |
| OCR | PaddleOCR / Tesseract |
| Image processing | Pillow / OpenCV |
| Fingerprinting | SHA-256 |
| Maps | OpenStreetMap-compatible services |
| Hosting | Vercel + Railway or equivalent |

The architecture should separate the application API, evidence-processing workers and file storage.

## 17.2 Core data entities

**User**
- id
- name
- phone
- email
- account_status
- created_at

**ContributorProfile**
- user_id
- contributor_type
- identity_status
- training_status
- assessment_status
- official_accreditation_status
- organisation_id

**Organisation**
- id
- name
- organisation_type
- verification_status
- contact_details

**PollingUnit**
- id
- official_code
- state_id
- lga_id
- ward_id
- official_name
- location_description
- coordinates
- dataset_version

**Election**
- id
- name
- election_date
- election_type
- status

**Contest**
- id
- election_id
- office
- constituency

**Assignment**
- id
- contributor_id
- polling_unit_id
- election_id
- assignment_status
- assigned_at

**EvidenceSubmission**
- id
- contributor_id
- polling_unit_id
- election_id
- contest_id
- evidence_type
- original_file_key
- file_hash
- device_reported_time
- server_received_time
- submission_status

**ExtractedResult**
- id
- submission_id
- candidate_id
- extracted_votes
- corrected_votes
- confidence
- review_status

**OfficialResultDocument**
- id
- polling_unit_id
- election_id
- source_reference
- file_hash
- retrieved_at
- version_reference

**EvidenceComparison**
- id
- polling_unit_id
- source_a_id
- source_b_id
- comparison_result
- discrepancy_details
- review_status

**Investigation**
- id
- comparison_id
- assigned_reviewer
- investigation_status
- findings
- resolution

**AuditEvent**
- id
- actor_id
- entity_type
- entity_id
- action
- previous_value
- new_value
- timestamp

## 17.3 Suggested API groups

Authentication:
- POST /auth/register
- POST /auth/login
- POST /auth/verify-phone
- POST /auth/logout

Volunteer management:
- POST /volunteers/apply
- GET /volunteers/status
- POST /volunteers/training/complete
- POST /volunteers/assessment/submit

Geography:
- GET /states
- GET /lgas
- GET /wards
- GET /polling-units
- GET /polling-units/search

Assignments:
- GET /assignments
- POST /assignments/request
- POST /assignments/approve
- POST /assignments/withdraw

Evidence:
- POST /evidence
- GET /evidence/{id}
- POST /evidence/{id}/sync
- GET /polling-units/{id}/evidence

Verification:
- GET /verification/queue
- POST /verification/{id}/review
- POST /verification/{id}/correction
- POST /verification/{id}/escalate

Public:
- GET /public/polling-units/{id}
- GET /public/elections/{id}/results
- GET /public/discrepancies
- POST /public/evidence-leads

Organisations:
- POST /organisations
- GET /organisations/{id}/coverage
- POST /organisations/{id}/members
- POST /organisations/{id}/assignments

These are proposed interface contracts, not existing implemented endpoints.

---

# 18. Product Screens

## Public experience
1. Landing page.
2. Polling-unit search.
3. Polling-unit results page.
4. Evidence details.
5. Discrepancy explanation.
6. Submit evidence lead.
7. About VeraVote and methodology.

## Volunteer experience
1. Application.
2. Identity verification.
3. Training.
4. Assessment.
5. Contributor dashboard.
6. Assignment selection.
7. Evidence capture.
8. Submission history.
9. Safety and support.

## Organisation experience
1. Organisation registration.
2. Coordinator dashboard.
3. Contributor management.
4. Coverage allocation.
5. Submission monitoring.
6. Evidence review.
7. Reports.

## Verification experience
1. Verification dashboard.
2. Submission queue.
3. Document viewer.
4. OCR comparison.
5. Source comparison.
6. Investigation workspace.
7. Review history.

---

# 19. Critical Edge Cases

The product must explicitly handle these scenarios.

### Contributor and identity cases
- Two accounts using the same phone number.
- Fake identity details.
- A contributor fails the assessment.
- A trained volunteer claims official accreditation.
- A party agent submits without valid authorisation.
- An observer's accreditation expires or is revoked.
- A contributor changes their assigned area.

### Election-day cases
- Contributor has no internet.
- Phone battery dies.
- Phone storage is full.
- Upload is interrupted.
- The same photograph is uploaded several times.
- Several contributors photograph the same result poster.
- Contributor is unable to access the polling unit.
- Contributor is threatened or asked to leave.
- A polling unit is relocated.
- A result sheet is incomplete or illegible.

### Evidence cases
- Photograph is blurry.
- Image is cropped.
- Document is rotated.
- Figures are handwritten unclearly.
- OCR extracts the wrong candidate figures.
- The original image appears manipulated.
- A photograph is forwarded from another person.
- Multiple sources disagree.
- Official IReV document is not available.
- IReV document changes after initial publication.
- A result sheet has an arithmetic inconsistency.

### Public-access cases
- Citizen does not know the polling-unit code.
- Citizen has no smartphone.
- Citizen has limited literacy.
- Several polling units have similar names.
- Search returns no match.
- A public result is later corrected.
- A citizen submits misleading or malicious information.

Every case must have an explicit system response rather than being silently ignored.

---

# 20. Success Metrics

VeraVote must measure evidence quality and public usefulness, not just registrations or downloads.

## Volunteer network
- Number of completed applications.
- Percentage completing identity verification.
- Percentage passing training.
- Percentage receiving assignments.
- Percentage completing assigned tasks.

## Coverage
- Number of polling units with assigned contributors.
- Number with at least one received submission.
- Number with multiple distinct evidence sources.
- Number with no evidence.
- Coverage distribution across states and LGAs.

## Evidence quality
- Percentage of submissions successfully processed.
- OCR correction rate.
- Duplicate submission rate.
- Percentage with complete metadata.
- Percentage of comparisons requiring human intervention.

## Verification
- Median review time.
- Number of discrepancies identified.
- Number resolved.
- Number remaining unresolved.
- Percentage of public records with accessible supporting evidence.

## Citizen access
- Polling-unit searches.
- Public evidence page visits.
- Citizen evidence leads submitted.
- Evidence lead review completion rate.
- Public user feedback.

## Trust
- Number of correction requests.
- Number of successful appeals.
- Audit-log completeness.
- Privacy and security incidents.
- Percentage of public records with transparent methodology.

VeraVote must never present the number of registered volunteers as evidence of actual polling-unit coverage.

---

# 21. 48-Hour Hackathon MVP

The complete platform is the product vision. The hackathon prototype must demonstrate the central workflow convincingly.

## Must build

### A. Volunteer registration
- Application form.
- Basic identity-status simulation.
- Training and assessment flow.
- Contributor classification.

### B. Coverage management
- State, LGA, ward and polling-unit selection.
- Simple assignment workflow.
- Coverage dashboard.

### C. Evidence submission
- Image upload.
- Polling-unit association.
- Evidence receipt.
- File fingerprint.
- Submission status.

### D. Verification engine
- OCR or controlled simulated extraction.
- Human correction interface.
- Arithmetic checks.
- Comparison between multiple submissions.
- Comparison against simulated IReV data.

### E. Public explorer
- Search polling units.
- View result evidence.
- View evidence sources.
- View discrepancy status.
- Submit a citizen evidence lead.

## Demo scenarios

**Scenario A — Consistent evidence**

Two independently sourced observer submissions agree with the official document.

Expected output: Consistent evidence.

**Scenario B — Conflicting evidence**

Two observer submissions agree with each other, but the official document differs by 20 votes.

Expected output: Discrepancy detected; human review required.

**Scenario C — Insufficient evidence**

One contributor submits a result sheet, but there is no second source or official document.

Expected output: Evidence received; insufficient evidence for corroboration.

**Scenario D — Citizen evidence lead**

A citizen uploads a photograph of a result sheet displayed publicly.

Expected output: Citizen-submitted lead; pending verification.

All demo records must be clearly identified as simulated data. Do not imply live INEC integration.

## Excluded from the hackathon build

- Live nationwide deployment.
- Actual INEC accreditation.
- Full NIN verification integration.
- Live IReV API integration.
- Production-grade USSD.
- Automated fraud detection.
- Automated election-result certification.
- Nationwide language and audio coverage.
- Full incident-reporting and emergency-response systems.

---

# 22. Risks and Mitigation

| Risk | Mitigation |
|---|---|
| Existing products offer similar monitoring workflows | Differentiate through transparent evidence provenance, source-independence analysis and public review history |
| Fake or coordinated submissions | Identity checks, duplicate detection, source relationship tracking and human review |
| Volunteer safety concerns | Clear boundaries, safe withdrawal and private assignments |
| Legal confusion around observer accreditation | Separate VeraVote status from official INEC status |
| Poor connectivity | Offline-first capture and delayed sync |
| Incorrect OCR | Human confirmation and original-document preservation |
| Political manipulation | Source labels, conflict-of-interest controls and transparent methodology |
| Data breaches | Encryption, least privilege and incident response |
| Nationwide coverage claims without evidence | Publish actual coverage and missing-data indicators |
| Incorrect public conclusions | Careful evidence statuses, human review and correction mechanisms |

---

# 23. Product Roadmap

## Phase 1 — Hackathon prototype
- Functional demonstration.
- Simulated contributor onboarding.
- Evidence upload.
- Comparison workflow.
- Public polling-unit explorer.

## Phase 2 — Controlled operational pilot
- Real volunteer onboarding.
- Real identity-verification process.
- Authoritative polling-unit dataset.
- Legal and privacy review.
- Offline testing.
- Operational verification procedures.

## Phase 3 — Nationwide readiness
- State-level coverage management.
- Organisation partnerships.
- Election-day load testing.
- Multilingual support.
- Improved document extraction.
- Security testing.
- Disaster recovery.

## Phase 4 — Election operations
- Nationwide contributor recruitment.
- Coverage allocation.
- Evidence collection.
- Review and discrepancy management.
- Public reporting.

## Phase 5 — Post-election transparency
- Comprehensive evidence reports.
- Searchable historical records.
- Corrections and appeals.
- Public exports and research access.
- Long-term evidence retention according to policy.

---

# 24. Definition of Done

The first working prototype is complete when:

1. A person can apply to become a VeraVote volunteer.
2. The application can distinguish a community contributor from an officially accredited observer or authorised party agent.
3. A contributor can be assigned to a polling unit.
4. A contributor can submit a result-sheet photograph.
5. The system creates an evidence receipt.
6. The original image remains preserved.
7. The system extracts or simulates extraction of result figures.
8. A reviewer can correct the extracted figures.
9. The system can compare two evidence sources.
10. The system can compare independent evidence against an official reference document.
11. The system can flag a discrepancy without declaring fraud.
12. A citizen can search for a polling unit and inspect its evidence.
13. A citizen can submit an evidence lead.
14. The public interface explains the status of evidence in plain language.

---

# 25. Final Product Definition

VeraVote is a nationwide-capable, independently operated election evidence platform.

It brings together ordinary Nigerians, trained community contributors, accredited observers, party agents and civil society organisations to preserve and examine polling-unit result evidence.

Its defining capability is not simply collecting photographs or displaying election figures.

It is maintaining a transparent chain of evidence: who submitted a record, what document was submitted, when the server received it, how the figures were extracted, what other sources support or contradict it, what reviewers concluded and what remains unresolved.

**VeraVote does not ask Nigerians to trust another authority. It gives them evidence they can inspect.**