from __future__ import annotations

import json
from pathlib import Path

from app.schemas.graph import FixtureStory


def load_story_fixture(path: Path, fixture_name: str) -> FixtureStory:
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        raw_story = data[fixture_name]
    except KeyError as exc:
        raise ValueError(f"unknown fixture: {fixture_name}") from exc
    story = FixtureStory.model_validate(raw_story)
    if not story.fixture:
        raise ValueError("story must be explicitly marked as a fixture")
    return story


def load_story_fixtures(path: Path) -> dict[str, FixtureStory]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = {name: FixtureStory.model_validate(raw) for name, raw in data.items()}
    if not all(story.fixture for story in fixtures.values()):
        raise ValueError("all stories must be explicitly marked as fixtures")
    return fixtures
