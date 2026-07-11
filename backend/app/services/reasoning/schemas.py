"""Strict structured-output contracts for the four LLM prompts.

Every model forbids extra fields and requires excerpt citations for any
conclusion. These schemas are validated on every model response; invalid output
is retried once and otherwise triggers deterministic fallback.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.schemas.graph import Certainty, ClaimState, StrictModel

# --- Shared inputs ----------------------------------------------------------


class Excerpt(StrictModel):
    """A single public news/evidence excerpt supplied to the model."""

    excerpt_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    url: str = ""


class ApprovedClaim(StrictModel):
    """A claim already resolved by the deterministic publication policy.

    The model may explain this record but may never change its ``claim_state``,
    ``certainty``, or ``publish`` decision.
    """

    edge_id: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    claim_state: ClaimState
    certainty: Certainty
    required_condition: str
    condition_met: bool
    publish: bool


# --- A. Event fact extraction ----------------------------------------------


class EventFact(StrictModel):
    statement: str = Field(min_length=1)
    excerpt_ids: list[str] = Field(min_length=1)


class EventFactExtraction(StrictModel):
    facts: list[EventFact] = Field(default_factory=list)


# --- B. Applicability assessment -------------------------------------------


class ConditionStatus(StrEnum):
    MET = "met"
    UNMET = "unmet"
    INSUFFICIENT = "insufficient"


class ApplicabilityAssessment(StrictModel):
    condition_status: ConditionStatus
    supporting_excerpt_ids: list[str] = Field(default_factory=list)
    contradiction_excerpt_ids: list[str] = Field(default_factory=list)
    # Advisory only. The deterministic policy re-derives the published state and
    # the model can never elevate beyond a conditional pathway here.
    permitted_claim_state: ClaimState
    rationale_excerpt_ids: list[str] = Field(min_length=1)


# --- C. Explanation ---------------------------------------------------------


class Explanation(StrictModel):
    claim_state: ClaimState
    text: str = Field(min_length=1)
    mentions_unmet_condition: bool
    excerpt_ids: list[str] = Field(min_length=1)


# --- D. Faithfulness review -------------------------------------------------


class SentenceAssessment(StrictModel):
    sentence: str = Field(min_length=1)
    supported: bool
    supporting_excerpt_ids: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class FaithfulnessReview(StrictModel):
    sentences: list[SentenceAssessment] = Field(min_length=1)
    all_supported: bool
