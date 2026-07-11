import json
from pathlib import Path
from typing import Any

import pytest

from app.schemas.graph import Certainty, ClaimState
from app.services.reasoning.enrichment import (
    assess_applicability,
    extract_event_facts,
    generate_explanation,
)
from app.services.reasoning.provider import (
    DisabledLlmProvider,
    LlmInvalidOutput,
    ScriptedLlmProvider,
)
from app.services.reasoning.schemas import ApprovedClaim, EventFact, Excerpt

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads(
    (ROOT / "data" / "fixtures" / "llm" / "enrichment_sample.json").read_text(encoding="utf-8")
)

EXCERPTS = [
    Excerpt(
        excerpt_id="source_12",
        text="The Strait of Hormuz carries a large share of seaborne oil.",
        url="https://www.eia.gov/",
    ),
    Excerpt(
        excerpt_id="source_47",
        text="Officials say transit remains open; no material disruption is confirmed.",
        url="https://example.invalid/",
    ),
]

CONDITIONAL_CLAIM = ApprovedClaim(
    edge_id="edge.hormuz_disruption__oil_price",
    mechanism="Hormuz carries large oil volumes; a material transit disruption can lift prices.",
    claim_state=ClaimState.CONDITIONAL_PATHWAY,
    certainty=Certainty.ESTABLISHED,
    required_condition="material disruption to Strait of Hormuz oil transit",
    condition_met=False,
    publish=True,
)


def _scripted(**responses: list[Any]) -> ScriptedLlmProvider:
    return ScriptedLlmProvider(
        {name: [json.dumps(item) for item in values] for name, values in responses.items()}
    )


def test_published_conditional_explanation_is_faithful() -> None:
    provider = _scripted(
        explanation=[FIXTURE["explanation_valid"]],
        faithfulness=[FIXTURE["faithfulness_valid"]],
    )
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is True
    assert result.claim_state is ClaimState.CONDITIONAL_PATHWAY
    assert result.explanation is not None
    assert "could" in result.explanation.lower()
    assert result.trace.provider == "scripted"
    assert result.trace.steps == ("explanation", "faithfulness")
    assert result.trace.faithfulness_all_supported is True


def test_conditional_language_is_required() -> None:
    draft = {**FIXTURE["explanation_valid"], "mentions_unmet_condition": False}
    provider = _scripted(explanation=[draft], faithfulness=[FIXTURE["faithfulness_valid"]])
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is False
    assert result.suppression_reason == "missing_conditional_language"


def test_unsupported_sentence_is_suppressed() -> None:
    unfaithful_draft = {
        "claim_state": "conditional_pathway",
        "text": "Oil prices have already risen sharply because of the closure.",
        "mentions_unmet_condition": True,
        "excerpt_ids": ["source_12"],
    }
    provider = _scripted(
        explanation=[unfaithful_draft],
        faithfulness=[FIXTURE["faithfulness_unsupported"]],
    )
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is False
    assert result.explanation is None
    assert result.suppression_reason == "unsupported_sentence"


def test_invalid_output_is_retried_once_then_succeeds() -> None:
    provider = ScriptedLlmProvider(
        {
            "explanation": ["{ not valid json", json.dumps(FIXTURE["explanation_valid"])],
            "faithfulness": [json.dumps(FIXTURE["faithfulness_valid"])],
        }
    )
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is True


def test_two_invalid_outputs_fall_back_deterministically() -> None:
    provider = ScriptedLlmProvider({"explanation": ["{ bad", "{ still bad"]})
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is False
    assert result.suppression_reason == "explanation_unavailable"


def test_model_cannot_alter_the_claim_state() -> None:
    elevated = {**FIXTURE["explanation_valid"], "claim_state": "observed_effect"}
    provider = _scripted(explanation=[elevated], faithfulness=[FIXTURE["faithfulness_valid"]])
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is False
    assert result.suppression_reason == "claim_state_altered"
    assert result.trace.model_claim_state == "observed_effect"


def test_citation_of_unknown_excerpt_is_suppressed() -> None:
    bad_cite = {**FIXTURE["explanation_valid"], "excerpt_ids": ["source_12", "source_999"]}
    provider = _scripted(explanation=[bad_cite], faithfulness=[FIXTURE["faithfulness_valid"]])
    result = generate_explanation(provider, CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is False
    assert result.suppression_reason == "cited_unknown_excerpt"


def test_policy_gate_blocks_unpublishable_claim_without_calling_model() -> None:
    not_shown = CONDITIONAL_CLAIM.model_copy(
        update={"claim_state": ClaimState.NOT_SHOWN, "publish": False}
    )
    # Empty provider would raise if called; the policy gate must return first.
    provider = ScriptedLlmProvider({})
    result = generate_explanation(provider, not_shown, EXCERPTS)
    assert result.published is False
    assert result.suppression_reason == "policy_does_not_permit"


def test_disabled_provider_keeps_core_deterministic() -> None:
    result = generate_explanation(DisabledLlmProvider(), CONDITIONAL_CLAIM, EXCERPTS)
    assert result.published is False
    assert result.suppression_reason == "llm_disabled"
    assert result.trace.provider == "disabled"


def test_applicability_clamps_overclaim_to_safe_state() -> None:
    over = {
        "condition_status": "met",
        "supporting_excerpt_ids": ["source_12"],
        "contradiction_excerpt_ids": [],
        "permitted_claim_state": "observed_effect",
        "rationale_excerpt_ids": ["source_12"],
    }
    provider = _scripted(applicability=[over])
    assessment = assess_applicability(
        provider,
        edge_definition=CONDITIONAL_CLAIM.mechanism,
        required_condition=CONDITIONAL_CLAIM.required_condition,
        event_facts=[
            EventFact(
                statement="Officials warned of a possible closure.", excerpt_ids=["source_47"]
            )
        ],
        excerpts=EXCERPTS,
    )
    assert assessment.permitted_claim_state is ClaimState.NOT_SHOWN


def test_event_fact_extraction_requires_citations() -> None:
    # A fact with no excerpt IDs violates the schema; two invalid outputs fail.
    invalid = {"facts": [{"statement": "Something happened.", "excerpt_ids": []}]}
    provider = _scripted(event_facts=[invalid, invalid])
    with pytest.raises(LlmInvalidOutput):
        extract_event_facts(provider, {"headline": "fixture"}, EXCERPTS)
