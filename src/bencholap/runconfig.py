"""Run configuration (YAML) — what to benchmark, against which targets and variants.

Example::

    name: trino-483-vs-484
    benchmark: tpch
    scale_factor: 1
    layout: unpartitioned          # a layout from the benchmark definition (`bencholap layouts`)
    # layouts: [unpartitioned, sorted]   # or several: every target runs on every layout
    # loaders: [default, head]       # optional: who writes the datasets: the pinned loader ("default")
    #                                # and/or targets by name; every target reads every copy
    queries: all                   # or [q01, q06]
    match: "avg\\s*\\("             # optional: only queries whose SQL matches this regex
    warmup: 1                      # unmeasured executions per query
    repetitions: 3                 # measured executions per query
    rounds: 1                      # >1 alternates targets (A B A B) to spread machine noise
    profile_mode: false            # true: one profiled pass per configuration after the measurements
    timeout: 10m                   # per-query limit
    resources: {memory: 10g, cpus: 4}   # per engine container
    cluster: {type: docker, workers: 0}  # docker | command | external, see engines/trino
    targets:
      - {name: base, source: "483"}
      - name: head
        source: "github:me/trino@my-branch"
        catalog: {iceberg: {iceberg.some-property: "value"}}   # added on top of the version profile
    variants:
      - {name: default}
      - name: no-fs-cache
        config: {cache-manager.config-files: null}           # null removes a property
        session: {enable_dynamic_filtering: false}

Each target x variant pair is one "configuration" in the results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import benchmarks


@dataclass
class Overrides:
    catalog: dict[str, dict[str, Any]] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    session: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> Overrides:
        return cls(catalog=d.get("catalog") or {}, config=d.get("config") or {}, session=d.get("session") or {})

    def as_dict(self) -> dict:
        return {k: v for k, v in {"catalog": self.catalog, "config": self.config, "session": self.session}.items() if v}


@dataclass
class TargetSpec:
    name: str
    source: str
    engine: str
    overrides: Overrides
    cluster: dict | None = None


@dataclass
class Variant:
    name: str
    overrides: Overrides
    description: str = ""


@dataclass
class RunConfig:
    name: str
    benchmark: str
    scale_factor: str
    layout: str            # first layout (kept for callers that need one)
    queries: list[str]
    warmup: int
    repetitions: int
    rounds: int
    timeout: str
    resources: dict[str, Any]
    capture_plans: bool
    cluster: dict
    targets: list[TargetSpec]
    variants: list[Variant]
    # dataset keys: a layout name, or "<layout>@<target name>" for a copy written by that target
    layouts: list[str] = field(default_factory=list)
    profile_mode: bool = False
    raw: dict = field(default_factory=dict)

    def configurations(self) -> list[tuple[TargetSpec, Variant]]:
        return [(t, v) for t in self.targets for v in self.variants]

    def dataset_loader(self, key: str) -> TargetSpec | None:
        """The target that writes the dataset `key`, None for the pinned default loader."""
        _, _, name = key.partition("@")
        return next(t for t in self.targets if t.name == name) if name else None


def _combine(a: Overrides, b: Overrides) -> Overrides:
    catalog = {k: dict(v) for k, v in a.catalog.items()}
    for name, props in b.catalog.items():
        catalog.setdefault(name, {}).update(props)
    return Overrides(catalog, {**a.config, **b.config}, {**a.session, **b.session})


def merged_overrides(t: TargetSpec, v: Variant) -> Overrides:
    return _combine(t.overrides, v.overrides)


def select_queries(bench: benchmarks.Benchmark, sf: str, queries, match: str | None) -> list[str]:
    """`queries`: "all", a named subset ("quick"), "q01,q06" or a list; `match`: regex searched (case-insensitive) in the
    canonical SQL, e.g. "avg\\s*\\(" for every query that computes an average."""
    if queries in (None, "all"):
        selected = list(bench.queries)
    elif isinstance(queries, str) and queries.strip() in (bench.subsets or {}):
        selected = list(bench.subsets[queries.strip()]["queries"])
    elif isinstance(queries, str):
        selected = [q.strip() for q in queries.split(",") if q.strip()]
    else:
        selected = list(queries)
    unknown = set(selected) - set(bench.queries)
    if unknown:
        raise ValueError(f"unknown {bench.name} queries: {sorted(unknown)}")
    if match:
        rx = re.compile(match, re.IGNORECASE)
        selected = [q for q in selected if rx.search(bench.query(q, sf).canonical_sql)]
        if not selected:
            raise ValueError(f"no {bench.name} query matches {match!r}")
    return selected


def from_dict(d: dict) -> RunConfig:
    bench = benchmarks.load(d.get("benchmark", "tpch"))
    sf = benchmarks.format_sf(d.get("scale_factor", 1))
    queries = select_queries(bench, sf, d.get("queries", "all"), d.get("match"))
    engine = d.get("engine", "trino")
    targets = []
    for i, t in enumerate(d.get("targets") or []):
        if isinstance(t, (str, int)):
            t = {"source": str(t)}
        targets.append(TargetSpec(name=str(t.get("name") or t["source"]), source=str(t["source"]),
                                  engine=t.get("engine", engine), overrides=Overrides.from_dict(t),
                                  cluster=t.get("cluster")))
    if not targets:
        raise ValueError("a run needs at least one target")
    if len({t.name for t in targets}) != len(targets):
        raise ValueError("target names must be unique")
    variants = [Variant(str(v["name"]), Overrides.from_dict(v), v.get("description", ""))
                for v in (d.get("variants") or [{"name": "default"}])]
    names = d.get("layouts") or [d.get("layout")]
    if isinstance(names, str):
        names = [x.strip() for x in names.split(",") if x.strip()]
    layouts = list(dict.fromkeys(bench.layout(n).name for n in names))
    layout = layouts[0]
    loaders = d.get("loaders") or ["default"]
    if isinstance(loaders, str):
        loaders = [x.strip() for x in loaders.split(",") if x.strip()]
    target_names = {t.name for t in targets}
    unknown = [x for x in loaders if x != "default" and x not in target_names]
    if unknown:
        raise ValueError(f"loaders {unknown} are neither `default` nor target names {sorted(target_names)}")
    layouts = [lay if loader == "default" else f"{lay}@{loader}" for lay in layouts for loader in dict.fromkeys(loaders)]
    return RunConfig(
        name=d.get("name") or " vs ".join(t.name for t in targets),
        benchmark=bench.name, scale_factor=sf, layout=layout,
        queries=queries, warmup=int(d.get("warmup", 1)), repetitions=int(d.get("repetitions", 3)),
        rounds=int(d.get("rounds", 1)), timeout=str(d.get("timeout", "10m")),
        resources=d.get("resources") or {"memory": "10g"}, capture_plans=bool(d.get("capture_plans", True)),
        cluster=d.get("cluster") or {"type": "docker", "workers": 0},
        targets=targets, variants=variants, layouts=layouts, profile_mode=bool(d.get("profile_mode")), raw=d,
    )


def load(path: Path) -> RunConfig:
    return from_dict(yaml.safe_load(Path(path).read_text()))
