"""Deterministic story-to-node linking for live GDELT ingestion.

The linker maps a fresh article's GDELT themes onto curated graph nodes using
each node's ``gdelt_tags``. It never invents a mapping and never asserts that an
event-specific outcome has occurred: live stories are always resolved with
``condition_met=False`` so the publication policy renders their edges as
conditional pathways. Upgrading a live claim beyond a conditional pathway
requires evidence-grounded assessment and is deferred to the Milestone 4 LLM
applicability layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Keyword rules are intentionally small, documented, and conservative. They set
# only the descriptive ``event_status`` label; they never set ``condition_met``.
_THREAT_KEYWORDS = (
    "threat",
    "threaten",
    "warn",
    "vow",
    "could",
    "may ",
    "might",
    "risk",
    "possible",
    "plan to",
    "plans to",
    "weigh",
    "consider",
)
_DISRUPTION_KEYWORDS = (
    "close",
    "closed",
    "closure",
    "halt",
    "halted",
    "disrupt",
    "blockade",
    "block",
    "attack",
    "strike",
    "seiz",
    "shut",
    "suspend",
)


@dataclass(frozen=True)
class LinkableNode:
    """The minimal node information the linker needs, decoupled from the ORM."""

    slug: str
    gdelt_tags: tuple[str, ...]
    has_outgoing_edges: bool


@dataclass(frozen=True)
class NodeTagIndex:
    """A deterministic GDELT-theme -> node lookup built from curated nodes."""

    _by_tag: dict[str, tuple[str, ...]]
    _source_slugs: frozenset[str]

    def node_for_tags(self, tags: list[str]) -> str | None:
        """Return the best curated node slug for an article's themes, or None.

        Selection is deterministic and independent of theme ordering: among all
        candidate nodes whose ``gdelt_tags`` intersect the article's themes,
        nodes that have outgoing edges (and therefore produce a ripple) are
        preferred, with an alphabetical slug tie-break.
        """
        candidates: set[str] = set()
        for tag in tags:
            candidates.update(self._by_tag.get(_normalize_tag(tag), ()))
        if not candidates:
            return None
        return min(candidates, key=lambda slug: (slug not in self._source_slugs, slug))


def _normalize_tag(tag: str) -> str:
    return tag.strip().upper()


def build_node_tag_index(nodes: list[LinkableNode]) -> NodeTagIndex:
    """Index curated nodes by their GDELT themes for live story mapping."""
    by_tag: dict[str, set[str]] = {}
    source_slugs: set[str] = set()
    for node in nodes:
        if node.has_outgoing_edges:
            source_slugs.add(node.slug)
        for tag in node.gdelt_tags:
            normalized = _normalize_tag(tag)
            if normalized:
                by_tag.setdefault(normalized, set()).add(node.slug)
    frozen = {tag: tuple(sorted(slugs)) for tag, slugs in by_tag.items()}
    return NodeTagIndex(_by_tag=frozen, _source_slugs=frozenset(source_slugs))


def classify_event_status(title: str, excerpt: str) -> tuple[str, bool]:
    """Derive a descriptive event status and the always-unmet condition flag.

    The returned ``condition_met`` is always ``False`` for live ingestion: a
    keyword match is not evidence that a mechanism's required condition has
    actually been satisfied. Threat language takes precedence over disruption
    language so a "threatens to close" headline is labelled ``threat_only``.
    """
    text = f"{title} {excerpt}".lower()
    if any(keyword in text for keyword in _THREAT_KEYWORDS):
        return "threat_only", False
    if any(keyword in text for keyword in _DISRUPTION_KEYWORDS):
        return "disruption_reported", False
    return "reported", False


def live_prominence_reasons(
    published_at: datetime,
    now: datetime,
    source_country: str,
    curated_edge_count: int,
) -> list[str]:
    """Build transparent, human-readable prominence reasons for a live story."""
    reasons: list[str] = ["live GDELT ingestion"]

    hours = max((now - published_at).total_seconds() / 3600.0, 0.0)
    if hours < 1:
        reasons.append("published within the hour")
    elif hours < 6:
        reasons.append(f"recent (within {int(hours) + 1} hours)")
    elif hours < 24:
        reasons.append("published today")
    else:
        reasons.append("older than a day")

    if curated_edge_count > 0:
        plural = "mechanism" if curated_edge_count == 1 else "mechanisms"
        reasons.append(f"{curated_edge_count} curated {plural} from the matched node")
    else:
        reasons.append("no established ripple yet")

    if source_country:
        reasons.append(f"origin: {source_country}")
    return reasons
