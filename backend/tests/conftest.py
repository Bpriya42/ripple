from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.main import app
from app.models import RippleCache


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with Session(get_engine()) as session, session.begin():
        session.execute(delete(RippleCache))
    with TestClient(app) as test_client:
        yield test_client
