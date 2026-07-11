"""Enrichment orchestration.

Turns an already-approved deterministic claim into a published, source-faithful
explanation, or suppresses it. The deterministic publication policy is supreme:
the model may only explain a claim the policy already approved, must preserve the
exact claim state, and every generated sentence must be supported by cited
excerpts. The model never assigns certainty or decides publication eligibility.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.schemas.graph import ClaimState
from app.services.reasoning.prompts import (
    PROMPT_VERSION,
    SYSTEM_APPLICABILITY,
    SYSTEM_EVENT_FACTS,
    SYSTEM_EXPLANATION,
    SYSTEM_FAITHFULNESS,
    build_applicability_user,
    build_event_fact_user,
    build_explanation_user,
    build_faithfulness_user,
)
from app.services.reasoning.provider import (
    LlmError,
    LlmProvider,
    LlmRequest,
    parse_with_retry,
)
from app.services.reasoning.schemas import (
    ApplicabilityAssessment,
    ApprovedClaim,
    ConditionStatus,
    EventFact,
    EventFactExtraction,
    Excerpt,
    Explanation,
    FaithfulnessReview,
)

logger = logging.getLogger("ripple.reasoning")

# The model may never elevate a live claim beyond these states; anything else is
# clamped to the safe, non-published state.
_ALLOWED_APPLICABILITY_STATES = {ClaimState.CONDITIONAL_PATHWAY, ClaimState.NOT_SHOWN}


@dataclass(frozen=True)
class EnrichmentTrace:
    provider: str
    prompt_version: str
    steps: tuple[str, ...]
    model_claim_state: str | None = None
    faithfulness_all_supported: bool | None = None


@dataclass(frozen=True)
class EnrichmentResult:
    published: bool
    claim_state: ClaimState
    explanation: str | None
    suppression_reason: str | None
    trace: EnrichmentTrace


def _suppressed(
    claim: ApprovedClaim,
    provider: LlmProvider,
    steps: list[str],
    reason: str,
    *,
    model_claim_state: str | None = None,
    faithfulness: bool | None = None,
) -> EnrichmentResult:
    logger.info("enrichment suppressed edge=%s reason=%s", claim.edge_id, reason)
    return EnrichmentResult(
        published=False,
        claim_state=claim.claim_state,
        explanation=None,
        suppression_reason=reason,
        trace=EnrichmentTrace(
            provider=provider.name,
            prompt_version=PROMPT_VERSION,
            steps=tuple(steps),
            model_claim_state=model_claim_state,
            faithfulness_all_supported=faithfulness,
        ),
    )


def generate_explanation(
    provider: LlmProvider,
    claim: ApprovedClaim,
    excerpts: list[Excerpt],
) -> EnrichmentResult:
    """Produce a published explanation only if every gate passes."""
    steps: list[str] = []
    known_ids = {excerpt.excerpt_id for excerpt in excerpts}

    # Gate 0: the deterministic policy must already permit publication.
    if not claim.publish or claim.claim_state is ClaimState.NOT_SHOWN:
        return _suppressed(claim, provider, steps, "policy_does_not_permit")

    if not provider.enabled:
        return _suppressed(claim, provider, steps, "llm_disabled")

    # Step 1: draft the explanation (retry once on invalid schema).
    steps.append("explanation")
    request = LlmRequest(
        system=SYSTEM_EXPLANATION,
        user=build_explanation_user(claim, excerpts),
        schema_name="explanation",
        json_schema=Explanation.model_json_schema(),
    )
    try:
        draft = parse_with_retry(provider, request, Explanation)
    except LlmError:
        logger.warning("enrichment explanation failed edge=%s; falling back", claim.edge_id)
        return _suppressed(claim, provider, steps, "explanation_unavailable")

    # Deterministic integrity gates on the draft.
    if draft.claim_state is not claim.claim_state:
        return _suppressed(
            claim, provider, steps, "claim_state_altered", model_claim_state=draft.claim_state.value
        )
    if not set(draft.excerpt_ids).issubset(known_ids):
        return _suppressed(claim, provider, steps, "cited_unknown_excerpt")
    if claim.claim_state is ClaimState.CONDITIONAL_PATHWAY and not draft.mentions_unmet_condition:
        return _suppressed(claim, provider, steps, "missing_conditional_language")

    # Step 2: faithfulness review of the drafted sentences.
    steps.append("faithfulness")
    review_request = LlmRequest(
        system=SYSTEM_FAITHFULNESS,
        user=build_faithfulness_user(draft.text, claim, excerpts),
        schema_name="faithfulness",
        json_schema=FaithfulnessReview.model_json_schema(),
    )
    try:
        review = parse_with_retry(provider, review_request, FaithfulnessReview)
    except LlmError:
        logger.warning("enrichment review failed edge=%s; falling back", claim.edge_id)
        return _suppressed(claim, provider, steps, "faithfulness_unavailable")

    supported = review.all_supported and all(item.supported for item in review.sentences)
    cited_ok = all(
        set(item.supporting_excerpt_ids).issubset(known_ids) for item in review.sentences
    )
    if not supported or not cited_ok:
        return _suppressed(
            claim,
            provider,
            steps,
            "unsupported_sentence",
            model_claim_state=draft.claim_state.value,
            faithfulness=review.all_supported,
        )

    logger.info("enrichment published edge=%s provider=%s", claim.edge_id, provider.name)
    return EnrichmentResult(
        published=True,
        claim_state=claim.claim_state,
        explanation=draft.text,
        suppression_reason=None,
        trace=EnrichmentTrace(
            provider=provider.name,
            prompt_version=PROMPT_VERSION,
            steps=tuple(steps),
            model_claim_state=draft.claim_state.value,
            faithfulness_all_supported=True,
        ),
    )


def extract_event_facts(
    provider: LlmProvider,
    story_metadata: dict[str, object],
    excerpts: list[Excerpt],
) -> EventFactExtraction:
    """Extract attributable facts (prompt A) with strict validation."""
    request = LlmRequest(
        system=SYSTEM_EVENT_FACTS,
        user=build_event_fact_user(story_metadata, excerpts),
        schema_name="event_facts",
        json_schema=EventFactExtraction.model_json_schema(),
    )
    return parse_with_retry(provider, request, EventFactExtraction)


def assess_applicability(
    provider: LlmProvider,
    edge_definition: str,
    required_condition: str,
    event_facts: list[EventFact],
    excerpts: list[Excerpt],
) -> ApplicabilityAssessment:
    """Assess applicability (prompt B), clamping any over-claim to a safe state.

    The model's ``permitted_claim_state`` is advisory. Anything outside the
    allowed set (conditional pathway or not shown) is treated as ``not_shown``;
    the deterministic policy remains the sole publication authority.
    """
    request = LlmRequest(
        system=SYSTEM_APPLICABILITY,
        user=build_applicability_user(edge_definition, required_condition, event_facts, excerpts),
        schema_name="applicability",
        json_schema=ApplicabilityAssessment.model_json_schema(),
    )
    assessment = parse_with_retry(provider, request, ApplicabilityAssessment)
    if assessment.permitted_claim_state not in _ALLOWED_APPLICABILITY_STATES:
        logger.info(
            "clamping applicability claim_state=%s -> not_shown",
            assessment.permitted_claim_state.value,
        )
        return assessment.model_copy(update={"permitted_claim_state": ClaimState.NOT_SHOWN})
    if assessment.condition_status is ConditionStatus.MET:
        # A met condition is a deterministic-evidence decision, never the model's.
        logger.info("applicability reported condition met; downgraded for policy authority")
    return assessment
