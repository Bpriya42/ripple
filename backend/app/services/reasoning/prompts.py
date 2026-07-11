"""Prompt text and user-message builders for the four LLM contracts.

The system prompts are the verbatim contracts from the build handoff (Section 6).
User builders inject only the minimum necessary public excerpts and stable graph
definitions, honoring the Gemini data boundary.
"""

from __future__ import annotations

import json

from app.services.reasoning.schemas import ApprovedClaim, EventFact, Excerpt

PROMPT_VERSION = "m4-2026-07-11"

SYSTEM_EVENT_FACTS = (
    "Extract only facts explicitly stated in the supplied story excerpts. Do not "
    "infer causes, effects, motives, future outcomes, or missing details. For "
    "every fact, include one or more exact supporting excerpt IDs. If a fact is "
    "uncertain in the source, preserve that uncertainty. Return only the required "
    "JSON schema."
)

SYSTEM_APPLICABILITY = (
    "Assess whether the listed event facts meet the required condition of a known "
    "causal mechanism. A mechanism being valid does not prove its outcome has "
    "occurred. If the condition is unmet, return conditional_pathway. If evidence "
    "is insufficient or contradictory, return not_shown. Do not assign certainty; "
    "report only evidence facts, condition status, contradictions, and a permitted "
    "claim state. Cite excerpt IDs for every conclusion. Return only the required "
    "JSON schema."
)

SYSTEM_EXPLANATION = (
    "Write a concise public explanation using only the approved claim record and "
    "cited evidence excerpts. Preserve the exact claim state. Use conditional "
    "language when claim_state is conditional_pathway. Do not add facts, "
    "quantities, causal steps, forecasts, or certainty language not present in the "
    "input. Mention the unmet condition when one exists. Return only the required "
    "JSON schema."
)

SYSTEM_FAITHFULNESS = (
    "For each sentence in the proposed explanation, decide whether the supplied "
    "excerpts directly support it. Flag unsupported, overstated, causal, temporal, "
    "numeric, or certainty claims. Do not repair the explanation. Return only the "
    "required JSON schema."
)


def number_excerpts(excerpts: list[Excerpt]) -> str:
    return "\n".join(f"[{item.excerpt_id}] {item.text}" for item in excerpts)


def build_event_fact_user(story_metadata: dict[str, object], excerpts: list[Excerpt]) -> str:
    return (
        f"Story metadata: {json.dumps(story_metadata, sort_keys=True)}\n"
        f"Source excerpts:\n{number_excerpts(excerpts)}"
    )


def build_applicability_user(
    edge_definition: str,
    required_condition: str,
    event_facts: list[EventFact],
    excerpts: list[Excerpt],
) -> str:
    facts = json.dumps([fact.model_dump() for fact in event_facts], sort_keys=True)
    return (
        f"Known mechanism: {edge_definition}\n"
        f"Required condition: {required_condition}\n"
        f"Event facts: {facts}\n"
        f"Evidence excerpts:\n{number_excerpts(excerpts)}"
    )


def build_explanation_user(claim: ApprovedClaim, excerpts: list[Excerpt]) -> str:
    record = json.dumps(claim.model_dump(mode="json"), sort_keys=True)
    return f"Approved claim record: {record}\nEvidence excerpts:\n{number_excerpts(excerpts)}"


def build_faithfulness_user(draft: str, claim: ApprovedClaim, excerpts: list[Excerpt]) -> str:
    record = json.dumps(claim.model_dump(mode="json"), sort_keys=True)
    return (
        f"Proposed explanation: {draft}\n"
        f"Approved claim record: {record}\n"
        f"Evidence excerpts:\n{number_excerpts(excerpts)}"
    )
