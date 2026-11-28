"""Build benchmark datasets once into the shared Iceberg catalog.

Pipeline: tpcgen-cli (byte-identical to dbgen/dsdgen) -> raw Parquet uploaded to the raw
bucket -> a pinned "loader" Trino reads it through a Hive staging catalog and writes the
Iceberg tables with CREATE TABLE AS SELECT using the table properties of the chosen
validated layout -> optional ANALYZE -> row counts checked -> manifest written.

Every engine and version under test then reads exactly the same Iceberg snapshot.
"""

from __future__ import annotations

import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import requests
from pyarrow import fs as pafs

from . import benchmarks, stack
from .engines import get as get_engine
from .util import home, log, read_json, run, write_json

DEFAULT_LOADER = "484"
LOADER_CONFIG = {"query.max-memory-per-node": "5GB", "query.max-memory": "5GB"}


@dataclass(frozen=True)
class DatasetId:
    benchmark: str
    scale_factor: str
    layout: str
    writer: str = ""     # empty: written by the pinned default loader; else a tag of the engine build that wrote it

    @property
    def schema(self) -> str:
        sf = self.scale_factor.replace(".", "_")
        suffix = f"_w{self.writer}" if self.writer else ""
        return f"{self.benchmark}_sf{sf}_{self.layout}{suffix}".replace("-", "_")

    @property
    def key(self) -> str:
        return f"{self.benchmark}/sf{self.scale_factor}/{self.layout}" + (f"@{self.writer}" if self.writer else "")


def writer_tag(target) -> str:
    """Identifies the build that wrote a dataset: the commit of source builds, otherwise the version."""
    commit = (target.source or {}).get("commit") or ""
    if re.fullmatch(r"[0-9a-f]{12,40}", commit):
        return commit[:12]
    return re.sub(r"[^0-9a-z]+", "_", str(target.version).lower()).strip("_") or "unknown"


def dataset_id(benchmark: str, sf: str, key: str, resolved: dict) -> DatasetId:
    """DatasetId of a run's dataset key ("<layout>" or "<layout>@<target name>"), `resolved` maps target names to
    resolved targets."""
    layout, _, loader = key.partition("@")
    return DatasetId(benchmark, sf, layout, writer_tag(resolved[loader]) if loader else "")


def manifest_path(ds: DatasetId) -> Path:
    return stack.state_dir() / "datasets" / f"{ds.schema}.json"


def get_manifest(ds: DatasetId) -> dict | None:
    p = manifest_path(ds)
    return read_json(p) if p.exists() else None


def list_manifests() -> list[dict]:
    d = stack.state_dir() / "datasets"
    return [read_json(p) for p in sorted(d.glob("*.json"))] if d.exists() else []


def _strip_comments(sql: str) -> str:
    return "\n".join(ln for ln in sql.splitlines() if not ln.lstrip().startswith("--")).strip().rstrip(";")


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
    """Generated (TPC) or downloaded (ClickBench) raw Parquet files, one directory per table."""
    if out.exists() and any(out.rglob("*.parquet")):
        log.info("reusing raw data in %s", out)
        return out
    out.mkdir(parents=True, exist_ok=True)
    g = bench.generator
    if g["tool"] == "download":
        tdir = out / g["table"]
        tdir.mkdir(exist_ok=True)
        n = int(float(sf))
        log.info("downloading %d %s file(s)", n, bench.name)
        for i in range(n):
            url = g["url"].format(i=i)
            target = tdir / url.rsplit("/", 1)[-1]
            if target.exists():
                continue
            with requests.get(url, stream=True, timeout=600) as r:
                r.raise_for_status()
                tmp = target.with_suffix(".part")
                with open(tmp, "wb") as f:
                    f.writelines(r.iter_content(1 << 20))
                tmp.rename(target)
        return out
    tool, version = g["tool"], g["version"]
    log.info("generating %s SF%s with %s %s", bench.name, sf, tool, version)
    run(["uvx", "--from", f"{tool}=={version}", tool, bench.name, "parquet", "-s", sf,
         "-o", str(out), "--tables", ",".join(bench.tables)])
    for table in bench.tables:  # one directory per table, like the downloaded datasets
        (out / table).mkdir(exist_ok=True)
        (out / f"{table}.parquet").rename(out / table / f"{table}.parquet")
    return out


def _table_props(tl: benchmarks.TableLayout) -> list[str]:
    def arr(cols):
        return "ARRAY[" + ", ".join(f"'{c}'" for c in cols) + "]"
    props = ["format = 'PARQUET'", "format_version = 2"]
    if tl.partitioning:
        props.append(f"partitioning = {arr(tl.partitioning)}")
    if tl.sorted_by:
        props.append(f"sorted_by = {arr(tl.sorted_by)}")
    if tl.bloom_filter_columns:
        props.append(f"parquet_bloom_filter_columns = {arr(tl.bloom_filter_columns)}")
    return props


def build_many(benchmark: str, sf: str, layouts: list[str | None], loaders: dict[str, str] | None = None,
               **kw) -> list[dict]:
    """Build several datasets of one benchmark and scale factor from the same raw data. `layouts` are layout
    names or "<layout>@<target name>" keys; `loaders` maps the keys written by a target to its source."""
    keep = kw.pop("keep_raw", False)
    loaders = loaders or {}
    out = []
    for i, key in enumerate(layouts):
        layout = key.partition("@")[0] if key else key
        extra = {"loader": loaders[key], "tag_writer": True} if key in loaders else {}
        out.append(build(benchmark, sf, layout, keep_raw=keep or i < len(layouts) - 1, **kw, **extra))
    return out


def build(benchmark: str, sf: str, layout: str | None = None, loader: str = DEFAULT_LOADER,
          force: bool = False, keep_raw: bool = False, resources: dict | None = None,
          tag_writer: bool = False) -> dict:
    """`tag_writer`: the dataset is a separate copy identified by the loader build (DatasetId.writer), for
    comparing what different engine builds write; otherwise it is the shared dataset of the pinned loader."""
    bench = benchmarks.load(benchmark)
    sf = benchmarks.format_sf(sf)
    if sf not in bench.scale_factors():
        raise ValueError(f"{benchmark} has canonical queries for scale factors {bench.scale_factors()}, not {sf}")
    lay = bench.layout(layout)
    engine = get_engine("trino")
    target = engine.resolve(loader) if tag_writer else None
    ds = DatasetId(bench.name, sf, lay.name, writer_tag(target) if target else "")
    existing = get_manifest(ds)
    if existing and not force:
        if existing.get("layout") == lay.as_dict() and existing.get("generator") == bench.generator:
            log.info("dataset %s already built", ds.key)
            return existing
        log.info("dataset %s was built with a different layout or generator definition; rebuilding", ds.key)
        force = True

    stack.ensure_up()
    local = generate(bench, sf, home() / "data" / bench.name / f"sf{sf}")
    s3 = stack.s3_filesystem()
    raw_prefix = f"{stack.STACK.raw_bucket}/{bench.name}/sf{sf}"
    schemas: dict[str, pa.Schema] = {}
    for table in bench.tables:
        files = sorted((local / table).glob("*.parquet"))
        if not files:
            raise RuntimeError(f"no raw data for {table} in {local / table}")
        schemas[table] = pq.read_schema(files[0])
        for src in files:
            dst = f"{raw_prefix}/{table}/{src.name}"
            if s3.get_file_info(dst).type != pafs.FileType.File:
                pafs.copy_files(str(src), dst, destination_filesystem=s3)
    log.info("raw data uploaded to s3://%s", raw_prefix)
    staging_ddl = staging_select = None
    if bench.staging:
        staging_ddl = (bench.dir / bench.staging["ddl"]).read_text()
        staging_select = (bench.dir / bench.staging["select"]).read_text()

    target = target or engine.resolve(loader)
    # Partitioned and sorted writes keep many writers open; give the loader query enough memory.
    running = engine.start(target, {"config": LOADER_CONFIG}, resources or {"memory": "10g"},
                           catalogs=("iceberg", "staging"), label="loader")
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
            q(f"DROP TABLE IF EXISTS {staging}.{table}")
            location = f"s3://{raw_prefix}/{table}/"
            if staging_ddl:
                q(_strip_comments(staging_ddl).format(table=f"{staging}.{table}", location=location))
                select = _strip_comments(staging_select).format(source=f"{staging}.{table}")
            else:
                cols = ", ".join(f"{f.name} {_trino_type(f.type)}" for f in schemas[table])
                q(f"CREATE TABLE {staging}.{table} ({cols}) WITH (format = 'PARQUET', "
                  f"external_location = '{location}')")
                select = f"SELECT * FROM {staging}.{table}"
            tl = lay.table(table)
            props = _table_props(tl)
            t0 = time.time()
            log.info("loading %s.%s (%s)", ds.schema, table, ", ".join(props[2:]) or "no layout properties")
            if tl.row_group_rows:
                q(f"SET SESSION iceberg.parquet_writer_row_group_max_row_count = {int(tl.row_group_rows)}")
            q(f"CREATE TABLE iceberg.{ds.schema}.{table} WITH ({', '.join(props)}) AS {select}")
            if tl.row_group_rows:
                q("RESET SESSION iceberg.parquet_writer_row_group_max_row_count")
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
        "writer": ds.writer,
        "stack": {"storage_image": stack.SEAWEEDFS_IMAGE, "catalog_image": stack.REST_CATALOG_IMAGE},
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "build_seconds": round(time.time() - started, 1),
        "tables": tables,
    }
    write_json(manifest_path(ds), manifest)
    log.info("dataset %s ready: %d tables, %.1f MB", ds.key, len(tables),
             sum(t["data_bytes"] or 0 for t in tables.values()) / 1e6)
    return manifest
