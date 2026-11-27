"""Profile mode: one more pass per configuration after the timed measurements, so timings are
unaffected, recording where the time and memory go.

Per configuration a fresh cluster (with an extra `jmx` catalog) runs every query three times:

1. warmup, not recorded (JIT and caches, like the measured runs' warmup);
2. with async-profiler in CPU mode, recording per query the operator summary (query info),
   GC, allocation and S3 request deltas (JMX, summed over nodes), wall and CPU time;
3. with async-profiler in allocation mode.

Output: results/<run>/profiles/<configuration>/{cpu,alloc}.collapsed (merged over nodes) and
flame graphs (one per node), a `profile` section in result.json and results/<run>/profile.md.
A failure of any part is recorded and never fails the run.
"""

from __future__ import annotations

import re
import time
import traceback
from pathlib import Path
from typing import Any

from . import benchmarks
from .engines import get as get_engine
from .engines.trino import extract_stats
from .engines.trino.profiler import AsyncProfiler, JmxCounters, operator_summary
from .runconfig import RunConfig, merged_overrides
from .util import log

TOP_FRAMES = 30
_JAVA_FRAME = re.compile(r"_\[[ji01]\]$")   # async-profiler annotations (-a): compiled, inlined, interpreted, C1
_ANNOTATION = re.compile(r"_\[[a-z0-9]+\]$")


def _dirname(config_id: str) -> str:
    return "/".join(re.sub(r"[^A-Za-z0-9._-]+", "_", p) for p in config_id.split("/"))


def _profile_queries(session, bench, cfg: RunConfig, engine: str, counters, record: bool) -> dict[str, dict]:
    out: dict[str, dict] = {}
    before = counters.snapshot() if counters and record else {}
    for qid in cfg.queries:
        q = bench.query(qid, cfg.scale_factor, engine)
        t0 = time.perf_counter()
        infos, error = [], None
        try:
            for stmt in q.statements:
                session.execute(stmt, fetch=False)
                infos.append(getattr(session, "last_info", {}) or {})
        except Exception as e:  # noqa: BLE001
            error = str(e)[:500]
        if not record:
            continue
        wall = (time.perf_counter() - t0) * 1000
        rec: dict[str, Any] = {"wall_ms": round(wall, 1), "query_ids": [i.get("queryId") for i in infos]}
        if error:
            rec["error"] = error
        stats = [extract_stats(i) for i in infos]
        for k in ("total_cpu_ms", "total_blocked_ms", "physical_input_bytes", "peak_user_memory_reservation_bytes"):
            vals = [s[k] for s in stats if isinstance(s.get(k), (int, float))]
            if vals:
                rec[k] = round(sum(vals), 1)
        rec["operators"] = operator_summary(infos)
        if counters:
            after = counters.snapshot()
            rec["counters"] = counters.delta(before, after)
            before = after
        out[qid] = rec
    return out


def _profile_configuration(cfg: RunConfig, bench, t, v, manifest, target, label: str, dest: Path) -> dict:
    engine = get_engine(t.engine)
    ov = merged_overrides(t, v)
    session_props = {"query_max_execution_time": cfg.timeout, **ov.session}
    res: dict[str, Any] = {"errors": []}
    running = engine.start(target, ov.as_dict(), cfg.resources, catalogs=("iceberg", "jmx"),
                           label=label, cluster=t.cluster or cfg.cluster)
    session = running.session(manifest["schema"], session_props)
    profiler = None
    try:
        try:
            counters = JmxCounters(session)
            res["jmx_tables"] = counters.tables
        except Exception as e:  # noqa: BLE001
            counters = None
            res["errors"].append(f"jmx: {str(e)[:300]}")
        _profile_queries(session, bench, cfg, t.engine, None, record=False)
        try:
            profiler = AsyncProfiler(running.containers) if running.containers else None
        except Exception as e:  # noqa: BLE001
            res["errors"].append(f"async-profiler: {str(e)[:300]}")
        files: list[Path] = []
        for mode in ("cpu", "alloc"):
            started = False
            if profiler:
                try:
                    res[f"{mode}_event"] = profiler.start(mode)
                    started = True
                except Exception as e:  # noqa: BLE001
                    res["errors"].append(f"async-profiler {mode}: {str(e)[:300]}")
            t0 = time.perf_counter()
            queries = _profile_queries(session, bench, cfg, t.engine, counters, record=mode == "cpu")
            res[f"{mode}_pass_seconds"] = round(time.perf_counter() - t0, 1)
            if mode == "cpu":
                res["queries"] = queries
            if started:
                files += profiler.stop(dest, mode)
        if counters and counters.errors:
            res["errors"] += counters.errors
        res["files"] = [f.name for f in files]
    finally:
        if profiler:
            profiler.close()
        session.close()
        running.stop()
    return res


def run_profile_pass(cfg: RunConfig, bench: benchmarks.Benchmark, resolved: dict, manifests: dict,
                     run_dir: Path) -> dict:
    """Profile every configuration; returns {config_id: profile}."""
    out: dict[str, dict] = {}
    multi_layout = len(cfg.layouts) > 1
    for (t, v), lay in ((tv, lay) for tv in cfg.configurations() for lay in cfg.layouts):
        config_id = f"{t.name}/{v.name}" + (f"/{lay}" if multi_layout else "")
        dest = run_dir / "profiles" / _dirname(config_id)
        log.info("profile pass: %s", config_id)
        try:
            out[config_id] = _profile_configuration(cfg, bench, t, v, manifests[lay], resolved[t.name],
                                                    f"profile-{config_id}", dest)
            out[config_id]["dir"] = str(dest.relative_to(run_dir))
        except Exception:  # noqa: BLE001 - profiling never fails the run
            log.error("profile pass of %s failed:\n%s", config_id, traceback.format_exc())
            out[config_id] = {"errors": [traceback.format_exc()[-1500:]]}
    return out


# ---------------------------------------------------------------- collapsed stacks
_HIDDEN_CLASS = re.compile(r"\.0x[0-9a-f]+")   # lambda forms / generated classes differ per JVM
_VM_THREADS = (("JIT compiler threads", re.compile(r"CompileBroker|Compiler")),
               ("GC threads", re.compile(r"G1|GC|WorkerThread::run|ConcurrentGCThread")))


def _frame_name(frame: str) -> str:
    return _HIDDEN_CLASS.sub("", _ANNOTATION.sub("", frame).replace("/", "."))


def java_self(collapsed: Path, mode: str = "cpu") -> dict[str, Any]:
    """Self value per Java frame: each stack is charged to its innermost Java frame, so native
    leaves (copy stubs, allocation slow paths) count for the Java method that called them. In
    allocation profiles the leaf is the allocated type: it is counted per type and the stack is
    charged to the Java method that allocated. Stacks without a Java frame are grouped by kind
    of VM thread."""
    frames: dict[str, int] = {}
    types: dict[str, int] = {}
    vm: dict[str, int] = {}
    total = 0
    if collapsed.exists():
        with collapsed.open() as f:
            for line in f:
                stack, _, value = line.rstrip("\n").rpartition(" ")
                if not value.isdigit():
                    continue
                n = int(value)
                total += n
                parts = stack.split(";")
                if mode == "alloc" and parts:
                    t = _frame_name(parts.pop())
                    types[t] = types.get(t, 0) + n
                for frame in reversed(parts):
                    if _JAVA_FRAME.search(frame):
                        name = _frame_name(frame)
                        frames[name] = frames.get(name, 0) + n
                        break
                else:
                    kind = next((k for k, rx in _VM_THREADS if rx.search(stack)), "other VM / native")
                    vm[kind] = vm.get(kind, 0) + n
    return {"frames": frames, "types": types, "vm": vm, "total": total}


# ---------------------------------------------------------------- profile.md
def _fmt_bytes(b: float | None) -> str:
    if not b:
        return "0"
    for unit, size in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if abs(b) >= size:
            return f"{b / size:.1f} {unit}"
    return f"{b:.0f} B"


def _fmt_value(v: float, mode: str) -> str:
    return f"{v / 1e9:.2f} s" if mode == "cpu" else _fmt_bytes(v)


def _short(error: str) -> str:
    lines = error.strip().splitlines() or [""]
    return (lines[-1] if lines[0].startswith("Traceback") else lines[0])[:150]


def _md(s: Any) -> str:
    return str(s).replace("|", "\\|")


def _s3_calls(counters: dict) -> str:
    def total(name):
        return int(sum(v for k, v in counters.items() if k.startswith(f"s3_{name}") and k.endswith("_calls")))
    parts = [f"{total(n)} {label}" for n, label in (("getobject", "GET"), ("headobject", "HEAD"),
                                                       ("listobjectsv2", "LIST"))]
    return ", ".join(parts) if any(k.startswith("s3_") for k in counters) else "n/a"


def write_markdown(results: dict, run_dir: Path) -> Path:
    profile = results.get("profile") or {}
    configs = list(profile)
    lines = [f"# Profile: {results.get('name')}", "",
             ("One extra pass per configuration after the timed runs (warmup pass, CPU-profiled pass, "
             "allocation-profiled pass). Numbers are single executions of the CPU-profiled pass, not "
             "measurements. CPU and allocations are summed over all nodes; GC, allocation and S3 "
             "deltas come from JMX and include the small jmx queries between queries."), ""]
    lines += ["| configuration | CPU event | CPU pass | files | problems |", "|---|---|---:|---|---|"]
    for c in configs:
        p = profile[c]
        lines.append(f"| {_md(c)} | {p.get('cpu_event', 'n/a')} | {p.get('cpu_pass_seconds', '?')} s | "
                     f"`{p.get('dir', '')}` | {_md('; '.join(_short(e) for e in p.get('errors', [])))} |")
    lines.append("")

    queries = list(dict.fromkeys(q for c in configs for q in (profile[c].get("queries") or {})))
    if queries:
        lines += ["## Queries", "",
                  ("Top operators by CPU (share of the query's operator CPU). Allocation is the JVM total "
                  "(TotalThreadAllocatedBytes delta), JIT the compiler time (TotalCompilationTime delta)."), ""]
    for q in queries:
        lines += [f"### {q}", "",
                  "| configuration | wall | CPU | GC (count / ms) | JIT | allocated | S3 calls | top operators |",
                  "|---|---:|---:|---:|---:|---:|---|---|"]
        for c in configs:
            tables = profile[c].get("jmx_tables") or []
            counted = {"gc": any("garbagecollector" in t for t in tables),
                       "alloc": any(t.endswith("type=threading") for t in tables),
                       "jit": any(t.endswith("type=compilation") for t in tables)}
            r = (profile[c].get("queries") or {}).get(q)
            if not r:
                continue
            k = r.get("counters") or {}
            ops = ", ".join(f"{o['operator'].removesuffix('Operator')} {o['cpu_share'] * 100:.0f}%"
                            for o in r.get("operators", [])[:4])
            gc = f"{int(k.get('gc_count', 0))} / {k.get('gc_time_ms', 0):.0f}" if counted["gc"] else "n/a"
            jit = f"{k.get('jit_time_ms', 0):.0f} ms" if counted["jit"] else "n/a"
            lines.append(f"| {_md(c)} | {r['wall_ms']:.0f} ms | {r.get('total_cpu_ms', 0):.0f} ms | {gc} | {jit} | "
                         f"{_fmt_bytes(k.get('allocated_bytes')) if counted['alloc'] else 'n/a'} | {_s3_calls(k)} | "
                         f"{_md(ops)}{' **error**' if r.get('error') else ''} |")
        lines.append("")

    prof: dict[tuple[str, str], dict[str, Any]] = {}
    for c in configs:
        d = profile[c].get("dir")
        for mode in ("cpu", "alloc"):
            prof[(c, mode)] = java_self(run_dir / d / f"{mode}.collapsed", mode) if d else java_self(Path("-"))
    for mode, title, n in (("cpu", "CPU", TOP_FRAMES), ("alloc", "allocation", 15)):
        lines += [f"## Hottest Java frames: {title} (self, whole profiled pass)", "",
                  "Each sample is charged to its innermost Java frame. "
                  + ("Values are CPU seconds of all threads, including JIT compiler and GC threads (which "
                     "Trino's query CPU time does not count)." if mode == "cpu"
                     else "Values are allocated bytes (estimated from samples), charged to the allocating "
                          "Java method; allocated types are listed separately."), ""]
        for c in configs:
            p = prof[(c, mode)]
            total = p["total"]
            if not total:
                continue
            vm = ", ".join(f"{k} {_fmt_value(v, mode)} ({v / total * 100:.0f}%)"
                           for k, v in sorted(p["vm"].items(), key=lambda kv: -kv[1]))
            lines += [f"**{_md(c)}**: total {_fmt_value(total, mode)}" + (f"; without Java frame: {vm}" if vm else ""),
                      "", "| # | frame | self | share |", "|---:|---|---:|---:|"]
            for i, (name, val) in enumerate(sorted(p["frames"].items(), key=lambda kv: -kv[1])[:n], 1):
                lines.append(f"| {i} | `{_md(name)}` | {_fmt_value(val, mode)} | {val / total * 100:.1f}% |")
            lines.append("")
            if p["types"]:
                lines.append("Allocated types: " + ", ".join(
                    f"`{_md(k)}` {_fmt_bytes(v)} ({v / total * 100:.0f}%)"
                    for k, v in sorted(p["types"].items(), key=lambda kv: -kv[1])[:10]))
                lines.append("")
        base = configs[0] if configs else None
        for c in configs[1:]:
            b, x = prof[(base, mode)], prof[(c, mode)]
            if not b["total"] or not x["total"]:
                continue
            bf, cf = b["frames"], x["frames"]
            names = set(sorted(bf, key=lambda k: -bf[k])[:100]) | set(sorted(cf, key=lambda k: -cf[k])[:100])
            diff = sorted(names, key=lambda k: -abs(cf.get(k, 0) - bf.get(k, 0)))[:20]
            lines += [(f"**{_md(c)} vs {_md(base)}** ({title}): total {_fmt_value(b['total'], mode)} → "
                       f"{_fmt_value(x['total'], mode)}; largest changes"), "",
                      "| frame | baseline | change | delta |", "|---|---:|---:|---:|"]
            for name in diff:
                bv, xv = bf.get(name, 0), cf.get(name, 0)
                lines.append(f"| `{_md(name)}` | {_fmt_value(bv, mode)} | {_fmt_value(xv, mode)} | "
                             f"{'+' if xv >= bv else '-'}{_fmt_value(abs(xv - bv), mode)} |")
            lines.append("")
    out = run_dir / "profile.md"
    out.write_text("\n".join(lines) + "\n")
    return out
