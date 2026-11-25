#!/usr/bin/env python3
"""Render the TPC-DS qualification queries from the kit's query templates and the
qualification substitution parameters published in the TPC-DS specification (Appendix B).

dsqgen's -qualify flag only changes the query order; it still draws random substitution
values. The official answer sets correspond to the qualification parameters, so we
substitute them ourselves:

  * define lines and comments are dropped from the template
  * [NAME] / [NAME.k] tokens are replaced with the Appendix B values
  * [_LIMITA]/[_LIMITB] are removed, [_LIMITC] becomes "limit <_LIMIT>"

Every token in a template body must be covered by the spec, otherwise the script fails.

Usage: tpcds_qualification.py <spec.txt (pdftotext -layout)> <templates dir> <out dir>
"""

import re
import sys
from pathlib import Path

SECTION = re.compile(r"^\s*B\.(\d+)\s+query(\d+)\.tpl\b.*$")
FOOTER = re.compile(r"TPC Benchmark.*Standard Specification|Page \d+ of \d+")
ASSIGN = re.compile(r"([A-Z][A-Z0-9_]*)(?:\.(\d+))?\s*=\s*")


def parse_spec(text: str) -> dict[int, dict[str, dict[int, str]]]:
    params: dict[int, dict[str, dict[int, str]]] = {}
    current = None
    in_params = False
    for line in text.splitlines():
        m = SECTION.match(line)
        if m:
            current = int(m.group(2))
            params[current] = {}
            in_params = False
            continue
        if current is None:
            continue
        if line.strip().startswith("Appendix C") or re.match(r"^\s*Appendix C", line):
            break
        if "Qualification Substitution Parameters" in line:
            in_params = True
            continue
        if not in_params or FOOTER.search(line):
            continue
        body = line.replace("•", " ").strip()
        if not body:
            continue
        matches = list(ASSIGN.finditer(body))
        if not matches:
            continue
        for i, a in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            value = body[a.end():end].strip()
            idx = int(a.group(2)) if a.group(2) else 1
            params[current].setdefault(a.group(1), {})[idx] = value
    return params


TOKEN = re.compile(r"\[([A-Za-z_][A-Za-z0-9_]*)(?:\.(\d+))?\]")


def render(template: str, qparams: dict[str, dict[int, str]], qnum: int) -> str:
    limit = None
    body_lines = []
    pending = None  # multi-line define being skipped
    for line in template.splitlines():
        s = line.strip()
        if pending is not None:
            pending += " " + s
            if s.endswith(";"):
                pending = None
            continue
        if s.startswith("--"):
            continue
        if re.match(r"^define\b", s, re.IGNORECASE):
            m = re.match(r"^define\s+_LIMIT\s*=\s*(\d+)\s*;", s, re.IGNORECASE)
            if m:
                limit = int(m.group(1))
            if not s.endswith(";"):
                pending = s
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip()
    missing = set()

    def sub(m: re.Match) -> str:
        name, idx = m.group(1), int(m.group(2)) if m.group(2) else 1
        if name == "_LIMITA" or name == "_LIMITB":
            return ""
        if name == "_LIMITC":
            return f"limit {limit}" if limit else ""
        if name in ("_BEGIN", "_END"):
            return ""
        vals = qparams.get(name)
        if not vals or idx not in vals:
            missing.add(f"{name}.{idx}")
            return m.group(0)
        return vals[idx]

    out = TOKEN.sub(sub, body)
    if missing:
        raise SystemExit(f"query{qnum}.tpl: no qualification value for {sorted(missing)}")
    # dsqgen puts the "select" of [_LIMITA] select [_LIMITB] on one line: tidy leading spaces
    return re.sub(r"[ \t]+\n", "\n", out).strip() + "\n"


def main(spec_txt: Path, templates: Path, out: Path) -> None:
    params = parse_spec(spec_txt.read_text())
    if len(params) != 99:
        raise SystemExit(f"expected 99 queries in Appendix B, found {len(params)}")
    out.mkdir(parents=True, exist_ok=True)
    for q in range(1, 100):
        tpl = (templates / f"query{q}.tpl").read_text()
        (out / f"q{q:02d}.sql").write_text(render(tpl, params[q], q))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
