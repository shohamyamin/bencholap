"""Benchmark definitions: tables, canonical queries, official answers, validated layouts.

Canonical queries are the official generator output (see scripts/generate-queries) and are
the source of truth. An engine may override a query only through a file in
``benchmarks/<name>/overrides/<engine>/[sf<N>/]<query>.sql`` that states its reason in a
``-- reason:`` header line; every override used is recorded in the results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

BENCH_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class TableLayout:
    partitioning: tuple[str, ...] = ()
    sorted_by: tuple[str, ...] = ()
    bloom_filter_columns: tuple[str, ...] = ()
    # maximum rows per Parquet row group when writing (Trino session property
    # parquet_writer_row_group_max_row_count); smaller row groups give min/max and bloom filters
    # something to skip
    row_group_rows: int | None = None

    def as_dict(self) -> dict:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items() if v}


@dataclass(frozen=True)
class Layout:
    name: str
    description: str
    validated: bool
    sources: tuple[dict, ...]
    analyze: bool
    tables: dict[str, TableLayout]
    basis: str = ""   # why a layout that is not a published setup exists

    def table(self, name: str) -> TableLayout:
        return self.tables.get(name, TableLayout())

    def as_dict(self) -> dict:
        return {
            "name": self.name, "description": " ".join(self.description.split()), "validated": self.validated,
            "basis": " ".join(self.basis.split()),
            "sources": list(self.sources), "analyze": self.analyze,
            "tables": {t: tl.as_dict() for t, tl in self.tables.items()},
        }


@dataclass(frozen=True)
class Query:
    id: str
    benchmark: str
    scale_factor: str
    canonical_sql: str
    sql: str
    override: dict | None = None
    statements: tuple[str, ...] = field(default=())


def _split_statements(sql: str) -> tuple[str, ...]:
    body = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    parts = [p.strip() for p in re.split(r";\s*(?:\n|$)", body)]
    return tuple(p for p in parts if p)


def format_sf(sf: float | str) -> str:
    f = float(sf)
    return str(int(f)) if f.is_integer() else str(f)


@dataclass(frozen=True)
class Benchmark:
    name: str
    title: str
    tables: tuple[str, ...]
    queries: tuple[str, ...]
    answers_sf: str | None
    answers_format: str | None
    default_layout: str
    layouts: dict[str, Layout]
    generator: dict
    supported_sf: tuple[str, ...] = ()
    answer_exceptions: dict | None = None
    staging: dict | None = None   # custom raw table DDL / load SELECT files
    subsets: dict | None = None   # named query subsets, e.g. "quick"

    @property
    def dir(self) -> Path:
        return BENCH_DIR / self.name

    def descriptions(self) -> dict[str, str]:
        p = self.dir / "descriptions.yaml"
        return yaml.safe_load(p.read_text()) if p.exists() else {}

    def scale_factors(self) -> list[str]:
        return list(self.supported_sf)

    def layout(self, name: str | None) -> Layout:
        name = name or self.default_layout
        if name not in self.layouts:
            raise ValueError(f"unknown layout {name!r} for {self.name}; available: {sorted(self.layouts)}")
        return self.layouts[name]

    def query(self, qid: str, sf: str | float, engine: str | None = None) -> Query:
        sf = format_sf(sf)
        if sf not in self.supported_sf:
            raise ValueError(f"{self.name} supports scale factors {list(self.supported_sf)}, not {sf}")
        path = self.dir / "queries" / f"sf{sf}" / f"{qid}.sql"
        if not path.exists():
            path = self.dir / "queries" / "any" / f"{qid}.sql"
        canonical = path.read_text()
        sql, override = canonical, None
        if engine:
            for cand in (self.dir / "overrides" / engine / f"sf{sf}" / f"{qid}.sql",
                         self.dir / "overrides" / engine / f"{qid}.sql"):
                if cand.exists():
                    sql = cand.read_text()
                    reason = re.findall(r"^--\s*reason:\s*(.+)$", sql, re.MULTILINE)
                    if not reason:
                        raise ValueError(f"override {cand} must state a '-- reason:' header")
                    override = {"engine": engine, "file": str(cand.relative_to(BENCH_DIR)),
                                "reason": " ".join(reason)}
                    break
        return Query(qid, self.name, sf, canonical, sql, override, _split_statements(sql))

    def answer_file(self, qid: str, sf: str | float) -> list[Path]:
        """Official answer files for a query (TPC-DS may have NULLS FIRST/LAST variants)."""
        if self.answers_sf is None or format_sf(sf) != self.answers_sf:
            return []
        adir = self.dir / "answers"
        if self.answers_format == "tpch":
            p = adir / f"{qid}.out"
            return [p] if p.exists() else []
        n = int(qid[1:])
        exact = adir / f"{n}.ans"
        if exact.exists():
            return [exact]
        return sorted(adir.glob(f"{n}_NULLS_*.ans"))


@cache
def load(name: str) -> Benchmark:
    path = BENCH_DIR / name / "benchmark.yaml"
    if not path.exists():
        raise ValueError(f"unknown benchmark {name!r}; available: {available()}")
    d = yaml.safe_load(path.read_text())
    layouts = {}
    for lname, ld in d["layouts"].items():
        tables = {
            t: TableLayout(**{k: (v if isinstance(v, (str, int)) else tuple(v)) for k, v in (spec or {}).items()})
            for t, spec in (ld.get("tables") or {}).items()
        }
        unknown = set(tables) - set(d["tables"])
        if unknown:
            raise ValueError(f"layout {lname} references unknown tables {unknown}")
        if not ld.get("validated") and not ld.get("basis"):
            raise ValueError(f"{name} layout {lname}: a layout that is not a published setup needs a 'basis'")
        layouts[lname] = Layout(lname, ld.get("description", ""), bool(ld.get("validated")),
                                tuple(ld.get("sources") or []), bool(ld.get("analyze", True)), tables,
                                ld.get("basis", ""))
    answers = d.get("answers") or {}
    return Benchmark(
        name=d["name"], title=d["title"], tables=tuple(d["tables"]), queries=tuple(d["queries"]),
        answers_sf=format_sf(answers["scale_factor"]) if answers else None,
        answers_format=answers.get("format"), default_layout=d["default_layout"], layouts=layouts,
        generator=d.get("generator", {}),
        supported_sf=tuple(format_sf(x) for x in d["scale_factors"]),
        answer_exceptions=answers.get("exceptions"),
        staging=d.get("staging"),
        subsets=d.get("subsets") or {},
    )


def available() -> list[str]:
    return sorted(p.parent.name for p in BENCH_DIR.glob("*/benchmark.yaml"))
