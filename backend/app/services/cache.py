from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import RippleCache


class PostgresRippleCache:
    def __init__(self, session: Session, ttl: timedelta = timedelta(minutes=15)) -> None:
        self.session = session
        self.ttl = ttl

    def get(self, key: str) -> dict[str, Any] | None:
        item = self.session.scalar(select(RippleCache).where(RippleCache.cache_key == key))
        if item is None:
            return None
        if item.expires_at <= datetime.now(UTC):
            self.session.execute(delete(RippleCache).where(RippleCache.id == item.id))
            self.session.flush()
            return None
        return dict(item.payload)

    def set(self, key: str, payload: dict[str, Any]) -> None:
        expires_at = datetime.now(UTC) + self.ttl
        self.session.execute(
            insert(RippleCache)
            .values(cache_key=key, payload=payload, expires_at=expires_at)
            .on_conflict_do_update(
                constraint="uq_ripple_cache_key",
                set_={"payload": payload, "expires_at": expires_at},
            )
        )
        self.session.flush()
