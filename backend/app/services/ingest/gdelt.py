"""GDELT 2.0 DOC API adapter for live energy-news ingestion.

The adapter fetches fresh articles per curated GDELT theme, deduplicates them,
maps each to a curated graph node via the deterministic linker, and normalizes
them into :class:`NormalizedStory` records the ingestion job can persist.

Network access lives only in :class:`HttpGdeltDocClient` and is opt-in. Tests
drive the parser and provider through :class:`RecordedGdeltDocClient`, which
reads a checked-in fixture and never touches the network.
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from pydantic import HttpUrl

from app.core.config import gdelt_base_url
from app.services.ingest.provider import NormalizedStory
from app.services.linker import (
    NodeTagIndex,
    classify_event_status,
    live_prominence_reasons,
)

_USER_AGENT = "RippleIngest/0.1 (+https://github.com/ripple; educational research)"
_DEFAULT_MAX_RECORDS = 25
_DEFAULT_TIMESPAN = "1d"


class GdeltArticle:
    """A single normalized article returned by the DOC API."""

    __slots__ = ("url", "title", "seendate", "domain", "sourcecountry")

    def __init__(
        self,
        *,
        url: str,
        title: str,
        seendate: datetime,
        domain: str,
        sourcecountry: str,
    ) -> None:
        self.url = url
        self.title = title
        self.seendate = seendate
        self.domain = domain
        self.sourcecountry = sourcecountry


def parse_seendate(value: str) -> datetime:
    """Parse a GDELT ``seendate`` (compact ``YYYYMMDDThhmmssZ`` or ISO 8601)."""
    raw = value.strip()
    try:
        return datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except ValueError:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def parse_doc_response(body: str) -> list[GdeltArticle]:
    """Parse a DOC API JSON body into articles, tolerating empty responses."""
    text = body.strip()
    if not text:
        return []
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError:
        return []
    raw_articles = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(raw_articles, list):
        return []
    articles: list[GdeltArticle] = []
    for entry in raw_articles:
        if not isinstance(entry, dict):
            continue
        url = str(entry.get("url", "")).strip()
        title = str(entry.get("title", "")).strip()
        seendate = str(entry.get("seendate", "")).strip()
        if not url or not title or not seendate:
            continue
        articles.append(
            GdeltArticle(
                url=url,
                title=title,
                seendate=parse_seendate(seendate),
                domain=str(entry.get("domain", "")).strip(),
                sourcecountry=str(entry.get("sourcecountry", "")).strip(),
            )
        )
    return articles


class GdeltDocClient(Protocol):
    def fetch_theme(self, theme: str) -> list[GdeltArticle]: ...


class HttpGdeltDocClient:
    """Live DOC API client. The only component that performs networking."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        max_records: int = _DEFAULT_MAX_RECORDS,
        timespan: str = _DEFAULT_TIMESPAN,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url or gdelt_base_url()
        self.max_records = max_records
        self.timespan = timespan
        self.timeout = timeout

    def fetch_theme(self, theme: str) -> list[GdeltArticle]:
        query = urllib.parse.urlencode(
            {
                "query": f"theme:{theme} sourcelang:english",
                "mode": "ArtList",
                "format": "json",
                "maxrecords": str(self.max_records),
                "timespan": self.timespan,
                "sort": "DateDesc",
            }
        )
        request = urllib.request.Request(  # noqa: S310 - fixed https GDELT endpoint
            f"{self.base_url}?{query}",
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            body = response.read().decode("utf-8", "replace")
        return parse_doc_response(body)


class RecordedGdeltDocClient:
    """Offline client that replays a checked-in DOC API fixture."""

    def __init__(self, path: Path) -> None:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("fixture") is not True:
            raise ValueError("recorded GDELT payload must be explicitly marked as a fixture")
        queries = payload.get("queries", {})
        if not isinstance(queries, dict):
            raise ValueError("recorded GDELT payload must contain a 'queries' object")
        self._by_theme: dict[str, list[GdeltArticle]] = {
            theme: parse_doc_response(json.dumps(response)) for theme, response in queries.items()
        }

    def fetch_theme(self, theme: str) -> list[GdeltArticle]:
        return self._by_theme.get(theme, [])


def _story_slug(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]  # noqa: S324 - id only
    return f"story.gdelt.{digest}"


class GdeltProvider:
    """Compose a DOC client and the linker into normalized live stories."""

    def __init__(
        self,
        client: GdeltDocClient,
        index: NodeTagIndex,
        themes: list[str],
        edge_counts: dict[str, int],
        *,
        now: datetime | None = None,
    ) -> None:
        self.client = client
        self.index = index
        self.themes = themes
        self.edge_counts = edge_counts
        self.now = now or datetime.now(UTC)

    def fetch(self) -> list[NormalizedStory]:
        collected: dict[str, GdeltArticle] = {}
        themes_by_url: dict[str, set[str]] = {}
        for theme in self.themes:
            for article in self.client.fetch_theme(theme):
                collected.setdefault(article.url, article)
                themes_by_url.setdefault(article.url, set()).add(theme)

        stories: list[NormalizedStory] = []
        for url, article in collected.items():
            themes = sorted(themes_by_url[url])
            mapped_node = self.index.node_for_tags(themes)
            event_status, condition_met = classify_event_status(article.title, "")
            curated_edges = self.edge_counts.get(mapped_node, 0) if mapped_node else 0
            stories.append(
                NormalizedStory(
                    slug=_story_slug(url),
                    headline=article.title,
                    published_at=article.seendate,
                    origin_location=article.sourcecountry or "Unknown",
                    themes=themes,
                    entities=[],
                    source_outlet=article.domain or "unknown source",
                    source_url=HttpUrl(url),
                    source_excerpt=article.title,
                    event_status=event_status,
                    condition_met=condition_met,
                    prominence_reasons=live_prominence_reasons(
                        published_at=article.seendate,
                        now=self.now,
                        source_country=article.sourcecountry,
                        curated_edge_count=curated_edges,
                    ),
                    fixture=False,
                    mapped_node=mapped_node,
                )
            )
        stories.sort(key=lambda story: story.slug)
        return stories
