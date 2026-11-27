"""Profile pass support for Trino: operator summaries, JMX counters and async-profiler.

Used only by the optional profile pass (src/bencholap/profiling.py), which runs after the
timed measurements on a freshly started cluster with an extra `jmx` catalog.
"""

from __future__ import annotations

import os
import re
import tarfile
import urllib.request
from pathlib import Path
from typing import Any

from ...util import home, log, run

ASYNC_PROFILER_VERSION = os.environ.get("BENCHOLAP_ASYNC_PROFILER_VERSION", "4.6")
REMOTE_DIR = "/tmp/bencholap-async-profiler"


def _duration_ms(v: Any) -> float:
    from . import _duration_ms as parse

    return parse(v) or 0.0


def _size_bytes(v: Any) -> float:
    from . import _size_bytes as parse

    return parse(v) or 0.0


# ---------------------------------------------------------------- operators
def operator_summary(infos: list[dict], top: int = 10) -> list[dict]:
    """queryStats.operatorSummaries of the statements of one query, summed by operator type,
    the `top` types with the most CPU. cpu_share is the share of the CPU of all operators."""
    agg: dict[str, dict[str, Any]] = {}
    for info in infos:
        for op in (info.get("queryStats") or {}).get("operatorSummaries") or []:
            a = agg.setdefault(op.get("operatorType") or "?", {
                "operator": op.get("operatorType") or "?", "instances": 0, "cpu_ms": 0.0, "wall_ms": 0.0,
                "blocked_ms": 0.0, "input_positions": 0, "input_bytes": 0.0, "output_positions": 0,
                "output_bytes": 0.0, "peak_memory_bytes": 0.0})
            a["instances"] += 1
            a["cpu_ms"] += sum(_duration_ms(op.get(k)) for k in ("addInputCpu", "getOutputCpu", "finishCpu"))
            a["wall_ms"] += sum(_duration_ms(op.get(k)) for k in ("addInputWall", "getOutputWall", "finishWall"))
            a["blocked_ms"] += _duration_ms(op.get("blockedWall"))
            a["input_positions"] += op.get("inputPositions") or 0
            a["input_bytes"] += _size_bytes(op.get("inputDataSize"))
            a["output_positions"] += op.get("outputPositions") or 0
            a["output_bytes"] += _size_bytes(op.get("outputDataSize"))
            # largest peak of one operator instance (peaks of different operators need not overlap)
            a["peak_memory_bytes"] = max(a["peak_memory_bytes"], _size_bytes(op.get("peakUserMemoryReservation")))
    total = sum(a["cpu_ms"] for a in agg.values()) or 1.0
    ops = sorted(agg.values(), key=lambda a: -a["cpu_ms"])[:top]
    for a in ops:
        a["cpu_share"] = round(a["cpu_ms"] / total, 4)
        for k in ("cpu_ms", "wall_ms", "blocked_ms"):
            a[k] = round(a[k], 1)
    return ops


# ---------------------------------------------------------------- JMX counters
# Cumulative counters read from the jmx catalog (summed over all nodes) before and after each
# query; the difference is the query's share (one query runs at a time in the profile pass,
# the small jmx queries themselves are included).
_GC = "java.lang:%type=garbagecollector%"   # jmx table names are lowercase, keys sorted
_THREADING = "java.lang:type=threading"
_COMPILATION = "java.lang:type=compilation"


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class JmxCounters:
    def __init__(self, session) -> None:
        self.session = session
        rows = session.execute(
            "SELECT table_name FROM jmx.information_schema.tables WHERE table_schema = 'current' AND ("
            f"table_name LIKE '{_GC}' OR table_name IN ('{_THREADING}', '{_COMPILATION}') OR table_name LIKE '%s3filesystemstats%')"
        ).rows or []
        self.tables = sorted(r[0] for r in rows)
        self.errors: list[str] = []

    def _select(self, sql: str) -> tuple[list[str], list[tuple]]:
        r = self.session.execute(sql)
        return [c.lower() for c in (r.columns or [])], r.rows or []

    def snapshot(self) -> dict[str, float]:
        out: dict[str, float] = {}

        def add(key: str, v: Any) -> None:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[key] = out.get(key, 0) + v

        for table in self.tables:
            try:
                if "type=garbagecollector" in table:
                    m = re.search(r"name=([^,]+)", table)
                    name = re.sub(r"[^a-z0-9]+", "_", (m.group(1) if m else table).lower()).strip("_")
                    _, rows = self._select(f"SELECT collectioncount, collectiontime FROM jmx.current.{_quote(table)}")
                    for count, ms in rows:
                        add("gc_count", count)
                        add("gc_time_ms", ms)
                        add(f"gc_{name}_count", count)
                        add(f"gc_{name}_time_ms", ms)
                elif table == _COMPILATION:
                    _, rows = self._select(f"SELECT totalcompilationtime FROM jmx.current.{_quote(table)}")
                    for (v,) in rows:
                        add("jit_time_ms", v)
                elif table == _THREADING:
                    _, rows = self._select(f"SELECT totalthreadallocatedbytes FROM jmx.current.{_quote(table)}")
                    for (v,) in rows:
                        add("allocated_bytes", v)
                else:  # S3FileSystemStats: CounterStat totals per API call, e.g. getobject.calls.totalcount
                    cols, rows = self._select(f"SELECT * FROM jmx.current.{_quote(table)}")
                    for row in rows:
                        for c, v in zip(cols, row):
                            if c.endswith(".totalcount"):
                                add("s3_" + re.sub(r"[^a-z0-9]+", "_", c.removesuffix(".totalcount")), v)
            except Exception as e:  # noqa: BLE001 - a missing bean or column only loses that counter
                if len(self.errors) < 10:
                    self.errors.append(f"{table}: {str(e)[:200]}")
        return out

    @staticmethod
    def delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
        return {k: round(v - before.get(k, 0), 3) for k, v in after.items() if v - before.get(k, 0)}


# ---------------------------------------------------------------- async-profiler
def _async_profiler() -> Path:
    """Download (once) the async-profiler release for this architecture."""
    arch = {"x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}[os.uname().machine]
    name = f"async-profiler-{ASYNC_PROFILER_VERSION}-linux-{arch}"
    root = home() / "cache" / "async-profiler"
    if not (root / name / "bin" / "asprof").exists():
        root.mkdir(parents=True, exist_ok=True)
        archive = root / f"{name}.tar.gz"
        url = (f"https://github.com/async-profiler/async-profiler/releases/download/"
               f"v{ASYNC_PROFILER_VERSION}/{name}.tar.gz")
        log.info("downloading %s", url)
        urllib.request.urlretrieve(url, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(root, filter="data")
        archive.unlink()
    return root / name


class AsyncProfiler:
    """async-profiler attached (dynamic attach, as the trino user) to the Trino JVM of every
    container of a docker cluster. Values are totals (--total): CPU nanoseconds or bytes."""

    CPU_EVENTS = ("cpu", "ctimer", "itimer")

    def __init__(self, containers: list[str]) -> None:
        self.containers = containers
        local = _async_profiler()
        self.pids: dict[str, str] = {}
        for c in containers:
            run(["docker", "exec", "-u", "root", c, "rm", "-rf", REMOTE_DIR], capture=True, check=False)
            run(["docker", "cp", str(local), f"{c}:{REMOTE_DIR}"], capture=True)
            # the JDK's jps lists the JVMs of the container's user; the server's main class is io.trino.*
            out = run(["docker", "exec", c, "sh", "-c", 'PATH="$PATH:$JAVA_HOME/bin" jps -l'],
                      capture=True, check=False)
            pids = [ln.split()[0] for ln in (out.stdout or "").splitlines() if "io.trino" in ln]
            if not pids:
                raise RuntimeError(f"no Trino JVM found in {c}: {((out.stdout or '') + (out.stderr or ''))[:300]}")
            self.pids[c] = pids[0]
        self.event: str | None = None

    def _asprof(self, c: str, *args: str) -> tuple[bool, str]:
        out = run(["docker", "exec", "-u", "trino", c, f"{REMOTE_DIR}/bin/asprof", *args, self.pids[c]],
                  capture=True, check=False, timeout=300)
        text = ((out.stdout or "") + (out.stderr or "")).strip()
        return out.returncode == 0 and "error" not in text.lower(), text

    def start(self, mode: str) -> str:
        """mode cpu: the first CPU event that works in the container (perf_events need privileges,
        ctimer/itimer do not); mode alloc: allocation sampling. Returns the event used."""
        events = self.CPU_EVENTS if mode == "cpu" else ("alloc",)
        errors = []
        for event in events:
            results = [self._asprof(c, "start", "-e", event) for c in self.containers]
            if all(ok for ok, _ in results):
                self.event = event
                return event
            errors.append(f"{event}: {'; '.join(t for _, t in results)[:300]}")
            for c in self.containers:
                self._asprof(c, "stop")
        raise RuntimeError("async-profiler did not start: " + " | ".join(errors))

    def stop(self, dest: Path, mode: str) -> list[Path]:
        """Write <mode>.collapsed (merged over all nodes) and one flame graph per node into dest."""
        dest.mkdir(parents=True, exist_ok=True)
        merged: dict[str, int] = {}
        files = []
        for i, c in enumerate(self.containers):
            node = "" if len(self.containers) == 1 else ("-coordinator" if i == 0 else f"-worker-{i}")
            remote = f"/tmp/bencholap-{mode}"
            self._asprof(c, "dump", "-o", "collapsed", "-a", "--total", "-f", f"{remote}.collapsed")
            self._asprof(c, "stop", "-o", "flamegraph", "-a", "--total", "--title", f"{mode} {c}",
                         "-f", f"{remote}.html")
            html = dest / f"{mode}{node}.html"
            if run(["docker", "cp", f"{c}:{remote}.html", str(html)], capture=True, check=False).returncode == 0:
                files.append(html)
            tmp = dest / f".{mode}{node}.collapsed"
            if run(["docker", "cp", f"{c}:{remote}.collapsed", str(tmp)], capture=True, check=False).returncode == 0:
                for line in tmp.read_text().splitlines():
                    stack, _, value = line.rpartition(" ")
                    if stack and value.isdigit():
                        merged[stack] = merged.get(stack, 0) + int(value)
                tmp.unlink()
        collapsed = dest / f"{mode}.collapsed"
        collapsed.write_text("".join(f"{s} {v}\n" for s, v in sorted(merged.items(), key=lambda kv: -kv[1])))
        files.append(collapsed)
        return files

    def close(self) -> None:
        for c in self.containers:
            run(["docker", "exec", "-u", "root", c, "rm", "-rf", REMOTE_DIR], capture=True, check=False)
