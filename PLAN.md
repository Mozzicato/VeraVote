# VeraVote — Hackathon MVP Build Plan

Source of truth: [prd.md](prd.md) §21 (48-hour MVP) and §24 (Definition of Done).

## Guiding rules (from the PRD — non-negotiable)

- VeraVote verifies **provenance and consistency**, never the truth of a result. No "fraud", "rigged" or "winner" language anywhere.
- All demo data is **clearly labelled simulated**. No claim of live INEC / IReV integration.
- A VeraVote-trained contributor is **never** shown as INEC-accredited.
- Original evidence is **never overwritten**. Extraction and corrections live in separate records. Every change writes an audit event.
- Device time is "device-reported", never "verified". Server-received time is recorded independently.
- Multiple photos ≠ multiple independent sources (same file hash = same document).

## Stack (MVP)

| Layer | Choice | Note |
|---|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic 2 | As PRD §17 |
| Database | SQLite locally (`DATABASE_URL` switch to PostgreSQL) | No Postgres installed; SQLAlchemy keeps it portable |
| File storage | Local `storage/` folder behind a storage interface | Swap for Cloudflare R2 later |
| Extraction | Controlled simulated extraction | PRD §21 D allows this; OCR plug-in point kept |
| Auth | Demo role switcher (`X-Demo-User` header) | Clearly marked as simulated; real sessions in Phase 2 |
| Frontend | Next.js (App Router, TypeScript), Tailwind, PWA manifest | Mobile-first, text-first |
| Offline | IndexedDB queue + client-generated submission IDs | Idempotent sync on the server |

## Milestones

### M1 — Backend foundation ✅
- Project layout, config, DB session, models for every PRD §17.2 entity.
- Seed: one demo state → LGA → wards → polling units (with landmark aliases), one election/contest/candidates, demo users for every role, one organisation.
- Audit log service.

### M2 — Verification engine (the core) ✅
- SHA-256 fingerprinting, original-file preservation.
- Simulated extraction → proposed fields with confidence.
- Human correction (with reason, audited) and confirm/reject.
- Arithmetic validation (candidate sum = valid votes; valid + rejected = cast; cast ≤ accredited).
- Source independence (distinct documents / contributors / organisations).
- Pairwise comparison incl. simulated IReV documents → public status per PRD §10.1.
- Seed the four demo scenarios A–D and test each produces the PRD's expected output.

### M3 — API ✅
- Geography + polling-unit search (code, name, alias, cascading selection).
- Volunteer application → identity simulation → training → assessment (80% pass mark, configurable) → classification.
- Assignments (request / approve / accept / withdraw) + coverage numbers that never count "assigned" as "observed".
- Evidence upload with client ID idempotency + receipt.
- Verification queue, review, correction, escalation.
- Public polling-unit page, discrepancies list, citizen evidence leads.

### M4 — Frontend: public explorer ✅
- Landing, search, polling-unit page (plain-language status, sources, timeline, methodology), submit evidence lead, about/methodology.

### M5 — Frontend: volunteer + offline capture ✅
- Application, training, assessment, dashboard, assignment selection, evidence capture with IndexedDB queue and sync states (PRD §8.2), submission history, safety/withdrawal.

### M6 — Frontend: verification + organisation ✅
- Review queue with filters, document viewer beside extracted fields, correction UI, source comparison, investigation record.
- Coordinator coverage dashboard.

### M7 — Demo polish ✅ (README walkthrough + Playwright end-to-end suite)
- Walkthrough script for scenarios A–D, "SIMULATED DATA" banner, README run instructions.

## Definition of Done checklist (PRD §24)

- [x] 1 Apply as volunteer
- [x] 2 Distinguish community contributor vs accredited observer vs party agent
- [x] 3 Assign contributor to a polling unit
- [x] 4 Submit a result-sheet photo
- [x] 5 Evidence receipt
- [x] 6 Original preserved
- [x] 7 Extract / simulate extraction
- [x] 8 Reviewer corrects figures
- [x] 9 Compare two evidence sources
- [x] 10 Compare against official reference document
- [x] 11 Flag discrepancy without declaring fraud
- [x] 12 Citizen searches and inspects a polling unit
- [x] 13 Citizen submits an evidence lead
- [x] 14 Plain-language status explanations
