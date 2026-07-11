"""Demonstrate the enrichment pipeline on a fixture claim.

By default this uses the configured provider (disabled unless ``LLM_PROVIDER=gemini``
and ``LLM_API_KEY`` are set), so it shows the deterministic fallback. Pass
``--demo`` to run the full pipeline offline with canned fixture responses.

    uv run --project backend python scripts/explain_claim.py --demo
    uv run --project backend python scripts/explain_claim.py            # uses env provider
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.core.dotenv import load_dotenv
from app.schemas.graph import Certainty, ClaimState
from app.services.reasoning.enrichment import generate_explanation
from app.services.reasoning.provider import (
    LlmProvider,
    ScriptedLlmProvider,
    default_provider,
)
from app.services.reasoning.schemas import ApprovedClaim, Excerpt

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "fixtures" / "llm" / "enrichment_sample.json"

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

CLAIM = ApprovedClaim(
    edge_id="edge.hormuz_disruption__oil_price",
    mechanism="Hormuz carries large oil volumes; a material transit disruption can raise oil prices.",
    claim_state=ClaimState.CONDITIONAL_PATHWAY,
    certainty=Certainty.ESTABLISHED,
    required_condition="material disruption to Strait of Hormuz oil transit",
    condition_met=False,
    publish=True,
)


def _demo_provider() -> LlmProvider:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return ScriptedLlmProvider(
        {
            "explanation": [json.dumps(data["explanation_valid"])],
            "faithfulness": [json.dumps(data["faithfulness_valid"])],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run enrichment on a fixture claim")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use canned fixture responses instead of the configured provider.",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    provider = _demo_provider() if args.demo else default_provider()
    print(f"# provider: {provider.name} (enabled={provider.enabled})")
    result = generate_explanation(provider, CLAIM, EXCERPTS)
    print(
        json.dumps(
            {
                "published": result.published,
                "claim_state": result.claim_state.value,
                "explanation": result.explanation,
                "suppression_reason": result.suppression_reason,
                "trace": asdict(result.trace),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
