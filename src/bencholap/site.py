"""Static results site (GitHub Pages) built from a directory of run results.

    <results>/runs/<run_id>/result.json      written by `bencholap publish`

`bencholap site build --results <dir> --out <site>` renders:

    index.html                 overview: latest release, release history, recent runs
    runs.html                  every run, filter and sort by performance
    explore.html               every query of every comparison, filter and sort
    runs/<run_id>/index.html   interactive report of one run
    data/runs.json, data/queries.json   the same data for your own analysis

Release history only combines runs from the same machine class (cluster profile and
hardware), benchmark, scale factor and layout, and only the default variant.
"""

from __future__ import annotations

import json
import os
import shutil
from collections import defaultdict
from pathlib import Path

from . import report
from .util import read_json


def _runs(results_dir: Path) -> list[tuple[Path, dict]]:
    out = []
    for p in sorted((results_dir / "runs").glob("*/result.json")):
        try:
            out.append((p, read_json(p)))
        except (OSError, ValueError):
            continue
    out.sort(key=lambda x: x[1]["started_at"], reverse=True)
    return out


def _series(runs: list[tuple[Path, dict]]) -> list[dict]:
    groups: dict[tuple, dict[int, dict]] = defaultdict(dict)
    meta: dict[tuple, dict] = {}
    for _, r in sorted(runs, key=lambda x: x[1]["started_at"]):
        b = r["benchmark"]
        key = (r["machine"]["fingerprint"], b["name"], b["scale_factor"], b["layout"])
        meta[key] = {"machine": r["machine"]["display"], "fingerprint": r["machine"]["fingerprint"],
                     "profile": r["machine"].get("profile"), "benchmark": b["title"],
                     "scale_factor": b["scale_factor"], "layout": b["layout"]}
        for c in r["configurations"]:
            if c.get("start_error") or c.get("variant") != "default":
                continue
            if (c.get("source") or {}).get("kind") != "release" or c.get("version_number") is None:
                continue
            per_q = {}
            for q in r["queries"]:
                if q["config_id"] == c["id"] and q["status"] == "ok" and q["summary"].get("wall_ms"):
                    per_q[q["query"]] = (q["summary"]["wall_ms"]["median"],
                                         (q["summary"].get("total_cpu_ms") or {}).get("median"))
            groups[key][c["version_number"]] = {"run_id": r["run_id"], "q": per_q, "started_at": r["started_at"]}
    series = []
    for key, points in groups.items():
        common = set.intersection(*(set(p["q"]) for p in points.values()))
        rows = []
        for v in sorted(points):
            p = points[v]
            cpu = [p["q"][q][1] for q in common]
            rows.append({"version": v, "run_id": p["run_id"], "started_at": p["started_at"],
                         "total_ms": sum(p["q"][q][0] for q in common),
                         "cpu_ms": sum(cpu) if all(x is not None for x in cpu) else None})
        first = rows[0]["total_ms"] or None
        for row in rows:
            row["vs_first"] = (row["total_ms"] / first) if first else None
        series.append({**meta[key], "points": rows, "common_queries": len(common),
                       "same_run": len({r["run_id"] for r in rows}) == 1})
    series.sort(key=lambda s: (s["benchmark"], float(s["scale_factor"])))
    return series


def _summary(r: dict, a: dict) -> dict:
    rc = r.get("run_config") or {}
    base = a.get("baseline")
    cfgs = []
    for c in a["configs"]:
        t = a["totals"].get(c["id"], {})
        cfgs.append({"id": c["id"], "version": c.get("version"), "spec": c.get("target_spec"),
                     "total_ms": t.get("total_ms"), "cpu_ms": t.get("total_cpu_ms"),
                     "geomean": t.get("geomean_ratio") if c["id"] != base else None,
                     "failed": t.get("error", 0) + t.get("wrong_result", 0)})
    if len(cfgs) < 2:
        main = None
    else:  # sweeps: newest version vs oldest
        main = cfgs[-1] if rc.get("kind") == "sweep" else cfgs[1]
    ch = [x for x in a["changes"] if main and x["config"] == main["id"]]
    return {
        "run_id": r["run_id"], "name": r["name"], "started_at": r["started_at"],
        "kind": rc.get("kind", "manual"), "profile": r["machine"].get("profile") or rc.get("profile"),
        "benchmark": r["benchmark"]["title"], "benchmark_id": r["benchmark"]["name"],
        "scale_factor": r["benchmark"]["scale_factor"], "layout": r["benchmark"]["layout"],
        "machine": r["machine"]["display"], "fingerprint": r["machine"]["fingerprint"],
        "queries": len({q["query"] for q in r["queries"]}), "baseline": base, "configs": cfgs,
        "geomean": main["geomean"] if main else None,
        "improvements": sum(1 for x in ch if x["ratio"] < 1), "regressions": sum(1 for x in ch if x["ratio"] > 1),
        "failed": sum(c["failed"] for c in cfgs),
        "issue": (rc.get("request") or {}).get("issue"), "requested_by": (rc.get("request") or {}).get("requested_by"),
        "duration_seconds": r.get("duration_seconds"),
    }


def _query_rows(r: dict, a: dict) -> list[dict]:
    rows = []
    base = a.get("baseline")
    bcfg = next((c for c in a["configs"] if c["id"] == base), None)
    for row in a["queries"]:
        b = row["cells"].get(base) or {}
        for c in a["configs"]:
            if c["id"] == base:
                continue
            cell = row["cells"].get(c["id"])
            if not cell:
                continue
            rr = cell.get("ratio") or {}
            cr = cell.get("cpu_ratio") or {}
            rows.append({
                "run_id": r["run_id"], "started_at": r["started_at"][:10], "kind": (r.get("run_config") or {}).get("kind", "manual"),
                "benchmark": r["benchmark"]["name"], "sf": r["benchmark"]["scale_factor"],
                "profile": r["machine"].get("profile"), "query": row["query"],
                "baseline": f"{base} ({bcfg.get('version')})" if bcfg else base,
                "target": f"{c['id']} ({c.get('version')})", "status": cell["status"],
                "base_ms": b.get("median_ms"), "ms": cell.get("median_ms"),
                "ratio": rr.get("ratio"), "low": rr.get("low"), "high": rr.get("high"),
                "significant": bool(rr.get("significant")), "cpu_ratio": cr.get("ratio"),
                "input_ratio": cell.get("input_ratio"), "plan_changed": bool(cell.get("plan_changed")),
                "validation": cell.get("validation"),
            })
    return rows


def build(results_dir: Path, out: Path, repo: str | None = None) -> Path:
    repo = repo or os.environ.get("GITHUB_REPOSITORY")
    runs = _runs(results_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    env = report._env()
    summaries, qrows = [], []
    for path, r in runs:
        r = {**r, "comparable": True}
        a = report.analyze(r)
        run_dir = out / "runs" / r["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        if a["configs"]:
            (run_dir / "index.html").write_text(report.html_report(r, a, root="../..", repo=repo))
        shutil.copy(path, run_dir / "result.json")
        summaries.append(_summary(r, a))
        qrows += _query_rows(r, a)
    series = _series(runs)
    latest_release = next((s for s in summaries if s["kind"] == "release"), None)
    (out / "data" / "runs.json").write_text(json.dumps(summaries))
    (out / "data" / "queries.json").write_text(json.dumps(qrows))
    common = {"repo": repo, "root": "."}
    (out / "index.html").write_text(env.get_template("index.html").render(
        page="index", runs=summaries, latest_release=latest_release, series_json=json.dumps(series),
        series=series, stats={"runs": len(summaries), "queries": len(qrows),
                              "releases": len({p["version"] for s in series for p in s["points"]})}, **common))
    (out / "runs.html").write_text(env.get_template("runs.html").render(
        page="runs", runs_json=json.dumps(summaries), **common))
    (out / "explore.html").write_text(env.get_template("explore.html").render(
        page="explore", rows_json=json.dumps(qrows), **common))
    (out / ".nojekyll").write_text("")
    return out
