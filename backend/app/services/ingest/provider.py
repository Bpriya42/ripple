from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import Field, HttpUrl

from app.schemas.graph import StrictModel


class NormalizedStory(StrictModel):
    slug: str
    headline: str
    published_at: datetime
    origin_location: str
    themes: list[str]
    entities: list[str]
    source_outlet: str
    source_url: HttpUrl
    source_excerpt: str
    mapped_node: str
    event_status: str
    condition_met: bool


class StoryProvider(Protocol):
    def fetch(self) -> list[NormalizedStory]: ...


class FixtureArticle(StrictModel):
    fixture_id: str
    title: str
    seendate: datetime
    sourcecountry: str
    themes: list[str]
    entities: list[str]
    domain: str
    url: HttpUrl
    excerpt: str
    mapped_node: str
    event_status: str
    condition_met: bool


class FixturePayload(StrictModel):
    fixture: bool
    articles: list[FixtureArticle] = Field(min_length=1)


class FixtureGdeltProvider:
    """Normalize a checked-in GDELT-shaped payload; never performs networking."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(self) -> list[NormalizedStory]:
        payload = FixturePayload.model_validate_json(self.path.read_text(encoding="utf-8"))
        if not payload.fixture:
            raise ValueError("mock GDELT payload must be explicitly marked as a fixture")
        return [
            NormalizedStory(
                slug=f"story.fixture.gdelt.{article.fixture_id}",
                headline=f"Fixture: {article.title}",
                published_at=article.seendate,
                origin_location=article.sourcecountry,
                themes=article.themes,
                entities=article.entities,
                source_outlet=f"Fixture GDELT ({article.domain})",
                source_url=article.url,
                source_excerpt=article.excerpt,
                mapped_node=article.mapped_node,
                event_status=article.event_status,
                condition_met=article.condition_met,
            )
            for article in payload.articles
        ]
