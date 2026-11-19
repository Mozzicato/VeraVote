import os
import shutil
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="veravote-test-")
os.environ["VERAVOTE_DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["VERAVOTE_STORAGE_DIR"] = f"{_TMP}/storage"

from fastapi.testclient import TestClient  # noqa: E402

from app import seed  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    seed.reset()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def users(client):
    return {u["name"].split()[0].lower(): u["id"] for u in client.get("/demo/users").json()}


def as_user(uid: int) -> dict:
    return {"X-Demo-User": str(uid)}


def png(seed_bytes: bytes = b"x") -> bytes:
    return b"\x89PNG\r\n\x1a\n" + seed_bytes * 64


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)
