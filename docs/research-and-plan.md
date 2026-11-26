# bencholap: research and plan

Goal: an open-source, engine-agnostic benchmark harness that runs standard analytical
benchmarks (TPC-H, TPC-DS, later ClickBench and others) against query engines and
table formats, tracks results across releases and pull requests, compares engines
against each other, collects more than wall time (bytes read, files read, pruning,
CPU, memory), and publishes a readable report. Trino and its Iceberg connector are
the first target, but nothing in the core should be Trino-specific.

Research date: November 2026.

---

## 1. Existing projects

| Project | What it does | Engines | Iceberg | Metrics beyond time | CI / history | Fit for us |
|---|---|---|---|---|---|---|
| [trinodb/benchto](https://github.com/trinodb/benchto) | Macro-benchmark driver + results service (Postgres + web UI), Graphite/Grafana for cluster metrics, JFR/async-profiler hooks | Trino (JDBC, effectively Trino-only) | Via Trino | Cluster CPU/mem/network via Graphite, profiler output | Results service, no public dashboard | Trino-specific, heavy (Java service + Postgres + Graphite). Useful source of Trino-dialect TPC-H/TPC-DS query files (`testing/trino-benchto-benchmarks` in the Trino repo). |
| [prestodb/pbench](https://github.com/prestodb/pbench) | Go toolkit, positioned as a Benchto replacement: workloads, result capture, correctness checks, replay, result diffs, DDL generation | Presto, Prestissimo, Trino | Via engine | Query info JSON loaded into a DB for analysis | Used by the Presto project | Good ideas (stage JSON, result diffing, query-info ingestion), but Presto/Trino-only. |
| [microsoft/lst-bench](https://github.com/microsoft/lst-bench) (SIGMOD 2024) | Java JDBC runner + Python metrics module, built for table formats (Delta, Hudi, Iceberg): data maintenance, time travel, concurrency, degradation over time | Spark, Trino, Databricks, Snowflake, Fabric | Yes, first class | Telemetry per experiment/phase/session/statement; stability/degradation metrics | No CI story | Closest academic fit for the "evaluate the Iceberg connector" part, especially write/maintenance workloads. Its workload model (phase → session → task → statement) is worth copying. |
| [microsoft/LakeBench](https://github.com/microsoft/LakeBench) | Python library, `pip install`, ELTBench + TPC-H + TPC-DS + ClickBench, pluggable engine classes | Spark variants, DuckDB, Polars, Daft, Sail | No (Delta only today) | Engine version, compute size, duration, estimated cost | No | Nice extensibility model, but no Trino, no Iceberg, Fabric/Spark-centric. |
| [djouallah/lakehouse_benchmark](https://github.com/djouallah/lakehouse_benchmark) | Small-data, small-compute benchmark; TPC-H/TPC-DS + a "real workload" with dbt writing Iceberg via a REST catalog; published results site | DuckDB, StarRocks, chDB, Databend, Daft, others | Yes (OneLake via REST catalog) | Iceberg feature support matrix | Runs via GitHub workflows, public results page | Closest to our "same Iceberg tables, many engines" idea. Tied to Azure OneLake. Its "engine admission criteria" idea is good. |
| [ClickHouse/ClickBench](https://github.com/ClickHouse/ClickBench) | One dataset, 43 queries, a shell script per system, static results site | 100+ systems | Some entries read Parquet/Iceberg | Time + load time + storage size | Community PRs, static site | The model for "adding an engine = adding a folder". Only wall time; one denormalized table. |
| [PureStorage lakebench-k8s](https://github.com/PureStorage-OpenConnect/lakebench-k8s) | Provisions Spark + Iceberg + Trino on Kubernetes, medallion pipeline, 8-query score | Spark, Trino | Yes | Pipeline scoring | No | Custom workload, not a standard benchmark. |
| [conbench](https://github.com/conbench/conbench) | Language-agnostic continuous-benchmarking server used by Apache Arrow | Any (you post JSON) | n/a | Whatever you post | Yes, history + regression detection | A results-tracking backend, not a runner. Needs a hosted server. |
| [Bencher](https://bencher.dev/docs/how-to/github-actions/) | Continuous benchmarking service with statistical thresholds and PR comments | Any | n/a | Any numeric "measure" | Yes | Same role as conbench. Hosted SaaS or self-host. Could be an optional sink later. |
| [Nyrkiö](https://github.com/nyrkio/nyrkio) | Change-point detection for performance series | Any | n/a | Any | Yes | Useful reference for statistics. They report 20-50% noise on standard GitHub runners. |

Building blocks that already exist and should be reused, not rebuilt:

- **Data generation:** [tpcgen-rs / `tpcgen-cli`](https://github.com/datafusion-contrib/tpcgen-rs) generates TPC-H **and TPC-DS** directly to Parquet/CSV/Arrow, byte-for-byte identical to the reference generators, roughly 10x faster than `dbgen` (TPC-H SF100 Parquet in under 2 minutes on a laptop per the [DataFusion blog](https://datafusion.apache.org/blog/2025/04/10/fastest-tpch-generator/)). `uvx tpcgen-cli tpcds parquet -s 1 --output-dir ...`.
- **SQL translation:** [SQLGlot](https://github.com/tobymao/sqlglot) transpiles between 30+ dialects (Trino, Spark, DuckDB, Snowflake, ...) and its test suite already runs all TPC-H and TPC-DS queries.
- **Iceberg scan metrics:** Iceberg's [MetricsReporter / ScanReport API](https://iceberg.apache.org/docs/latest/metrics-reporting/) reports data/delete files and manifests considered, scanned and skipped, plus bytes and planning time. The REST catalog spec has a `/metrics` endpoint that engines can post these reports to (see [Polaris issue #3337](https://github.com/apache/polaris/issues/3337)). Which engines actually send them must be verified per engine.
- **Trino query metrics:** `QueryCompletedEvent` / `QueryStatistics` via the event listener SPI (HTTP event listener is built-in), or the `/v1/query/{id}` REST endpoint: wall, CPU, scheduled time, peak memory, physical input bytes/rows, processed rows, spilled bytes, per-operator stats.
- **Object storage for local runs:** MinIO community edition is archived (no images since Oct 2025, repo archived April 2026, per [this summary](https://pinggy.io/blog/minio_archived_self_hosted_s3_alternatives/)). Use SeaweedFS or Garage, both S3-compatible and docker-friendly.
- **REST catalogs:** Apache Polaris, Lakekeeper, Apache Gravitino, or the lightweight `apache/iceberg-rest-fixture` image for CI.

### Conclusion from the research

No existing project does all of: (a) Trino release/PR tracking, (b) multi-engine on the
same Iceberg tables, (c) storage-level I/O and pruning analysis, (d) automatic
translation, (e) free CI + static report. The pieces exist separately. The recommended
approach is a **thin new orchestrator** that reuses tpcgen-cli, SQLGlot, standard query
texts, Iceberg metrics and engine-native stats, and borrows design from LST-Bench
(workload model), ClickBench (one folder per engine, static site), pbench (result
diffing, query-info ingestion) and lakehouse_benchmark (engine admission criteria).

Alternative worth considering: contribute Trino + Iceberg support to LakeBench instead
of starting fresh. Cost: LakeBench is Delta-only and Spark/Fabric-oriented, and it has
no CI/history/report layer, so most of our work would still be new. Recommendation is a
new project, possibly offering engine adapters upstream later.

---

## 2. Principles

1. **Standard benchmarks only.** TPC-H, TPC-DS first. Later: ClickBench, SSB (Star Schema Benchmark), JOB (Join Order Benchmark), LST-Bench workloads for Iceberg write/maintenance.
2. **TPC fair use.** Results are not audited TPC results. Name them "TPC-H-derived" / "TPC-DS-derived" in reports and README, the way DuckDB, DataFusion and Polars do.
3. **Engine-agnostic core.** Core knows about datasets, workloads, runs and metrics. Engines, catalogs, table formats and storage are plugins.
4. **Correctness before speed.** Every query result is checked (reference answers or cross-engine agreement). A fast wrong answer is a failure.
5. **Deterministic metrics first, timing second.** Bytes read, files read, rows, plan shape and CPU time are far less noisy than wall time on shared runners. They are the main PR signal on free compute.
6. **Reproducible.** Every run records engine version/commit, image digest, config, dataset hash, hardware, and harness version. Anyone can rerun locally with one command.
7. **Start small.** One engine, one connector, one benchmark, one runner, then grow.

---

## 3. Architecture

```
            ┌───────────────────────────── bencholap CLI (Python) ─────────────────────────────┐
            │                                                                                  │
 config ──► │  Planner ──► Environment ──► Loader ──► Runner ──► Collectors ──► Validator ──► Results store
 (YAML)     │  (matrix)    (docker        (create    (warmup,   (engine,      (answers,       (JSON/Parquet)
            │               compose)       tables)    reps,      storage,      cross-engine)        │
            │                                         A/B)       iceberg,                           │
            │                                                    container)                         ▼
            │                                                                                 Reporter
            └──────────────────────────────────────────────────────────────────────── (HTML site, PR markdown)
```

### 3.1 Plugin axes

A run is a point in the matrix **engine × connector/format × catalog × storage × benchmark × scale factor**.

| Axis | Examples | Plugin responsibility |
|---|---|---|
| Engine | Trino, Spark, DuckDB, StarRocks, Presto, DataFusion | Start/stop (docker image or build), connect, run SQL, return query ID, fetch native stats, report version |
| Connector / table format | Iceberg, Hive/Parquet, Delta, Hudi, memory/native, Postgres | DDL/registration for that engine, engine-specific properties |
| Catalog | Iceberg REST (Polaris/Lakekeeper/fixture), Hive Metastore, Glue | Container + connection properties |
| Storage | SeaweedFS/Garage (S3), local FS, real S3 | Container, credentials, I/O metrics |
| Benchmark | TPC-H, TPC-DS, ClickBench, SSB | Schema, data generation, canonical queries, reference answers |

"Adding a connector" therefore means: a small module that knows how an engine creates or
attaches tables in that format, plus a docker-compose fragment if it needs a service.

### 3.2 Engine adapter interface (sketch)

```python
class Engine(Protocol):
    name: str                       # "trino"
    sql_dialect: str                # SQLGlot dialect name: "trino", "spark", "duckdb"

    def environment(self, ctx) -> ComposeFragment: ...   # services, configs, resource limits
    def version(self) -> EngineVersion: ...              # release or git SHA, image digest
    def connect(self) -> Session: ...
    def supports(self, connector: str) -> bool: ...

class Session(Protocol):
    def execute(self, sql: str, tag: str) -> QueryHandle: ...   # tag = "tpch-q01-rep3"
    def fetch_result(self, h) -> pyarrow.Table: ...
    def native_stats(self, h) -> dict: ...                      # engine-specific, mapped to common schema
    def explain(self, sql: str) -> str: ...                     # for plan diffing
```

### 3.3 Queries and translation

- Store each query once in a **canonical dialect** (the TPC spec text, generated with
  `qgen`/`dsqgen` using fixed seeds and the spec's validation substitution parameters).
- Translate per engine with SQLGlot at run time.
- Allow **per-engine overrides** (`queries/tpcds/overrides/<engine>/q14.sql`) when
  translation fails or an engine needs a semantic workaround. Overrides are listed in
  the report so readers can see where an engine got special treatment.
- Store the translated SQL in results so every number is traceable to exact SQL.
- Known trap: Trino's existing TPC-H q11 uses a constant only valid at SF1
  ([trino#9790](https://github.com/trinodb/trino/issues/9790)). Substitution parameters
  must depend on scale factor.

### 3.4 Correctness

- TPC-H SF1 and TPC-DS SF1: compare against official answer sets.
- Other scale factors and all cross-engine runs: compare result sets across engines with a
  reference engine (DuckDB is cheap and reliable), with rules for row order, float
  tolerance, decimal scale and NULL ordering.
- Status per query: `ok`, `wrong_result`, `error`, `timeout`, `unsupported`.

### 3.5 Metrics

Common schema per query execution, filled as far as each engine allows:

| Group | Metrics | Source |
|---|---|---|
| Time | wall, planning, queued, execution, CPU, scheduled | Harness clock + engine stats |
| Memory | peak memory, spilled bytes | Engine stats, container cgroup |
| Engine I/O (self-reported) | physical input bytes/rows, processed rows, output rows | Engine stats |
| **Storage I/O (independent)** | GET requests, bytes transferred, range-read sizes, LIST/HEAD calls, per-file access | Object-store access log or a logging S3 proxy in front of storage |
| **Iceberg planning / pruning** | manifests scanned/skipped, data files scanned/skipped, delete files, planning time | Iceberg ScanReport (REST `/metrics` or reporter), engine plan output |
| Container | CPU seconds, max RSS, network bytes | `docker stats` / cgroup files |
| Plan | normalized EXPLAIN text + hash | Engine `EXPLAIN` |

**Storage I/O measured at the storage layer** is the key design choice for comparing
engines fairly: it does not depend on what each engine chooses to report. Put a small
proxy (or use the object store's request log) between all engines and storage, tag
requests by run/query (separate access keys or a query-tag header where supported, or
time windows when queries run serially), and aggregate bytes and file paths per query.

**Pruning evaluation:**

1. For each query, extract the scan predicates per table (SQLGlot can do this from the
   canonical query).
2. Compute the "ideal" file set with PyIceberg `scan(row_filter=...).plan_files()`,
   which uses manifest partition values and column min/max stats.
3. Compare with the files each engine actually opened (from the storage log).
   Files read beyond the ideal set = missed pruning. Bytes read per file vs. columns
   needed = column projection and row-group/page skipping efficiency.
4. Across engines, the smallest observed file set is also a useful practical lower bound.

To make pruning measurable at all, the Iceberg dataset layout needs realistic
partitioning and sorting (for example TPC-DS fact tables partitioned by date key, TPC-H
`lineitem` sorted by `l_shipdate`). Layout variants become part of the benchmark config.

### 3.6 Results and history

- One JSON (or Parquet) file per run with the schema above plus environment metadata.
- Stored in a separate `results` branch or repository, so history is a plain git log and
  the site can be rebuilt from it at any time.
- Optional later sinks: Bencher or conbench for regression detection services.

### 3.7 Report

- Static site on GitHub Pages (like ClickBench): per-release trend charts per query,
  engine comparison tables, per-query drill-down with SQL, plan diff, metrics and
  storage I/O.
- PR mode: a Markdown summary (posted as a comment or job summary) with per-query
  deltas, confidence intervals, plan changes, and bytes/files read changes.
- Generated with Jinja2 + a charting library (Vega-Lite or Plotly), no server.

---

## 4. Statistics and noise

Standard GitHub runners are noisy (reports of 20-50% run-to-run variance;
see [Nyrkiö](https://github.com/nyrkio/nyrkio) and the
[Diesel case study](https://bencher.dev/learn/case-study/diesel/)). Mitigations:

- **A/B on the same machine in one job.** For a PR, run base and head on the same runner,
  interleaved (A B A B ...), never compare against a stored number from another machine.
- Warm-up runs discarded, then N repetitions (start with 5), report median and a
  bootstrap confidence interval; flag a change only when the interval excludes zero and
  the effect is above a threshold.
- Separate cold-cache and warm-cache phases; disable engine result/file caches unless
  the cache itself is under test.
- Prefer **CPU time, bytes read, files read, rows processed and plan hash** as the
  primary PR signals. They barely change between identical runs, so a change there is a
  real change.
- Fixed resource limits per engine container (CPU and memory via compose) so engines get
  equal resources in cross-engine comparisons.

---

## 5. Compute

| Option | Specs | Cost | Suitable for |
|---|---|---|---|
| GitHub-hosted standard runner, public repo | 4 vCPU, 16 GB RAM, ~14 GB SSD ([docs](https://docs.github.com/actions/reference/runners/github-hosted-runners)); disk can be enlarged by deleting preinstalled toolchains | Free, unlimited minutes for public repos, 6 h job limit | TPC-H SF1-SF10, TPC-DS SF1 (maybe SF10), single-node engines, correctness, deterministic metrics, A/B trends |
| GitHub larger runners | 4-64 vCPU | Paid; requires Team/Enterprise org | More stable numbers |
| Self-hosted runner on sponsored dedicated hardware (bare metal) | Any | Sponsor | Release-grade timing numbers, SF100+, multi-node clusters |
| Cloud credits (AWS/GCP/Azure open-source programs) | Any | Sponsor | Same, with real S3 |
| Local machine | Any | Free | Development, ad-hoc comparisons; same CLI |

Recommendation: start on free runners, treat their timing as trend-level and their
deterministic metrics as reliable. Design the harness so the same workflow runs on a
self-hosted runner later just by changing `runs-on`. Seek a sponsor once the project
shows value.

---

## 6. Automation

The harness lives in its own repo, not inside `trinodb/trino`, so it cannot react to
Trino PR events directly. Options:

- **Releases:** a scheduled workflow (daily) checks the latest `trinodb/trino` GitHub
  release / Docker Hub tag, and runs the release suite when a new one appears. Results
  appended to history, site rebuilt.
- **PRs, phase 1:** `workflow_dispatch` with inputs `repo`, `pr_number` (or two refs).
  The job builds Trino from the PR head and its merge base (`./mvnw -pl :trino-server -am
  -DskipTests` or a server tarball + docker image), runs the A/B suite, uploads the
  report as an artifact and job summary.
- **PRs, phase 2:** a scheduled poller that picks up Trino PRs carrying a label such as
  `performance`, or a GitHub App that listens for a `/bench` comment. Posting comments on
  trinodb/trino needs the maintainers' agreement, so the first version only publishes
  reports on our side.
- **Other engines:** same mechanism keyed on their releases (Spark, DuckDB, StarRocks...).

Building Trino from source on a 4-vCPU runner takes a while; cache the Maven repository
and measure early whether build + two-way benchmark fits comfortably in the 6-hour
limit. If not, split build and benchmark into separate jobs passing the image as an
artifact.

---

## 7. Proposed repository layout

```
bencholap/
  pyproject.toml
  src/bencholap/
    cli.py                 # bencholap run / compare / report / datagen
    config.py              # run matrix, YAML schema
    planner.py
    runner.py              # warmup, repetitions, A/B interleaving, timeouts
    stats.py               # medians, bootstrap CI, change detection
    validate.py            # result comparison
    results.py             # schema, read/write
    translate.py           # SQLGlot + overrides
    collectors/
      container.py         # cgroup / docker stats
      storage_proxy.py     # S3 access aggregation
      iceberg_metrics.py   # ScanReport ingestion, PyIceberg ideal-file sets
    engines/
      trino/               # adapter.py, compose.yml, etc/ configs
      spark/
      duckdb/
    connectors/
      iceberg/             # per-engine DDL/registration
      hive/
    catalogs/
      iceberg_rest/
    storage/
      seaweedfs/
    benchmarks/
      tpch/                # schema.sql, queries/, answers/, params.py
      tpcds/
    report/
      templates/
  configs/                 # ready-made suites: pr-smoke.yml, release.yml, cross-engine.yml
  .github/workflows/
    ci.yml                 # harness unit tests
    release-bench.yml
    pr-bench.yml
    site.yml
  docs/
```

---

## 8. Roadmap

**Phase 0: decisions (days)**
Confirm the open questions in section 9, choose the license (Apache-2.0 matches Trino and Iceberg), create the repo skeleton.

**Phase 1: MVP, Trino + Iceberg, TPC-H (2-3 weeks)**
- docker compose: Trino single node, Iceberg REST catalog fixture, SeaweedFS.
- Data: `tpcgen-cli` → Parquet → loaded into Iceberg tables via Trino (`CREATE TABLE AS` from a Hive/Parquet staging catalog) at SF1.
- Runner: warmup + N reps, wall time + Trino query stats.
- Validation against TPC-H SF1 answers.
- Output: JSON results + one static HTML report.
- `bencholap compare --engine trino --version 47x --version 48x` works locally and in a `workflow_dispatch` GitHub workflow.

**Phase 2: release tracking + TPC-DS (2 weeks)**
- Scheduled release detection, results branch, GitHub Pages site with history over the last N Trino releases (backfill by running old images).
- TPC-DS SF1 with SF-aware substitution parameters.
- Plan capture and plan-diff in the report.

**Phase 3: PR mode (2 weeks)**
- Build Trino from a PR ref and its merge base, A/B interleaved on one runner, statistical comparison, Markdown summary.

**Phase 4: second and third engine + translation (2-3 weeks)**
- DuckDB (cheap, also serves as correctness oracle) and Spark (reads the same Iceberg tables through the same REST catalog).
- SQLGlot translation + overrides, cross-engine validation, cross-engine report.
- Engine admission checklist (runs TPC-H via SQL, reads Iceberg via REST catalog, passes validation).

**Phase 5: storage I/O and pruning (2-3 weeks)**
- S3 request logging per query, bytes/files read per engine.
- Iceberg ScanReport ingestion where engines send it.
- Partitioned/sorted layout variants, PyIceberg ideal-file computation, pruning efficiency in the report.

**Phase 6: breadth**
- More connectors (Hive/Parquet, Delta), more engines (StarRocks, Presto/Prestissimo, DataFusion), more benchmarks (ClickBench, SSB, JOB, LST-Bench-style Iceberg maintenance and write workloads), concurrency/throughput runs, multi-node clusters on sponsored hardware.

---

## 9. Decisions

Decided:

- **Canonical dialect:** TPC spec SQL is the source of truth. Engine-specific override
  files (starting with Trino SQL) are used only when translation or execution of the
  spec SQL fails, and every override is listed in the report.
- **Separate repository:** the project lives in its own repo, independent of Trino's CI.
  It reacts to Trino releases and PRs from the outside (see section 6).

Still open:

1. **New project vs. contributing to an existing one** (LakeBench or LST-Bench). Recommendation above: new, thin, reuse components.
2. **Harness language.** Recommendation: Python (SQLGlot, PyIceberg, PyArrow, tpcgen-cli and report tooling are all Python). Engines are accessed over their native protocols (Trino REST client, Spark Connect, DuckDB in-process or as container).
3. **Data loading path for Iceberg.** Load once with one engine (or PyIceberg) and let all engines read the same tables (fair read comparisons), and separately benchmark each engine's own write path.
4. **Compute sponsor.** Who to approach and when (after the Phase 2 site exists is a good moment).

## 10. Early experiment: is storage I/O different between engines?

Before investing in Phase 5, run a cheap check in Phase 1-2: Trino and Spark read the
same Iceberg TPC-H SF1 tables through the logging proxy, and we compare GET count,
bytes, and files per query. Run it on two layouts: plain (unpartitioned, unsorted) and
pruning-friendly (`lineitem`/`orders` sorted or partitioned by date). Expected outcome:
small byte differences on full scans of the plain layout, and visible differences in
request count and in selective, join-heavy queries on the sorted layout. If even the
sorted layout shows nothing, Phase 5 gets cut down to request counts only.


## 11. Implementation status (first iteration)

Decisions taken: Python harness; tables written once and read by every target; TPC spec
SQL is canonical with Trino overrides only where needed; separate repository; published
images preferred over builds.

Findings that shaped the implementation:

- **TPC-DS query parameters.** `dsqgen -qualify` only orders queries; it still draws
  random substitution values, so its output does not match the official answer sets. The
  canonical TPC-DS queries are therefore rendered from the kit templates with the
  qualification parameters of the specification (v2.10.0 Appendix B, shipped in the kit),
  by `scripts/generate-queries/tpcds_qualification.py`. Parameters were cross-checked
  against DuckDB's TPC-DS queries. TPC-H uses `qgen -d` per scale factor (Q11 depends on SF).
- **Overrides.** Trino needs 1 TPC-H override (Q15: no column list in CREATE VIEW, CTE
  form instead) and 14 TPC-DS overrides: implicit varchar-to-date coercion, `date + int`,
  an out-of-scope `v1.` reference in Q47/Q57's ORDER BY, and integer division in Q21, Q34,
  Q73, Q78 and Q83 (Trino truncates `int / int`; the official answers assume exact division,
  so the dividend is cast to decimal as in Trino's own benchmark queries). The division
  cases were found by the answer validation, not by planning.
- **Answer validation.** All 22 TPC-H answers match. For TPC-DS, two answers cannot be used
  with tpcgen-cli data (Q85, Q93: the generated `reason` table maps descriptions to
  different keys than the data behind the kit's answer set); they are marked
  `no-reference` with the reason, and still compared across configurations.
- **Validated layouts.** TPC-H: unpartitioned CTAS (Trino benchto). TPC-DS: unpartitioned
  (Trino benchto) or fact tables identity-partitioned by their date key (LST-Bench Trino
  scripts and Databricks spark-sql-perf agree on the same seven columns). No published
  setup using sorting or bloom filters for these benchmarks was found; the layout model
  supports `sorted_by` and `bloom_filter_columns`, but such layouts must be marked
  `validated: false` until a source exists.
- **Version-specific catalog settings.** Iceberg REST catalog from Trino 405; S3 via legacy
  `hive.s3.*` before 440, `fs.native-s3.enabled` 440-480, `fs.s3.enabled` from 481 (legacy
  removed). The 484 image also enables a 2 GB file system memory cache in its default
  `config.properties`; reports list such differences per configuration.
- **Sweeps.** `bencholap sweep --every 10` currently resolves to 484, 474, ..., 414. All
  versions run in one job on one machine, so they are comparable with each other.

Shared runs (first GitHub runs, November 2026): benchmark requests come from an issue form
(approved by a maintainer with a label) or the workflow form; they can only choose reviewed
cluster profiles, presets and variants. Results go to the `results` branch and the site at
https://shohamyamin.github.io/bencholap/. A sweep of every 10th release (414..484) on one
GitHub runner showed TPC-H SF1 getting about 29% faster (geomean) from 414 to 484.

Not done yet (next steps): storage-level request logging and pruning analysis (section
3.5), a second engine (DuckDB or Spark via SQLGlot translation), Iceberg ScanReport
collection, TPC-DS full validation run, and dedicated hardware.
