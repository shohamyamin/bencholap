"""Result correctness: compare query output with the official TPC answer sets.

Answer files are only published for SF1. For other scale factors the report compares
result fingerprints across configurations instead (all configurations of a run read the
same dataset, so their results must agree).
"""

from __future__ import annotations

import datetime as dt
import decimal
import hashlib
import re
from pathlib import Path
from typing import Any

from .benchmarks import Benchmark

ABS_TOL = 0.01      # answers are printed with 2 decimals (TPC-DS sometimes 6)
REL_TOL = 1e-6


def norm_cell(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float, decimal.Decimal)):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return str(v).strip()


def fingerprint(rows: list[tuple]) -> str:
    h = hashlib.sha256()
    for row in rows:
        cells = []
        for c in row:
            c = norm_cell(c)
            cells.append("NULL" if c is None else f"{c:.2f}" if isinstance(c, float) else c)
        h.update(("\x1f".join(cells) + "\n").encode())
    return h.hexdigest()[:16]


def _num(s: str) -> float | None:
    try:
        return float(s)
    except ValueError:
        return None


def _cells_equal(actual: Any, expected: str | None) -> bool:
    if expected is None:
        return actual is None
    if actual is None:
        return False
    if isinstance(actual, float):
        e = _num(expected)
        return e is not None and abs(actual - e) <= max(ABS_TOL, REL_TOL * abs(e))
    if isinstance(actual, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", actual):
        return expected.startswith(actual)
    return actual == expected


def _rows_equal(a: list[Any], e: list[str | None]) -> bool:
    return len(a) == len(e) and all(_cells_equal(x, y) for x, y in zip(a, e))


_ROWCOUNT = re.compile(r"^\(\d+ rows?\)$|^\d+ rows? selected\.?$|^Elapsed:", re.IGNORECASE)
_SEPARATOR = re.compile(r"^[-|+ \t]+$")


def parse_answer(path: Path, fmt: str) -> list[list[str | None]]:
    """Parse an answer file. TPC-DS files for two-statement queries hold two result sets,
    each with its own header and a "N rows selected." trailer."""
    rows: list[list[str | None]] = []
    expect_header = True
    for line in path.read_text(errors="replace").splitlines():
        if not line.strip() or _SEPARATOR.match(line):
            continue
        if _ROWCOUNT.match(line.strip()):
            expect_header = True
            continue
        cells = [c.strip() for c in line.split("|")] if "|" in line else [line.strip()]
        if expect_header:
            expect_header = False
            continue
        rows.append([c if c != "" else None for c in cells])
    return rows


def _sort_key(row: list[Any]) -> tuple:
    out = []
    for c in row:
        if c is None:
            out.append((0, ""))
        elif isinstance(c, float):
            out.append((1, f"{c:020.1f}"))
        else:
            f = _num(c) if isinstance(c, str) else None
            out.append((1, f"{f:020.1f}") if f is not None else (2, c))
    return tuple(out)


def compare(actual_rows: list[tuple], expected: list[list[str | None]]) -> dict:
    actual = [[norm_cell(c) for c in r] for r in actual_rows]
    if len(actual) != len(expected):
        return {"status": "mismatch", "detail": f"row count {len(actual)} != expected {len(expected)}"}
    if all(_rows_equal(a, e) for a, e in zip(actual, expected)):
        return {"status": "match"}
    # ties in ORDER BY may legitimately permute rows: compare order-insensitively
    a_sorted, e_sorted = sorted(actual, key=_sort_key), sorted(expected, key=_sort_key)
    for a, e in zip(a_sorted, e_sorted):
        if not _rows_equal(a, e):
            return {"status": "mismatch", "detail": f"first differing row: got {a!r}, expected {e!r}"[:500]}
    return {"status": "match", "detail": "rows match ignoring order of ties"}


def validate(bench: Benchmark, qid: str, sf: str, result_sets: list[list[tuple]]) -> dict:
    files = bench.answer_file(qid, sf)
    if not files:
        return {"status": "no-reference"}
    rows = [r for rs in result_sets for r in rs]
    last = None
    for f in files:
        try:
            expected = parse_answer(f, bench.answers_format or "")
        except Exception as e:  # noqa: BLE001
            return {"status": "unparsable-reference", "reference": f.name, "detail": str(e)}
        res = compare(rows, expected)
        res["reference"] = f.name
        if res["status"] == "match":
            return res
        last = res
    return last or {"status": "no-reference"}
