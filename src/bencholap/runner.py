"""Execute a run: every target x variant against one dataset, with warmup, repetitions and
rounds, collecting timings, engine metrics, plans and validation into one results file."""

from __future__ import annotations

import re
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import __version__, benchmarks, dataset, machine, stack, validate
from .engines import get as get_engine
from .engines.base import ResolvedTarget
from .plans import plan_hash
from .runconfig import RunConfig, merged_overrides
from .stats import summarize
from .util import PACKAGE_DIR, log, run, sha256_text, stable_hash, write_json

RESULTS_SCHEMA_VERSION = 1
RESULT_ROWS_KEPT = 1000



def _harness_info() -> dict:
    out = run(["git", "-C", str(PACKAGE_DIR), "rev-parse", "HEAD"], capture=True, check=False)
    dirty = run(["git", "-C", str(PACKAGE_DIR), "status", "--porcelain"], capture=True, check=False)
    return {"version": __version__, "commit": (out.stdout or "").strip() or None,
            "dirty": bool((dirty.stdout or "").strip())}


def _sum_stats(parts: list[dict]) -> dict:
    out: dict[str, Any] = {}
    for p in parts:
        for k, v in p.items():
            if isinstance(v, (int, float)):
                out[k] = out.get(k, 0) + v
            elif k == "inputs":
                out.setdefault("inputs", []).extend(v)
    return out


@dataclass
class QueryRecord:
    config_id: str
    query: str
    sql: str
    override: dict | None
    executions: list[dict] = field(default_factory=list)
    status: str = "ok"
    error: str | None = None
    validation: dict | None = None
    result: dict | None = None
    plan: dict | None = None

    def as_dict(self) -> dict:
        measured = [e for e in self.executions if not e["warmup"] and e.get("ok")]
        summary = {"wall_ms": summarize([e["wall_ms"] for e in measured])}
        # every numeric engine statistic gets a summary, so any metric can be compared
        keys = sorted({k for e in measured for k, v in e["stats"].items() if isinstance(v, (int, float))})
        for m in keys:
            s = summarize([e["stats"][m] for e in measured if isinstance(e["stats"].get(m), (int, float))])
            if s:
                summary[m] = s
        return {
            "config_id": self.config_id, "query": self.query, "status": self.status, "error": self.error,
            "sql_sha256": sha256_text(self.sql)[:16], "sql": self.sql, "override": self.override,
            "validation": self.validation, "result": self.result, "plan": self.plan,
            "summary": summary, "executions": self.executions,
        }


# Errors that only mean "the cluster is still settling" (seen right after startup on some
# versions); the statement is retried and the attempt is not measured.
TRANSIENT_ERRORS = ("NO_NODES_AVAILABLE",)


def _execute_statement(session, stmt: str):
    for attempt in range(6):
        try:
            return session.execute(stmt)
        except Exception as e:
            if attempt == 5 or not any(t in str(e) for t in TRANSIENT_ERRORS):
                raise
            log.info("transient error (%s), retrying", str(e)[:120])
            time.sleep(5)


def _execute_query(session, q: benchmarks.Query) -> tuple[float, dict, list[list[tuple]], list[str]]:
    wall, stats, result_sets, ids = 0.0, [], [], []
    for stmt in q.statements:
        r = _execute_statement(session, stmt)
        wall += r.wall_ms
        stats.append(r.engine_stats)
        if r.query_id:
            ids.append(r.query_id)
        if r.columns and re.match(r"^\s*(with|select|\()", stmt, re.IGNORECASE):
            result_sets.append(r.rows or [])
    return wall, _sum_stats(stats), result_sets, ids


def _capture_plan(session, q: benchmarks.Query) -> dict | None:
    texts = []
    for stmt in q.statements:
        if re.match(r"^\s*(with|select|\()", stmt, re.IGNORECASE):
            texts.append(session.explain(stmt) or "")
        else:
            session.execute(stmt, fetch=False)  # e.g. CREATE VIEW in TPC-H Q15
    if not texts:
        return None
    text = "\n\n".join(texts)
    return {"hash": plan_hash(text), "text": text}


def _dataset_summary(manifest: dict) -> dict:
    return dict(manifest)  # includes SHOW CREATE TABLE per table, so the applied layout is visible


def run_benchmark(cfg: RunConfig, output_dir: Path) -> Path:
    bench = benchmarks.load(cfg.benchmark)
    manifests = {}
    for lay in cfg.layouts:
        ds = dataset.DatasetId(bench.name, cfg.scale_factor, lay)
        manifests[lay] = dataset.get_manifest(ds)
        if not manifests[lay]:
            raise RuntimeError(f"dataset {ds.key} is not built; run `bencholap dataset build --benchmark "
                               f"{bench.name} --sf {cfg.scale_factor} --layout {lay}` first")
    stack.ensure_up()

    started = time.time()
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(started)) + "-" + stable_hash(cfg.raw, 6)
    resolved: dict[str, ResolvedTarget] = {}
    for t in cfg.targets:
        log.info("resolving target %s = %s", t.name, t.source)
        resolved[t.name] = get_engine(t.engine).resolve(t.source)

    configurations: dict[str, dict] = {}
    records: dict[tuple[str, str], QueryRecord] = {}
    timeout_session = {"query_max_execution_time": cfg.timeout}

    multi_layout = len(cfg.layouts) > 1
    for rnd in range(cfg.rounds):
        for (t, v), lay in ((tv, lay) for tv in cfg.configurations() for lay in cfg.layouts):
            manifest = manifests[lay]
            config_id = f"{t.name}/{v.name}" + (f"/{lay}" if multi_layout else "")
            target = resolved[t.name]
            ov = merged_overrides(t, v)
            engine = get_engine(t.engine)
            log.info("round %d/%d: %s (%s %s)", rnd + 1, cfg.rounds, config_id, t.engine, target.version)
            try:
                running = engine.start(target, ov.as_dict(), cfg.resources, label=config_id,
                                       cluster=t.cluster or cfg.cluster)
            except Exception as e:  # noqa: BLE001
                log.error("could not start %s: %s", config_id, e)
                configurations.setdefault(config_id, {"id": config_id, "target": t.name, "variant": v.name,
                                                      "layout": lay, "start_error": str(e)[:2000]})
                continue
            configurations[config_id] = {
                "id": config_id, "target": t.name, "variant": v.name, "layout": lay, "engine": t.engine,
                "target_spec": t.source, "version": target.version, "version_number": target.version_number,
                "image": target.image, "source": target.source,
                "variant_description": v.description, "overrides": ov.as_dict(),
                "session": {**timeout_session, **ov.session},
                "effective_config": running.effective_config,
            }
            session = running.session(manifest["schema"], {**timeout_session, **ov.session})
            try:
                for qid in cfg.queries:
                    q = bench.query(qid, cfg.scale_factor, t.engine)
                    rec = records.setdefault((config_id, qid), QueryRecord(config_id, qid, q.sql, q.override))
                    if rec.status == "error":
                        continue
                    if cfg.capture_plans and rec.plan is None:
                        try:
                            rec.plan = _capture_plan(session, q)
                        except Exception as e:  # noqa: BLE001
                            rec.plan = {"error": str(e)[:1000]}
                    for i in range(cfg.warmup + cfg.repetitions):
                        warm = i < cfg.warmup
                        try:
                            wall, stats, result_sets, ids = _execute_query(session, q)
                        except Exception as e:  # noqa: BLE001
                            rec.status, rec.error = "error", str(e)[:2000]
                            rec.executions.append({"round": rnd, "rep": i, "warmup": warm, "ok": False})
                            log.warning("%s %s failed: %s", config_id, qid, str(e)[:300])
                            break
                        rec.executions.append({"round": rnd, "rep": i, "warmup": warm, "ok": True,
                                               "wall_ms": round(wall, 3), "query_ids": ids, "stats": stats})
                        if rec.validation is None:
                            rows = [r for rs in result_sets for r in rs]
                            rec.result = {"rows": len(rows), "fingerprint": validate.fingerprint(rows),
                                          "sample": [[validate.norm_cell(c) for c in r] for r in rows[:3]]}
                            if len(rows) <= RESULT_ROWS_KEPT:  # full result for diagnosing mismatches
                                rec.result["data"] = [[validate.norm_cell(c) for c in r] for r in rows]
                            rec.validation = validate.validate(bench, qid, cfg.scale_factor, result_sets)
                            if rec.validation["status"] == "mismatch":
                                rec.status = "wrong_result"
                    log.info("  %s %s %s", qid, rec.status,
                             f"{rec.executions[-1].get('wall_ms', 0):.0f} ms" if rec.executions else "")
            except Exception:  # noqa: BLE001
                log.error("run of %s aborted:\n%s", config_id, traceback.format_exc())
            finally:
                session.close()
                running.stop()

    profile = None
    if cfg.profile_mode:
        # after every measurement, on fresh clusters, so the timings above are unaffected
        from .profiling import run_profile_pass

        profile = run_profile_pass(cfg, bench, resolved, manifests, output_dir / run_id)

    results = {
        "schema_version": RESULTS_SCHEMA_VERSION,
        "run_id": run_id,
        "name": cfg.name,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "duration_seconds": round(time.time() - started, 1),
        "harness": _harness_info(),
        "machine": machine.describe(topology={
            "profile": cfg.raw.get("profile"),
            "cluster": {k: v for k, v in cfg.cluster.items() if k not in ("deploy", "teardown", "url")},
            "resources": cfg.resources}),
        "benchmark": {"name": bench.name, "title": bench.title, "scale_factor": cfg.scale_factor,
                      "layout": ", ".join(cfg.layouts), "layouts": cfg.layouts},
        "dataset": _dataset_summary(manifests[cfg.layouts[0]]),
        "datasets": {lay: _dataset_summary(m) for lay, m in manifests.items()},
        "settings": {"warmup": cfg.warmup, "repetitions": cfg.repetitions, "rounds": cfg.rounds,
                     "timeout": cfg.timeout, "resources": cfg.resources, "cluster": cfg.cluster,
                     "queries": cfg.queries, "match": cfg.raw.get("match")},
        "run_config": cfg.raw,
        "configurations": list(configurations.values()),
        "queries": [r.as_dict() for r in records.values()],
    }
    if profile is not None:
        results["profile"] = profile
    out = output_dir / run_id / "result.json"
    write_json(out, results)
    if profile is not None:
        from .profiling import write_markdown

        try:
            log.info("profile summary written to %s", write_markdown(results, out.parent))
        except Exception:  # noqa: BLE001 - profiling never fails the run
            log.error("profile summary failed:\n%s", traceback.format_exc())
    log.info("results written to %s", out)
    return out
