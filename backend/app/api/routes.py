from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.schemas.api import (
    ConceptRippleResponse,
    EdgeDetailResponse,
    ErrorResponse,
    FeedResponse,
    HealthResponse,
    StoryDetailResponse,
    StoryRippleResponse,
)
from app.services.cache import PostgresRippleCache
from app.services.feed import FeedService
from app.services.repositories import GraphRepository, InvalidCursorError, StoryRepository
from app.services.ripples import RippleService

router = APIRouter()
DatabaseSession = Annotated[Session, Depends(get_session)]
Depth = Annotated[int, Query(ge=1, le=3)]


def feed_service(session: Session) -> FeedService:
    return FeedService(StoryRepository(session))


def ripple_service(session: Session) -> RippleService:
    return RippleService(
        StoryRepository(session),
        GraphRepository(session),
        PostgresRippleCache(session),
    )


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(session: DatabaseSession) -> HealthResponse:
    session.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="ok")


@router.get(
    "/feed",
    response_model=FeedResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["stories"],
)
def feed(
    session: DatabaseSession,
    domain: Annotated[str, Query(min_length=1)] = "energy",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> FeedResponse:
    try:
        return feed_service(session).feed(domain, limit, cursor)
    except InvalidCursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/story/{story_id}",
    response_model=StoryDetailResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["stories"],
)
def story(story_id: str, session: DatabaseSession) -> StoryDetailResponse:
    response = feed_service(session).story(story_id)
    if response is None:
        raise HTTPException(status_code=404, detail="story not found")
    return response


@router.get(
    "/story/{story_id}/ripples",
    response_model=StoryRippleResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["ripples"],
)
def story_ripples(story_id: str, session: DatabaseSession, depth: Depth = 2) -> StoryRippleResponse:
    response = ripple_service(session).story_ripples(story_id, depth)
    if response is None:
        raise HTTPException(status_code=404, detail="story not found")
    return response


@router.get(
    "/concept/{node_slug}/ripples",
    response_model=ConceptRippleResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["ripples"],
)
def concept_ripples(
    node_slug: str, session: DatabaseSession, depth: Depth = 2
) -> ConceptRippleResponse:
    response = ripple_service(session).concept_ripples(node_slug, depth)
    if response is None:
        raise HTTPException(status_code=404, detail="concept not found")
    return response


@router.get(
    "/edge/{edge_id}",
    response_model=EdgeDetailResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["evidence"],
)
def edge(edge_id: str, session: DatabaseSession) -> EdgeDetailResponse:
    response = ripple_service(session).edge_detail(edge_id)
    if response is None:
        raise HTTPException(status_code=404, detail="edge not found or not publishable")
    return response
