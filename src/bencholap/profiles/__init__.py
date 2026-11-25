"""Reviewed, named choices for shared runs.

Requests from the GitHub form or an issue can only pick names defined here:

* ``clusters/<name>.yaml``  where and how Trino runs (runner, nodes, memory, scale factors)
* ``presets.yaml``          how many warmups / repetitions / rounds
* ``variants/<name>.yaml``  sets of settings to run every target with

Nobody sets worker counts or Trino properties in a request. New choices are added by
pull request, so maintainers review them.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

DIR = Path(__file__).resolve().parent


@cache
def clusters() -> dict[str, dict]:
    out = {}
    for p in sorted((DIR / "clusters").glob("*.yaml")):
        d = yaml.safe_load(p.read_text())
        if d["name"] != p.stem:
            raise ValueError(f"{p}: name must match the file name")
        out[d["name"]] = d
    return out


@cache
def presets() -> dict[str, dict]:
    return yaml.safe_load((DIR / "presets.yaml").read_text())


@cache
def variants() -> dict[str, dict]:
    return {p.stem: yaml.safe_load(p.read_text()) for p in sorted((DIR / "variants").glob("*.yaml"))}


def cluster(name: str) -> dict:
    if name not in clusters():
        raise ValueError(f"unknown cluster profile {name!r}; available: {', '.join(clusters())}")
    return clusters()[name]
