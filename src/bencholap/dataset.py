"""Build benchmark datasets once into the shared Iceberg catalog.

Pipeline: tpcgen-cli (byte-identical to dbgen/dsdgen) -> raw Parquet uploaded to the raw
bucket -> a pinned "loader" Trino reads it through a Hive staging catalog and writes the
Iceberg tables with CREATE TABLE AS SELECT using the table properties of the chosen
validated layout -> optional ANALYZE -> row counts checked -> manifest written.

Every engine and version under test then reads exactly the same Iceberg snapshot.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import fs as pafs

from . import benchmarks, stack
from .engines import get as get_engine
from .util import home, log, read_json, run, write_json

DEFAULT_LOADER = "484"


@dataclass(frozen=True)
class DatasetId:
    benchmark: str
    scale_factor: str
    layout: str

    @property
    def schema(self) -> str:
        sf = self.scale_factor.replace(".", "_")
        return f"{self.benchmark}_sf{sf}_{self.layout}".replace("-", "_")

    @property
    def key(self) -> str:
        return f"{self.benchmark}/sf{self.scale_factor}/{self.layout}"


def manifest_path(ds: DatasetId) -> Path:
    return stack.state_dir() / "datasets" / f"{ds.schema}.json"


def get_manifest(ds: DatasetId) -> dict | None:
    p = manifest_path(ds)
    return read_json(p) if p.exists() else None


def list_manifests() -> list[dict]:
    d = stack.state_dir() / "datasets"
    return [read_json(p) for p in sorted(d.glob("*.json"))] if d.exists() else []


def _trino_type(t: pa.DataType) -> str:
    if pa.types.is_int32(t):
        return "integer"
    if pa.types.is_int64(t):
        return "bigint"
    if pa.types.is_decimal(t):
        return f"decimal({t.precision},{t.scale})"
    if pa.types.is_string(t) or pa.types.is_large_string(t) or str(t) == "string_view":
        return "varchar"
    if pa.types.is_date32(t):
        return "date"
    if pa.types.is_float64(t):
        return "double"
    if pa.types.is_boolean(t):
        return "boolean"
    raise ValueError(f"unsupported generated column type {t}")


def generate(bench: benchmarks.Benchmark, sf: str, out: Path) -> Path:
    if out.exists() and any(out.glob("*.parquet")):
        log.info("reusing generated data in %s", out)
        return out
    out.mkdir(parents=True, exist_ok=True)
    tool, version = bench.generator["tool"], bench.generator["version"]
    log.info("generating %s SF%s with %s %s", bench.name, sf, tool, version)
    run(["uvx", "--from", f"{tool}=={version}", tool, bench.name, "parquet", "-s", sf,
         "-o", str(out), "--tables", ",".join(bench.tables)])
    return out


def build(benchmark: str, sf: str, layout: str | None = None, loader: str = DEFAULT_LOADER,
          force: bool = False, keep_raw: bool = False, resources: dict | None = None) -> dict:
    bench = benchmarks.load(benchmark)
    sf = benchmarks.format_sf(sf)
    if sf not in bench.scale_factors():
        raise ValueError(f"{benchmark} has canonical queries for scale factors {bench.scale_factors()}, not {sf}")
    lay = bench.layout(layout)
    ds = DatasetId(bench.name, sf, lay.name)
    existing = get_manifest(ds)
    if existing and not force:
        log.info("dataset %s already built", ds.key)
        return existing

    stack.ensure_up()
    local = generate(bench, sf, home() / "data" / bench.name / f"sf{sf}")
    s3 = stack.s3_filesystem()
    raw_prefix = f"{stack.STACK.raw_bucket}/{bench.name}/sf{sf}"
    schemas: dict[str, pa.Schema] = {}
    for table in bench.tables:
        src = local / f"{table}.parquet"
        schemas[table] = pq.read_schema(src)
        dst = f"{raw_prefix}/{table}/{table}.parquet"
        if s3.get_file_info(dst).type != pafs.FileType.File:
            pafs.copy_files(str(src), dst, destination_filesystem=s3)
    log.info("raw data uploaded to s3://%s", raw_prefix)

    engine = get_engine("trino")
    target = engine.resolve(loader)
    running = engine.start(target, {}, resources or {"memory": "8g"}, catalogs=("iceberg", "staging"),
                           label="loader")
    started = time.time()
    try:
        sess = running.session("default", {})
        q = sess.execute
        staging = f"staging.{ds.schema}"
        q(f"CREATE SCHEMA IF NOT EXISTS {staging} WITH (location = 's3://{raw_prefix}/')")
        if force:
            for table in bench.tables:
                q(f"DROP TABLE IF EXISTS iceberg.{ds.schema}.{table}")
        q(f"CREATE SCHEMA IF NOT EXISTS iceberg.{ds.schema}")
        tables = {}
        for table in bench.tables:
            cols = ", ".join(f"{f.name} {_trino_type(f.type)}" for f in schemas[table])
            q(f"DROP TABLE IF EXISTS {staging}.{table}")
            q(f"CREATE TABLE {staging}.{table} ({cols}) WITH (format = 'PARQUET', "
              f"external_location = 's3://{raw_prefix}/{table}/')")
            tl = lay.table(table)
            props = ["format = 'PARQUET'", "format_version = 2"]
            if tl.partitioning:
                props.append("partitioning = ARRAY[" + ", ".join(f"'{c}'" for c in tl.partitioning) + "]")
            if tl.sorted_by:
                props.append("sorted_by = ARRAY[" + ", ".join(f"'{c}'" for c in tl.sorted_by) + "]")
            if tl.bloom_filter_columns:
                props.append("parquet_bloom_filter_columns = ARRAY["
                             + ", ".join(f"'{c}'" for c in tl.bloom_filter_columns) + "]")
            t0 = time.time()
            log.info("loading %s.%s", ds.schema, table)
            q(f"CREATE TABLE iceberg.{ds.schema}.{table} WITH ({', '.join(props)}) "
              f"AS SELECT * FROM {staging}.{table}")
            if lay.analyze:
                q(f"ANALYZE iceberg.{ds.schema}.{table}")
            load_s = time.time() - t0
            expected = q(f"SELECT count(*) FROM {staging}.{table}").rows[0][0]
            actual = q(f"SELECT count(*) FROM iceberg.{ds.schema}.{table}").rows[0][0]
            if expected != actual:
                raise RuntimeError(f"{table}: loaded {actual} rows, expected {expected}")
            files = q(f'SELECT count(*), sum(file_size_in_bytes) FROM iceberg.{ds.schema}."{table}$files"').rows[0]
            snap = q(f'SELECT snapshot_id FROM iceberg.{ds.schema}."{table}$snapshots" '
                     "ORDER BY committed_at DESC LIMIT 1").rows[0][0]
            ddl = q(f"SHOW CREATE TABLE iceberg.{ds.schema}.{table}").rows[0][0]
            tables[table] = {"rows": actual, "data_files": files[0], "data_bytes": files[1],
                             "snapshot_id": snap, "load_seconds": round(load_s, 2), "ddl": ddl}
            q(f"DROP TABLE {staging}.{table}")
        q(f"DROP SCHEMA IF EXISTS {staging}")
        sess.close()
    finally:
        running.stop()

    if not keep_raw:
        s3.delete_dir(raw_prefix)
        shutil.rmtree(local, ignore_errors=True)

    manifest = {
        "id": ds.schema,
        "benchmark": bench.name,
        "scale_factor": sf,
        "layout": lay.as_dict(),
        "catalog": "iceberg",
        "schema": ds.schema,
        "generator": bench.generator,
        "loader": {"spec": target.spec, "version": target.version, "image": target.image,
                   "source": target.source},
        "stack": {"storage_image": stack.SEAWEEDFS_IMAGE, "catalog_image": stack.REST_CATALOG_IMAGE},
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "build_seconds": round(time.time() - started, 1),
        "tables": tables,
    }
    write_json(manifest_path(ds), manifest)
    log.info("dataset %s ready: %d tables, %.1f MB", ds.key, len(tables),
             sum(t["data_bytes"] or 0 for t in tables.values()) / 1e6)
    return manifest
