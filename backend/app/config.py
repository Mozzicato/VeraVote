"""Runtime configuration. Every value can be overridden with an environment variable."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("VERAVOTE_DATABASE_URL", f"sqlite:///{BASE_DIR / 'veravote.db'}")
STORAGE_DIR = Path(os.getenv("VERAVOTE_STORAGE_DIR", BASE_DIR / "storage"))
CORS_ORIGINS = os.getenv("VERAVOTE_CORS_ORIGINS", "http://localhost:3000").split(",")

# PRD §4.5: configurable pass mark, proposed starting threshold 80%.
ASSESSMENT_PASS_MARK = float(os.getenv("VERAVOTE_ASSESSMENT_PASS_MARK", "0.8"))

# Upload limits (PRD §14.2 secure file uploads).
MAX_UPLOAD_BYTES = int(os.getenv("VERAVOTE_MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))
ALLOWED_UPLOAD_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

# The hackathon build only ever runs on simulated data (PRD §21).
SIMULATED_MODE = True
