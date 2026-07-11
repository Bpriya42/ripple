"""LLM enrichment layer.

This package is strictly additive. The deterministic publication policy always
decides certainty and publication eligibility; the language model may only
explain an already-approved claim or propose source-grounded candidates. The
default provider is disabled, so the product runs with no model calls.
"""
