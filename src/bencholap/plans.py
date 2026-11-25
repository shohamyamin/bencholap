"""Plan normalization, so that "plan changed" means the plan itself changed."""

from __future__ import annotations

import re

from .util import sha256_text


def normalize_plan(text: str) -> str:
    lines = [ln for ln in text.splitlines()
             if "Estimates:" not in ln and not ln.startswith("Trino version:")]
    # Trino symbol names carry generated numeric suffixes (sum_123); they change without the
    # plan shape changing.
    return re.sub(r"\b([a-z_]+)_\d+\b", r"\1", "\n".join(lines))


def plan_hash(text: str) -> str:
    return sha256_text(normalize_plan(text))[:16]


def query_plan_hash(q: dict) -> str | None:
    """Hash of a result record's plan, recomputed from the text when it is available."""
    plan = q.get("plan") or {}
    if plan.get("text"):
        return plan_hash(plan["text"])
    return plan.get("hash")
