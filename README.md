# VeraVote — hackathon MVP

Independent election-evidence platform: preserve polling-unit result evidence, compare sources, and show the public
what the evidence says, in plain language. **All data is simulated. No live INEC or IReV integration.**

Spec: [prd.md](prd.md) · Build plan: [PLAN.md](PLAN.md)

## Run it

Needs Python 3.12+ and Node 20+.

```bash
# API (http://localhost:8000, docs at /docs). First start creates and seeds backend/veravote.db.
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # macOS/Linux: .venv/bin/pip
.venv/Scripts/python -m uvicorn app.main:app --port 8000

# Web app (http://localhost:3000)
cd frontend
npm install
npm run dev
```

Tests:
- API: `cd backend && .venv/Scripts/python -m pytest -q` (22 tests: scenarios A–D, privacy, idempotent sync, audit tampering…)
- Browser walkthrough: with the API running, `cd frontend && npx playwright install chromium && npm run e2e`.
  Drives the whole demo below in Chromium (desktop + 360px phone) and saves screenshots to `frontend/e2e/screenshots/`.
  It resets the demo data first.
Reset demo data: `POST http://localhost:8000/demo/reset` (or `python -m app.seed`).

Use **“Viewing as”** in the header to switch between demo people. Sign-in is simulated (`X-Demo-User` header).

## Demo walkthrough (PRD §21 scenarios)

| # | As | Go to | You'll see |
|---|---|---|---|
| A | Public visitor | Search “Central School”, open **Central Primary School I** | *Records agree*: 2 observers from 2 organisations + official copy, same figures |
| B | Public visitor | **Discrepancies** → Central Primary School II | *Records differ*: observers agree, official copy +20 for BNP. Human review required, no fraud claim |
| C | Public visitor | Search “Jetty” | *Not enough evidence to compare*: one source only |
| D | Public visitor | Search “Health Centre” | *Evidence received*, citizen lead pending verification |
| — | Chika Umeh (verifier) | **Verification** → Open Space beside Town Mosque | Simulated extraction with one misread field. Correct it (reason required), confirm, accept → status updates |
| — | Chika Umeh | Same unit → **Open unit workspace** → attach official doc | Matching figures → *Records agree*; different → *Records differ* |
| — | Chika, then Yusuf Garba | Scenario B unit → open investigation → close as “Discrepancy confirmed” | Needs senior approval; once approved → *Review completed* with public summary |
| — | Public visitor | **Volunteer** → apply (OTP `123456`) → 5 modules → assessment | Classified as *VeraVote-trained (not INEC-accredited)* |
| — | Tunde Bakare | **My assignments** → capture a photo (try offline in DevTools) | Saved on phone → synced → receipt with SHA-256 |
| — | Funke Adebayo (coordinator) | **Coverage** | Honest counts: assigned ≠ observed. Approve Emeka's pending request |

## Layout

```
backend/app/
  models.py              PRD §17.2 entities (+ audit hash chain, unit status)
  services/engine.py     comparison, source independence, public status (the core)
  services/extraction.py simulated extraction; OCR plugs in here
  services/arithmetic.py result-form arithmetic checks
  services/audit.py      append-only hash-chained audit log
  services/intake.py     upload validation, fingerprinting, receipts, idempotency
  routers/               public, volunteers, field (assignments/evidence/safety), verification, organisations, demo
  seed.py, demo_data.py  simulated geography, people and scenarios A–D
frontend/src/
  app/                   pages (public explorer, volunteer, contributor, verify, organisation)
  lib/offline.ts         IndexedDB capture queue + idempotent sync
```

## Deliberate MVP shortcuts

- SQLite by default; set `VERAVOTE_DATABASE_URL` for PostgreSQL.
- Files stored on local disk (`backend/storage/`) behind a storage interface; swap for Cloudflare R2.
- Extraction is simulated per PRD §21 D; real OCR (PaddleOCR / Tesseract) is not wired in.
- Phone OTP and identity checks are simulated; official status is checked manually by a reviewer.
- Uploads are type-sniffed and size-limited; malware scanning is a marked hook, not implemented.
