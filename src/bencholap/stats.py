"""Summary statistics and A/B comparison with bootstrap confidence intervals."""

from __future__ import annotations

import math
import random
import statistics
from collections.abc import Sequence

BOOTSTRAP_SAMPLES = 2000
SEED = 1234


def summarize(values: Sequence[float]) -> dict | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return {
        "n": len(vals), "median": statistics.median(vals), "mean": statistics.fmean(vals),
        "min": min(vals), "max": max(vals),
        "stdev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        "cv": (statistics.stdev(vals) / statistics.fmean(vals)) if len(vals) > 1 and statistics.fmean(vals) else 0.0,
    }


def ratio_ci(base: Sequence[float], head: Sequence[float], level: float = 0.95) -> dict | None:
    """Ratio of medians head/base with a percentile bootstrap interval.

    ratio < 1 means head is faster/smaller. ``significant`` is True when the whole
    interval is on one side of 1.
    """
    b = [v for v in base if v is not None]
    h = [v for v in head if v is not None]
    if not b or not h or statistics.median(b) == 0:
        return None
    point = statistics.median(h) / statistics.median(b)
    if len(b) < 2 or len(h) < 2:
        return {"ratio": point, "low": None, "high": None, "significant": False}
    rng = random.Random(SEED)
    samples = []
    for _ in range(BOOTSTRAP_SAMPLES):
        mb = statistics.median(rng.choices(b, k=len(b)))
        mh = statistics.median(rng.choices(h, k=len(h)))
        if mb > 0:
            samples.append(mh / mb)
    samples.sort()
    lo = samples[int((1 - level) / 2 * len(samples))]
    hi = samples[min(len(samples) - 1, int((1 + level) / 2 * len(samples)))]
    return {"ratio": point, "low": lo, "high": hi, "significant": hi < 1 or lo > 1}


def geomean(values: Sequence[float]) -> float | None:
    vals = [v for v in values if v and v > 0]
    return math.exp(statistics.fmean(math.log(v) for v in vals)) if vals else None
