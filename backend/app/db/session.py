from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import database_url


def build_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url(), pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return build_engine()


def build_session(url: str | None = None) -> Session:
    return Session(build_engine(url))
