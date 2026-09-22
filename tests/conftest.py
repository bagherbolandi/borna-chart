from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DB_FILE = Path("borna_chart.db")
if DB_FILE.exists():
    DB_FILE.unlink()

from app.core.db import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services.rate_limit_service import RateLimitService  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    engine.dispose()
    RateLimitService.reset()
    if DB_FILE.exists():
        DB_FILE.unlink()
    with TestClient(app) as test_client:
        yield test_client
