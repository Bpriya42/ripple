from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import build_engine
from app.models import Edge, EvidenceSource, Node


def test_bootstrap_imported_fixture_graph() -> None:
    with Session(build_engine()) as session:
        assert session.scalar(select(func.count()).select_from(Node)) >= 10
        assert session.scalar(select(func.count()).select_from(Edge)) >= 10
        assert session.scalar(select(func.count()).select_from(EvidenceSource)) >= 1
