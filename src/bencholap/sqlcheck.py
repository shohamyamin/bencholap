"""Cheap SQL compatibility check: plan every query of a benchmark on a target engine
against empty tables (EXPLAIN (TYPE VALIDATE)), without loading data or executing.

Use it when adding an engine or a new version to see which canonical queries need an
override before spending compute on a real run.
"""

from __future__ import annotations

import re

import yaml

from . import benchmarks, stack
from .engines import get as get_engine
from .util import log


def check(benchmark: str, target_spec: str, engine_name: str = "trino", sf: str = "1",
          queries: list[str] | None = None) -> list[dict]:
    bench = benchmarks.load(benchmark)
    schema_def = yaml.safe_load((bench.dir / "schema.yaml").read_text())["tables"]
    stack.ensure_up()
    engine = get_engine(engine_name)
    target = engine.resolve(target_spec)
    running = engine.start(target, {}, {"memory": "2g", "cpus": 1}, label="sqlcheck")
    schema = f"{bench.name}_empty"
    out = []
    try:
        s = running.session(schema, {})
        s.execute(f"CREATE SCHEMA IF NOT EXISTS iceberg.{schema}")
        for table, cols in schema_def.items():
            s.execute(f"CREATE TABLE IF NOT EXISTS iceberg.{schema}.{table} ("
                      + ", ".join(f"{c} {t}" for c, t in cols) + ")")
        for qid in queries or bench.queries:
            q = bench.query(qid, sf, engine_name)
            res = {"query": qid, "override": q.override["file"] if q.override else None, "status": "ok"}
            try:
                for stmt in q.statements:
                    if re.match(r"^\s*(with|select|\()", stmt, re.IGNORECASE):
                        s.execute(f"EXPLAIN (TYPE VALIDATE) {stmt}")
                    else:
                        s.execute(stmt)
            except Exception as e:  # noqa: BLE001
                res.update(status="error", error=str(e)[:400])
            out.append(res)
        s.close()
    finally:
        running.stop()
    bad = [r for r in out if r["status"] != "ok"]
    log.info("%s on %s %s: %d/%d queries plan successfully", bench.name, engine_name, target.version,
             len(out) - len(bad), len(out))
    return out
