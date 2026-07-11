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
