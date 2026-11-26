"""Turn result files into comparisons, a Markdown summary and a self-contained HTML report."""

from __future__ import annotations

import html
import json
import statistics
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .. import stats
from ..plans import query_plan_hash
from ..util import read_json

TEMPLATES = Path(__file__).with_name("templates")
SIGNIFICANT_CHANGE = 0.05   # report changes of at least 5% whose CI excludes "no change"
MAX_LISTED = 15             # rows per list in the Markdown summary (issue comments stay readable)


def load_results(paths: list[Path]) -> dict:
    """Load one result file, or merge several into one view (configurations are prefixed
    with their run id). Timings from different machines are flagged as not comparable."""
    results = [read_json(Path(p)) for p in paths]
    if len(results) == 1:
        r = results[0]
        r["comparable"] = True
        return r
    merged = dict(results[0])
    merged["name"] = " + ".join(r["name"] for r in results)
    merged["run_id"] = "+".join(r["run_id"] for r in results)
    merged["configurations"], merged["queries"] = [], []
    for r in results:
        prefix = r["run_id"].split("-")[0] + ":"
        for c in r["configurations"]:
            merged["configurations"].append({**c, "id": prefix + c["id"], "run_id": r["run_id"]})
        for q in r["queries"]:
            merged["queries"].append({**q, "config_id": prefix + q["config_id"]})
    merged["comparable"] = len({r["machine"]["fingerprint"] for r in results}) == 1 and len(
        {(r["benchmark"]["name"], r["benchmark"]["scale_factor"], r["benchmark"]["layout"]) for r in results}) == 1
    merged["machines"] = [r["machine"] for r in results]
    return merged


def _measured(q: dict, metric: str) -> list[float]:
    out = []
    for e in q.get("executions", []):
        if e.get("warmup") or not e.get("ok"):
            continue
        v = e["wall_ms"] if metric == "wall_ms" else e.get("stats", {}).get(metric)
        if v is not None:
            out.append(v)
    return out


def _median(q: dict | None, metric: str) -> float | None:
    if not q:
        return None
    s = q.get("summary", {}).get(metric)
    return s["median"] if s else None


def analyze(result: dict, baseline: str | None = None) -> dict:
    configs = [c for c in result["configurations"] if "start_error" not in c]
    failed_configs = [c for c in result["configurations"] if "start_error" in c]
    if not configs:
        return {"configs": [], "failed_configs": failed_configs, "queries": [], "totals": {}, "changes": []}
    base = baseline or configs[0]["id"]
    by = {(q["config_id"], q["query"]): q for q in result["queries"]}
    qids = list(dict.fromkeys(q["query"] for q in result["queries"]))
    rows, changes = [], []
    all_ok = []
    for qid in qids:
        cells = {}
        bq = by.get((base, qid))
        for c in configs:
            q = by.get((c["id"], qid))
            if not q:
                cells[c["id"]] = None
                continue
            cell = {
                "status": q["status"], "error": q.get("error"),
                "validation": (q.get("validation") or {}).get("status"),
                "median_ms": _median(q, "wall_ms"),
                "cv": (q["summary"].get("wall_ms") or {}).get("cv"),
                "cpu_ms": _median(q, "total_cpu_ms"),
                "input_bytes": _median(q, "physical_input_bytes"),
                "input_rows": _median(q, "physical_input_positions"),
                "peak_mem": _median(q, "peak_user_memory_reservation_bytes"),
                "plan_hash": query_plan_hash(q),
                "fingerprint": (q.get("result") or {}).get("fingerprint"),
                "override": q.get("override"),
            }
            if c["id"] != base and bq and q["status"] == "ok" and bq["status"] == "ok":
                cell["ratio"] = stats.ratio_ci(_measured(bq, "wall_ms"), _measured(q, "wall_ms"))
                cell["cpu_ratio"] = stats.ratio_ci(_measured(bq, "total_cpu_ms"), _measured(q, "total_cpu_ms"))
                bi, hi = _median(bq, "physical_input_bytes"), cell["input_bytes"]
                cell["input_ratio"] = (hi / bi) if bi and hi is not None else None
                bp = query_plan_hash(bq)
                cell["plan_changed"] = bool(bp and cell["plan_hash"] and bp != cell["plan_hash"])
                r = cell["ratio"]
                if r and r["significant"] and abs(r["ratio"] - 1) >= SIGNIFICANT_CHANGE:
                    changes.append({"query": qid, "config": c["id"], "ratio": r["ratio"], "low": r["low"],
                                    "high": r["high"], "plan_changed": cell["plan_changed"]})
            cells[c["id"]] = cell
        fps = {v["fingerprint"] for v in cells.values() if v and v.get("fingerprint") and v["status"] == "ok"}
        ok_everywhere = all(v and v["status"] == "ok" for v in cells.values())
        if ok_everywhere:
            all_ok.append(qid)
        rows.append({"query": qid, "cells": cells, "results_differ": len(fps) > 1, "ok_everywhere": ok_everywhere})

    totals = {}
    for c in configs:
        cid = c["id"]
        medians = [r["cells"][cid]["median_ms"] for r in rows if r["query"] in all_ok]
        ratios = [r["cells"][cid]["ratio"]["ratio"] for r in rows
                  if r["query"] in all_ok and r["cells"][cid] and r["cells"][cid].get("ratio")]
        statuses = [r["cells"][cid]["status"] for r in rows if r["cells"][cid]]
        validations = [r["cells"][cid]["validation"] for r in rows if r["cells"][cid]]
        totals[cid] = {
            "total_ms": sum(m for m in medians if m is not None),
            "total_cpu_ms": sum(r["cells"][cid]["cpu_ms"] or 0 for r in rows if r["query"] in all_ok),
            "total_input_bytes": sum(r["cells"][cid]["input_bytes"] or 0 for r in rows if r["query"] in all_ok),
            "geomean_ratio": stats.geomean(ratios) if cid != base else 1.0,
            "ok": statuses.count("ok"), "error": statuses.count("error"),
            "wrong_result": statuses.count("wrong_result"),
            "validated": validations.count("match"),
            "no_reference": validations.count("no-reference"),
        }
    changes.sort(key=lambda x: x["ratio"])
    return {"configs": configs, "failed_configs": failed_configs, "baseline": base, "queries": rows,
            "totals": totals, "changes": changes, "common_queries": len(all_ok),
            "config_diff": config_diff(configs)}


def _flatten(d: Any, prefix: str = "") -> dict[str, str]:
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flatten(v, f"{prefix}{k}" if not prefix else f"{prefix} / {k}"))
    elif isinstance(d, list):
        out[prefix] = ", ".join(map(str, d))
    else:
        out[prefix] = str(d)
    return out


def _jvm_options(lines: list[str]) -> dict[str, str]:
    out = {}
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        key, sep, val = ln.partition("=")
        out[key] = val if sep else "set"
    return out


def config_diff(configs: list[dict]) -> list[dict]:
    """Effective settings that differ between configurations (catalog, config.properties,
    JVM, session). Shows exactly what changed between versions and variants."""
    flat = {c["id"]: _flatten({"catalog": c.get("effective_config", {}).get("catalogs", {}),
                               "config.properties": c.get("effective_config", {}).get("config.properties", {}),
                               "session": c.get("session", {}),
                               "jvm.config": _jvm_options(c.get("effective_config", {}).get("jvm.config", []))})
            for c in configs}
    keys = sorted({k for f in flat.values() for k in f})
    rows = []
    for k in keys:
        vals = {cid: f.get(k) for cid, f in flat.items()}
        if len(set(vals.values())) > 1:
            rows.append({"key": k, "values": vals})
    return rows


def fmt_ms(v: float | None) -> str:
    if v is None:
        return "–"
    return f"{v / 1000:.2f} s" if v >= 1000 else f"{v:.0f} ms"


def fmt_bytes(v: float | None) -> str:
    if v is None:
        return "–"
    for unit, size in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if v >= size:
            return f"{v / size:.1f} {unit}"
    return f"{v:.0f} B"


def fmt_ratio(r: dict | None) -> str:
    if not r:
        return "–"
    pct = (r["ratio"] - 1) * 100
    s = f"{pct:+.1f}%"
    if r.get("low") is not None:
        s += f" [{(r['low'] - 1) * 100:+.0f}%, {(r['high'] - 1) * 100:+.0f}%]"
    return s


def _label(c: dict) -> str:
    return c["id"] + (f" ({c['version']})" if c.get("version") else "")


def markdown(result: dict, a: dict) -> str:
    b = result["benchmark"]
    lines = [f"## bencholap: {result['name']}", "",
             (f"{b['title']} SF{b['scale_factor']}, layout `{b['layout']}`, "
             f"{result['settings']['repetitions']} measured runs per query "
             f"({result['settings']['warmup']} warmup, {result['settings']['rounds']} round(s)). "
             f"Machine: {result['machine']['display']}."), ""]
    if not result.get("comparable", True):
        lines += [("> **Warning:** these results come from different machines or datasets; "
                  "timings are not comparable."), ""]
    lines += ["| configuration | target | total (common queries) | vs baseline (geomean) | CPU | ok | errors | wrong results | validated |",
              "|---|---|---|---|---|---|---|---|---|"]
    for c in a["configs"]:
        t = a["totals"][c["id"]]
        g = t["geomean_ratio"]
        lines.append(f"| {_label(c)} | `{c['target_spec']}` | {fmt_ms(t['total_ms'])} | "
                     f"{'baseline' if c['id'] == a['baseline'] else (f'{(g - 1) * 100:+.1f}%' if g else '–')} | "
                     f"{fmt_ms(t['total_cpu_ms'])} | {t['ok']} | {t['error']} | {t['wrong_result']} | {t['validated']} |")
    for c in a["failed_configs"]:
        lines.append(f"| {c['id']} | – | failed to start | | | | | | |")
    lines.append("")
    if a["changes"]:
        lines += [f"**Significant changes** (≥{SIGNIFICANT_CHANGE:.0%}, 95% CI excludes no change; negative = faster):", "",
                  "| query | configuration | change [95% CI] | plan changed |", "|---|---|---|---|"]
        shown = sorted(a["changes"], key=lambda c: -abs(c["ratio"] - 1))[:MAX_LISTED]
        for ch in sorted(shown, key=lambda c: c["ratio"]):
            lines.append(f"| {ch['query']} | {ch['config']} | {fmt_ratio(ch)} | {'yes' if ch['plan_changed'] else ''} |")
        if len(a["changes"]) > MAX_LISTED:
            better = sum(1 for c in a["changes"] if c["ratio"] < 1)
            lines.append(f"\n{len(a['changes'])} significant changes in total ({better} faster, "
                         f"{len(a['changes']) - better} slower); the {MAX_LISTED} largest are listed, all are in the report.")
        lines.append("")
    else:
        lines += ["No significant per-query timing changes.", ""]
    problems = [(r["query"], cid, c) for r in a["queries"] for cid, c in r["cells"].items()
                if c and c["status"] != "ok"]
    if problems:
        lines += ["**Failures:**", ""]
        lines += [f"- {q} on {cid}: {c['status']} {(c.get('error') or '')[:200]}" for q, cid, c in problems[:MAX_LISTED]]
        if len(problems) > MAX_LISTED:
            lines.append(f"- … {len(problems) - MAX_LISTED} more in the report")
        lines.append("")
    differ = [r["query"] for r in a["queries"] if r["results_differ"]]
    if differ:
        lines += [f"**Result sets differ between configurations:** {', '.join(differ)}", ""]
    if a["config_diff"]:
        lines += ["<details><summary>Settings that differ between configurations</summary>", "",
                  "| setting | " + " | ".join(c["id"] for c in a["configs"]) + " |",
                  "|---|" + "---|" * len(a["configs"])]
        for row in a["config_diff"][:60]:
            lines.append(f"| `{row['key']}` | " + " | ".join(
                html.escape(row["values"].get(c["id"]) or "–") for c in a["configs"]) + " |")
        lines += ["", "</details>", ""]
    lines.append("_Results are derived from TPC benchmarks and are not comparable to published TPC results._")
    return "\n".join(lines) + "\n"


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.filters.update(ms=fmt_ms, bytes=fmt_bytes, ratio=fmt_ratio)
    env.globals.update(label=_label)
    return env


def html_report(result: dict, a: dict, root: str | None = None, repo: str | None = None) -> str:
    data = payload(result, a)
    return _env().get_template("run.html").render(
        r=result, a=a, root=root, repo=repo, page="run", markdown=markdown(result, a),
        data_json=json.dumps(data, separators=(",", ":"), default=str).replace("</", "<\\/"))


# Metrics offered in the report's metric selector: key, label, kind (time|bytes|count).
METRICS = [
    ("wall_ms", "Wall time", "time"),
    ("total_cpu_ms", "CPU time", "time"),
    ("total_scheduled_ms", "Scheduled time", "time"),
    ("elapsed_ms", "Elapsed (engine)", "time"),
    ("planning_ms", "Planning time", "time"),
    ("analysis_ms", "Analysis time", "time"),
    ("execution_ms", "Execution time", "time"),
    ("queued_ms", "Queued time", "time"),
    ("total_blocked_ms", "Blocked time", "time"),
    ("physical_input_read_ms", "Input read time", "time"),
    ("physical_input_bytes", "Physical input", "bytes"),
    ("physical_input_positions", "Input rows", "count"),
    ("processed_input_bytes", "Processed input", "bytes"),
    ("processed_input_positions", "Processed rows", "count"),
    ("internal_network_input_bytes", "Exchange data", "bytes"),
    ("peak_user_memory_reservation_bytes", "Peak user memory", "bytes"),
    ("peak_total_memory_reservation_bytes", "Peak total memory", "bytes"),
    ("spilled_bytes", "Spilled", "bytes"),
    ("output_positions", "Output rows", "count"),
    ("total_drivers", "Drivers", "count"),
]
BOOTSTRAP_METRICS = {"wall_ms", "total_cpu_ms", "total_scheduled_ms", "elapsed_ms"}


def payload(result: dict, a: dict) -> dict:
    """Everything the interactive report needs, as plain JSON."""
    configs = a["configs"]
    base = a["baseline"]
    by = {(q["config_id"], q["query"]): q for q in result["queries"]}
    present = {m for q in result["queries"] for m in (q.get("summary") or {})}
    metrics = [{"key": k, "label": lbl, "kind": kind} for k, lbl, kind in METRICS if k in present]
    queries = []
    for row in a["queries"]:
        qid = row["query"]
        bq = by.get((base, qid))
        cells = {}
        for c in configs:
            q = by.get((c["id"], qid))
            if not q:
                continue
            values = {}
            for m in metrics:
                s = (q.get("summary") or {}).get(m["key"])
                if s:
                    values[m["key"]] = {"median": s["median"], "min": s["min"], "max": s["max"],
                                        "cv": s.get("cv"), "runs": _measured(q, m["key"])}
            ratios = {}
            if c["id"] != base and bq and bq["status"] == "ok" and q["status"] == "ok":
                for m in metrics:
                    b, h = _measured(bq, m["key"]), _measured(q, m["key"])
                    if not b or not h:
                        continue
                    if m["key"] in BOOTSTRAP_METRICS:
                        ratios[m["key"]] = stats.ratio_ci(b, h)
                    else:
                        mb = statistics.median(b)
                        if mb:
                            ratios[m["key"]] = {"ratio": statistics.median(h) / mb, "low": None, "high": None,
                                                "significant": False}
            cell = row["cells"].get(c["id"]) or {}
            cells[c["id"]] = {
                "status": q["status"], "error": q.get("error"),
                "validation": (q.get("validation") or {}).get("status"),
                "validation_detail": (q.get("validation") or {}).get("detail"),
                "override": (q.get("override") or {}).get("reason"),
                "plan_hash": query_plan_hash(q),
                "plan_changed": cell.get("plan_changed", False),
                "rows": (q.get("result") or {}).get("rows"),
                "values": values, "ratios": ratios,
            }
        sql = next((q.get("sql") for q in result["queries"] if q["query"] == qid and q.get("sql")), None)
        queries.append({"q": qid, "cells": cells, "results_differ": row["results_differ"],
                        "ok_everywhere": row["ok_everywhere"], "sql": sql})
    plans = {}
    for q in result["queries"]:
        text = (q.get("plan") or {}).get("text")
        if text:
            plans.setdefault(q["query"], {})[q["config_id"]] = text
    common = [r["q"] for r in queries if r["ok_everywhere"]]
    totals = {}
    for c in configs:
        t = {}
        for m in metrics:
            vals = [r["cells"][c["id"]]["values"].get(m["key"], {}).get("median") for r in queries
                    if r["q"] in common and c["id"] in r["cells"]]
            if vals and all(v is not None for v in vals):
                t[m["key"]] = sum(vals)
        totals[c["id"]] = {"metrics": t, **{k: v for k, v in a["totals"][c["id"]].items()}}
    b = result["benchmark"]
    return {
        "meta": {"name": result["name"], "run_id": result["run_id"], "benchmark": b["title"],
                 "benchmark_id": b["name"], "scale_factor": b["scale_factor"], "layout": b["layout"],
                 "started_at": result["started_at"], "duration_seconds": result.get("duration_seconds"),
                 "machine": result["machine"].get("display"), "fingerprint": result["machine"].get("fingerprint"),
                 "settings": result.get("settings"), "comparable": result.get("comparable", True),
                 "description": (result.get("run_config") or {}).get("description"),
                 "request": (result.get("run_config") or {}).get("request"),
                 "kind": (result.get("run_config") or {}).get("kind", "manual"),
                 "profile": (result.get("run_config") or {}).get("profile")},
        "baseline": base,
        "configs": [{"id": c["id"], "target": c["target"], "variant": c["variant"], "version": c.get("version"),
                     "spec": c.get("target_spec"), "image": c.get("image"),
                     "commit": (c.get("source") or {}).get("commit"),
                     "pr": (c.get("source") or {}).get("pull_request"),
                     "variant_description": c.get("variant_description")} for c in configs],
        "failed_configs": [{"id": c["id"], "error": c.get("start_error")} for c in a["failed_configs"]],
        "metrics": metrics,
        "queries": queries,
        "plans": plans,
        "common_queries": common,
        "totals": totals,
        "changes": a["changes"],
        "config_diff": a["config_diff"],
        "significant_change": SIGNIFICANT_CHANGE,
    }


def write_report(result_paths: list[Path], out_html: Path | None = None, out_md: Path | None = None,
                 baseline: str | None = None) -> dict:
    result = load_results(result_paths)
    a = analyze(result, baseline)
    if out_html:
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(html_report(result, a))
    if out_md:
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(markdown(result, a))
    return a
