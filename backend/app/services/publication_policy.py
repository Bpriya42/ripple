from __future__ import annotations

from dataclasses import dataclass

from app.schemas.graph import Certainty, ClaimState, Provenance


@dataclass(frozen=True)
class PolicyInput:
    provenance: Provenance
    condition_met: bool
    direct_outcome_evidence: bool = False
    independent_source_count: int = 0
    high_impact: bool = False
    contradiction: bool = False
    contradiction_can_be_presented: bool = False


@dataclass(frozen=True)
class PolicyDecision:
    claim_state: ClaimState
    certainty: Certainty
    certainty_reasons: tuple[str, ...]
    publish: bool
    contested: bool


def evaluate_publication(value: PolicyInput) -> PolicyDecision:
    """Apply the deterministic causal publication policy.

    Certainty describes evidence support for the mechanism, never a forecast.
    """
    threshold = 3 if value.high_impact else 2
    if value.contradiction and not value.contradiction_can_be_presented:
        return PolicyDecision(
            ClaimState.NOT_SHOWN,
            Certainty.SPECULATIVE,
            ("credible contradiction cannot be presented fairly",),
            False,
            False,
        )

    contested = value.contradiction and value.contradiction_can_be_presented
    contested_reason = ("credible contradiction is presented",) if contested else ()

    if value.direct_outcome_evidence:
        return PolicyDecision(
            ClaimState.OBSERVED_EFFECT,
            Certainty.ESTABLISHED,
            ("direct event-specific outcome evidence",) + contested_reason,
            True,
            contested,
        )

    if value.provenance is Provenance.CURATED:
        if value.condition_met:
            return PolicyDecision(
                ClaimState.ESTABLISHED_MECHANISM,
                Certainty.ESTABLISHED,
                ("curated mechanism", "required condition is met") + contested_reason,
                True,
                contested,
            )
        return PolicyDecision(
            ClaimState.CONDITIONAL_PATHWAY,
            Certainty.ESTABLISHED,
            ("curated mechanism", "required condition is not met") + contested_reason,
            True,
            contested,
        )

    if value.independent_source_count >= threshold and not value.contradiction:
        return PolicyDecision(
            ClaimState.EMERGING_SIGNAL,
            Certainty.EMERGING,
            (f"{value.independent_source_count} independent sources meet threshold {threshold}",),
            True,
            False,
        )

    reason = (
        f"{value.independent_source_count} independent sources do not meet threshold {threshold}"
    )
    return PolicyDecision(
        ClaimState.NOT_SHOWN,
        Certainty.SPECULATIVE,
        (reason,) + contested_reason,
        False,
        contested,
    )
