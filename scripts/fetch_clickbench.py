#!/usr/bin/env python3
"""Import the ClickBench workload for Trino from the ClickBench repository (pinned commit).

Writes into src/bencholap/benchmarks/clickbench/:
  queries/any/qNN.sql   the 43 ClickBench queries in Trino SQL (trino-datalake-partitioned/queries.sql)
  staging.sql           the raw Hive table over the Parquet files (from create.sql)
  load.sql              the SELECT that turns raw rows into the benchmark table (from the hits view)
  schema.yaml           column names and types of the resulting table (for check-sql)

Usage: python3 scripts/fetch_clickbench.py [commit]
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

COMMIT = sys.argv[1] if len(sys.argv) > 1 else "1084693d5b5b90eba868260e70df699d32ebbe3b"
SRC = "trino-datalake-partitioned"
OUT = Path(__file__).resolve().parents[1] / "src" / "bencholap" / "benchmarks" / "clickbench"


def fetch(path: str) -> str:
    url = f"https://raw.githubusercontent.com/ClickHouse/ClickBench/{COMMIT}/{path}"
    return subprocess.run(["curl", "-sfL", url], check=True, capture_output=True, text=True).stdout


def main() -> None:
    queries = [q.strip() for q in fetch(f"{SRC}/queries.sql").splitlines() if q.strip()]
    assert len(queries) == 43, len(queries)
    qdir = OUT / "queries" / "any"
    qdir.mkdir(parents=True, exist_ok=True)
    for n, q in enumerate(queries):
        (qdir / f"q{n:02d}.sql").write_text(
            f"-- ClickBench Q{n} (Trino dialect), ClickHouse/ClickBench@{COMMIT[:12]} {SRC}/queries.sql line {n + 1}\n"
            + q.rstrip(";") + ";\n")

    create = fetch(f"{SRC}/create.sql")
    raw = re.search(r"CREATE TABLE hive\.clickbench\.hits_raw \((.*?)\)\s*WITH", create, re.S).group(1)
    cols = [ln.strip().rstrip(",").split() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("--")]
    (OUT / "staging.sql").write_text(
        f"-- Raw table over the ClickBench Parquet files: column list from ClickHouse/ClickBench@{COMMIT[:12]}\n"
        f"-- {SRC}/create.sql (hits_raw). Placeholders: {{table}}, {{location}}.\n"
        "CREATE TABLE {table} (\n" + ",\n".join(f"    {c} {t}" for c, t in cols)
        + "\n) WITH (external_location = '{location}', format = 'PARQUET')\n")

    view = re.search(r"CREATE VIEW hive\.clickbench\.hits AS\s*(SELECT.*?)FROM hive\.clickbench\.hits_raw", create, re.S).group(1)
    (OUT / "load.sql").write_text(
        f"-- Benchmark table from the raw table: the hits view of ClickHouse/ClickBench@{COMMIT[:12]}\n"
        f"-- {SRC}/create.sql (EventTime, ClientEventTime and LocalEventTime are Unix seconds in the files).\n"
        "-- Placeholder: {source}.\n" + view.strip() + "\nFROM {source}\n")

    # from_unixtime returns timestamp(3) with time zone; Iceberg stores it as timestamp(6) with time zone
    converted = {m.group(2): "timestamp(6) with time zone"
                 for m in re.finditer(r"from_unixtime\((\w+)\)\s+AS\s+(\w+)", view, re.I)}
    schema = {"hits": [[c.lower(), converted.get(c, t)] for c, t in cols]}
    (OUT / "schema.yaml").write_text(
        "# Columns of the ClickBench hits table after load.sql (used for check-sql against empty tables).\n"
        + yaml.safe_dump({"tables": schema}, default_flow_style=None, sort_keys=False, width=200))
    (OUT / "SOURCE_COMMIT").write_text(COMMIT + "\n")
    print(f"wrote {len(queries)} queries and the table definition to {OUT}")


if __name__ == "__main__":
    main()
