#!/usr/bin/env python3
"""Create the Trino overrides for canonical TPC-DS queries that Trino cannot plan as written.

Each override is the canonical text with the smallest edit that makes it valid Trino SQL,
matching the corresponding query in Trino's own benchmark suite
(trinodb/trino testing/trino-benchmark-queries/src/main/resources/sql/trino/tpcds/).
Re-run after regenerating canonical queries:  python3 scripts/make_trino_overrides.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "bencholap" / "benchmarks" / "tpcds"
SRC = ROOT / "queries" / "any"
DST = ROOT / "overrides" / "trino"
TRINO_REF = "trinodb/trino testing/trino-benchmark-queries/src/main/resources/sql/trino/tpcds/{q}.sql"

DATE_LITERAL = re.compile(r"(?<!cast\()'(\d{4}-\d{1,2}-\d{1,2})'")


def cast_date_literals(sql: str) -> str:
    return DATE_LITERAL.sub(r"cast('\1' as date)", sql)


INT_DIV = ("integer / integer truncates in Trino, while the TPC-DS answers assume exact division; "
           "the dividend is cast to decimal, as in Trino's own benchmark query")


def sub(pattern: str, repl: str):
    return lambda q: re.sub(pattern, repl, q)


EDITS = {
    # Trino does not implicitly coerce varchar literals to date.
    **{q: (("string literal compared with a date column; Trino has no implicit varchar-to-date "
           "coercion, so the literal is wrapped in cast(... as date)"), cast_date_literals)
       for q in ("q16", "q32", "q58", "q92", "q94", "q95")},
    "q21": (INT_DIV, sub(r"then inv_after / inv_before", "then cast(inv_after as decimal(7,2)) / inv_before")),
    "q34": (INT_DIV, sub(r"then household_demographics\.hd_dep_count/",
                         "then cast(household_demographics.hd_dep_count as decimal(7,2))/")),
    "q73": (INT_DIV, sub(r"household_demographics\.hd_dep_count/",
                         "cast(household_demographics.hd_dep_count as decimal(7,2))/")),
    "q78": (INT_DIV, sub(r"round\(ss_qty/", "round(cast(ss_qty as decimal(10,2))/")),
    "q83": ("string literals compared with a date column are wrapped in cast(... as date) (no implicit "
            "varchar-to-date coercion in Trino); " + INT_DIV,
            lambda q: re.sub(r"(\w+_item_qty)/\(sr_item_qty\+", r"\1/(cast(sr_item_qty as decimal(9,4))+",
                             cast_date_literals(q))),
    "q72": ("date + integer is not defined in Trino; written as date + interval 'N' day",
            lambda s: re.sub(r"(d1\.d_date)\s*\+\s*(\d+)\b", r"\1 + interval '\2' day", s)),
    # The template's ORDER BY references v1.<col> outside the scope where v1 is visible.
    "q47": (("ORDER BY references v1.s_store_name outside the CTE where v1 is in scope; the "
            "equivalent output column s_store_name of v2 is used"),
            lambda s: re.sub(r"(order by sum_sales - avg_monthly_sales,\s*)v1\.", r"\1", s)),
    "q57": (("ORDER BY references v1.cc_name outside the CTE where v1 is in scope; the "
            "equivalent output column cc_name of v2 is used"),
            lambda s: re.sub(r"(order by sum_sales - avg_monthly_sales,\s*)v1\.", r"\1", s)),
}


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for q, (reason, fn) in EDITS.items():
        canonical = (SRC / f"{q}.sql").read_text()
        header = [ln for ln in canonical.splitlines() if ln.startswith("--")]
        body = "\n".join(ln for ln in canonical.splitlines() if not ln.startswith("--")) + "\n"
        new = fn(body)
        if new == body:
            raise SystemExit(f"{q}: edit did not change the query")
        lines = [f"-- Trino override of {q} (canonical: queries/any/{q}.sql)",
                 f"-- reason: {reason}.",
                 f"-- compare: {TRINO_REF.format(q=q)}"] + header
        (DST / f"{q}.sql").write_text("\n".join(lines) + "\n" + new)
        print(f"wrote {DST / (q + '.sql')}")


if __name__ == "__main__":
    main()
