import pytest
from pydantic import ValidationError

from app.services.reasoning.schemas import (
    EventFact,
    Explanation,
    FaithfulnessReview,
)


def test_explanation_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        Explanation.model_validate(
            {
                "claim_state": "conditional_pathway",
                "text": "x",
                "mentions_unmet_condition": True,
                "excerpt_ids": ["source_1"],
                "certainty": "established",  # not allowed; certainty is never model-assigned
            }
        )


def test_event_fact_requires_at_least_one_excerpt() -> None:
    with pytest.raises(ValidationError):
        EventFact.model_validate({"statement": "something", "excerpt_ids": []})


def test_faithfulness_requires_at_least_one_sentence() -> None:
    with pytest.raises(ValidationError):
        FaithfulnessReview.model_validate({"sentences": [], "all_supported": True})


def test_explanation_rejects_unknown_claim_state() -> None:
    with pytest.raises(ValidationError):
        Explanation.model_validate(
            {
                "claim_state": "definitely_true",
                "text": "x",
                "mentions_unmet_condition": False,
                "excerpt_ids": ["source_1"],
            }
        )
