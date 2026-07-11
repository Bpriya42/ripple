from __future__ import annotations

from app.schemas.api import (
    FeedItemResponse,
    FeedResponse,
    StoryDetailResponse,
    StorySourceResponse,
)
from app.services.repositories import StoryRepository


def source_response(source: object) -> StorySourceResponse:
    return StorySourceResponse.model_validate(source)


class FeedService:
    def __init__(self, stories: StoryRepository) -> None:
        self.stories = stories

    def feed(self, domain: str, limit: int, cursor: str | None) -> FeedResponse:
        stories, next_cursor = self.stories.list_feed(domain, limit, cursor)
        sources = self.stories.sources([story.id for story in stories])
        return FeedResponse(
            items=[
                FeedItemResponse(
                    story_id=story.slug,
                    headline=story.headline,
                    published_at=story.published_at,
                    origin_location=story.origin_location,
                    sources=[source_response(item) for item in sources[story.id]],
                    domain=story.domain,
                    prominence_reasons=story.prominence_reasons,
                    fixture=story.fixture,
                )
                for story in stories
            ],
            next_cursor=next_cursor,
        )

    def story(self, slug: str) -> StoryDetailResponse | None:
        story = self.stories.get(slug)
        if story is None:
            return None
        sources = self.stories.sources([story.id])[story.id]
        nodes = self.stories.matched_nodes(story.id)
        return StoryDetailResponse(
            story_id=story.slug,
            headline=story.headline,
            published_at=story.published_at,
            origin_location=story.origin_location,
            sources=[source_response(item) for item in sources],
            domain=story.domain,
            prominence_reasons=story.prominence_reasons,
            fixture=story.fixture,
            event_status=story.event_status,
            themes=story.themes,
            entities=story.entities,
            mapped_nodes=[node.slug for node in nodes],
        )
