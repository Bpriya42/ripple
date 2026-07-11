import pytest

from app.schemas.graph import Certainty, ClaimState, Provenance
from app.services.publication_policy import PolicyInput, evaluate_publication


@pytest.mark.parametrize(
    ("policy_input", "state", "publish"),
    [
        (
            PolicyInput(Provenance.CURATED, True, direct_outcome_evidence=True),
            ClaimState.OBSERVED_EFFECT,
            True,
        ),
        (
            PolicyInput(Provenance.CURATED, True),
            ClaimState.ESTABLISHED_MECHANISM,
            True,
        ),
        (
            PolicyInput(Provenance.CURATED, False),
            ClaimState.CONDITIONAL_PATHWAY,
            True,
        ),
        (
            PolicyInput(Provenance.AI_SUGGESTED, True, independent_source_count=2),
            ClaimState.EMERGING_SIGNAL,
            True,
        ),
        (
            PolicyInput(Provenance.AI_SUGGESTED, True, independent_source_count=1),
            ClaimState.NOT_SHOWN,
            False,
        ),
        (
            PolicyInput(
                Provenance.AI_SUGGESTED,
                True,
                independent_source_count=2,
                high_impact=True,
            ),
            ClaimState.NOT_SHOWN,
            False,
        ),
        (
            PolicyInput(
                Provenance.AI_SUGGESTED,
                True,
                independent_source_count=3,
                high_impact=True,
            ),
            ClaimState.EMERGING_SIGNAL,
            True,
        ),
        (
            PolicyInput(Provenance.CURATED, True, contradiction=True),
            ClaimState.NOT_SHOWN,
            False,
        ),
    ],
)
def test_publication_policy_rows(
    policy_input: PolicyInput, state: ClaimState, publish: bool
) -> None:
    decision = evaluate_publication(policy_input)
    assert decision.claim_state is state
    assert decision.publish is publish


def test_presentable_contradiction_is_contested() -> None:
    decision = evaluate_publication(
        PolicyInput(
            Provenance.CURATED,
            True,
            contradiction=True,
            contradiction_can_be_presented=True,
        )
    )
    assert decision.claim_state is ClaimState.ESTABLISHED_MECHANISM
    assert decision.contested is True


def test_threat_only_hormuz_is_conditional_and_established() -> None:
    decision = evaluate_publication(PolicyInput(Provenance.CURATED, condition_met=False))
    assert decision.claim_state is ClaimState.CONDITIONAL_PATHWAY
    assert decision.certainty is Certainty.ESTABLISHED
    assert "required condition is not met" in decision.certainty_reasons
