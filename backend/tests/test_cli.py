import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_threat_only_cli_outputs_conditional_pathway() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ripple_from_headline.py"),
            "--fixture",
            "threat_only_hormuz",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    first_edge = payload["ripple_chain"][0]
    assert payload["fixture"] is True
    assert first_edge["event_status"] == "threat_only"
    assert first_edge["condition_met"] is False
    assert first_edge["claim_state"] == "conditional_pathway"
    assert "material disruption" in first_edge["required_condition"]
    assert first_edge["evidence"]
    assert max(edge["hop"] for edge in payload["ripple_chain"]) <= payload["max_depth"]
