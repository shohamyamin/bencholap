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
    return " ".join(str(actual).split()) == " ".join(expected.split())


def _rows_equal(a: list[Any], e: list[str | None]) -> bool:
    return len(a) == len(e) and all(_cells_equal(x, y) for x, y in zip(a, e))


_ROWCOUNT = re.compile(r"^\(\d+ rows?\)$|^\d+ rows? selected\.?$|^Elapsed:", re.IGNORECASE)
_SEPARATOR = re.compile(r"^[-|+ \t]+$")
_DASHES = re.compile(r"-+")
_NOISE = re.compile(r"^(?:-+ OUTPUT Query \d+|INSERT \d+ \d+|(?:CREATE|DROP|SELECT) \d*)\s*$")


def _fixed_width_cells(line: str, spans: list[tuple[int, int]]) -> list[str]:
    """Assign each whitespace-separated token to the column it starts in. Some answer files
    are off by one character after tab expansion, so a token starting one position before
    a column belongs to that column."""
    cells = [[] for _ in spans]
    starts = [a for a, _ in spans]
    for m in re.finditer(r"\S+", line):
        k = max((j for j, a in enumerate(starts) if a <= m.start() + 1), default=0)
        cells[k].append(m.group(0))
    return [" ".join(c) for c in cells]


def _null(c: str) -> str | None:
    c = c.strip()
    return None if c in ("", "%") else c   # some SQL*Plus answer files print NULL as "%"


def parse_answer(path: Path, fmt: str) -> list[list[str | None]]:
    """Parse an official answer file.

    TPC-H files and some TPC-DS files are pipe separated. Most TPC-DS files are SQL*Plus
    output: a header line, a dashed line whose dash groups give the column positions
    (after expanding tabs), records wrapped over several physical lines when they are wide
    (one header/dash pair per physical line), and a "N rows selected." trailer per result
    set (two-statement queries have two result sets).
    """
    lines = [ln.expandtabs(8) for ln in path.read_text(errors="replace").splitlines()]
    rows: list[list[str | None]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or _ROWCOUNT.match(line.strip()) or _NOISE.match(line.strip()):
            i += 1
            continue
        # header line followed by a dash line: SQL*Plus block (possibly several pairs)
        segments: list[list[tuple[int, int]]] = []
        while i + 1 < len(lines) and lines[i].strip() and "|" not in lines[i] \
                and _SEPARATOR.match(lines[i + 1]) and "-" in lines[i + 1]:
            segments.append([(m.start(), m.end()) for m in _DASHES.finditer(lines[i + 1])])
            i += 2
        if segments:
            record: list[str | None] = []
            part = 0
            while i < len(lines) and not _ROWCOUNT.match(lines[i].strip()):
                ln = lines[i]
                i += 1
                if not ln.strip() and part == 0:
                    continue
                record += [_null(c) for c in _fixed_width_cells(ln, segments[part])]
                part += 1
                if part == len(segments):
                    rows.append(record)
                    record, part = [], 0
            continue
        # pipe separated: header line, optional separator, data until a blank/trailer line
        i += 1  # header
        while i < len(lines) and lines[i].strip() and not _ROWCOUNT.match(lines[i].strip()):
            if not _SEPARATOR.match(lines[i]):
                rows.append([_null(c) for c in lines[i].split("|")])
            i += 1
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
