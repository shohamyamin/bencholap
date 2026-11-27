# bencholap

Benchmarks for analytical query engines on **Apache Iceberg tables**: standard TPC-H, TPC-DS and
ClickBench workloads, run against any Trino build (releases, forks, branches, pull requests),
with results checked against official answers, much more measured than wall time, and every run
published as an interactive report.

**Results site:** https://shohamyamin.github.io/bencholap/ ·
**Benchmark your change:** [open a benchmark request](https://github.com/shohamyamin/bencholap/issues/new?template=benchmark.yml) ·
**Guides:** [how to benchmark a change](docs/how-to.md) · [benchmarks, data and queries](docs/benchmarks.md) · [hardware and funding](docs/funding.md)

> Results are derived from TPC-H / TPC-DS / ClickBench and are not comparable to published results.

## Scope today

- **Table format: Iceberg only.** Every benchmark reads Iceberg tables (Parquet, format v2)
  through an Iceberg REST catalog on S3-compatible storage. Hive, Delta Lake or other
  connectors are not implemented yet.
- **Engine: Trino only.** The engine plugin interface (`src/bencholap/engines/base.py`) is
  engine-agnostic and everything else (data, queries, validation, reports) is shared, but Trino is
  the only plugin so far.
- **Benchmarks:** TPC-H (22 queries), TPC-DS (99) and ClickBench (43). What the data is, how it is
  loaded and what each query does: [docs/benchmarks.md](docs/benchmarks.md).

## How to run a benchmark

### 1. From an issue (recommended, no setup)

1. Open [a benchmark request](https://github.com/shohamyamin/bencholap/issues/new?template=benchmark.yml):
   baseline and change (release, image, fork branch or pull request), benchmark, scale factor,
   table layouts, cluster profile, repetitions, queries (`all`, `quick` or a list) and an optional
   query filter (regular expression, e.g. `avg\s*\(`).
2. A bot checks the request and comments what will run.
3. A maintainer adds the label `benchmark: approved`.
4. The run happens on GitHub; the bot posts the summary and a link to the report, and closes the issue.

### 2. From the Actions tab (maintainers)

Actions → **benchmark** → Run workflow, with the same fields. Other workflows: **sweep** (every Nth
release in one job), **release-watch** (daily, new release vs previous), see [Automation](#automation).

### 3. Locally (development)

Requirements: Docker and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run bencholap stack up                                   # SeaweedFS (S3) + Iceberg REST catalog
uv run bencholap dataset build -b tpch --sf 1               # generate + load once (~2 min)
uv run bencholap compare 483 484 -q quick -n 3              # quick subset, 483 is the baseline
uv run bencholap compare 483 484 -b tpcds --rounds 2        # full TPC-DS
uv run bencholap compare 484 github:me/trino@my-branch -m 'avg\s*\('   # queries using avg()
```

Results go to `results/<run_id>/{result.json,report.html,summary.md}`; open `report.html`.

## How it works

```
 request (issue / form / CLI)
   └─ validated: targets, benchmark, scale factor, layouts, profile, preset, queries
 prepare (in parallel, before any measurement)
   ├─ targets: pull the release image, or build the fork / PR once (mvnd) and cache it
   └─ datasets: generate or download raw Parquet → write Iceberg tables once per layout
      with a pinned Trino → ANALYZE only where the layout's source does it → manifest (cached)
 measure (one isolated Trino cluster per target × variant × layout, restarted every time)
   ├─ per query: warmup runs, measured runs, rounds alternate targets (A B A B)
   ├─ engine metrics from Trino's query info, the distributed plan, the result
   └─ results checked against the official answers (TPC-H, TPC-DS) or between configurations
 report: result.json + interactive HTML + Markdown summary → results branch → site
```

- **Canonical queries** are the official generator output (TPC-H `qgen -d`, TPC-DS kit templates
  with the specification's qualification parameters, ClickBench's own Trino queries). An engine
  that cannot run one uses an override file with a stated reason, shown in the report.
- **Write once, read by everyone:** all targets read the same Iceberg snapshot.
- **Version-aware configuration:** Trino renames catalog properties between releases; profiles in
  `src/bencholap/engines/trino/profiles.yaml` pick the right ones per version, and the report lists
  every effective setting that differs between configurations.

## Table layouts

Each benchmark has published setups (unpartitioned, as in Trino's and ClickBench's own setups;
date-partitioned TPC-DS facts as in LST-Bench and spark-sql-perf) and clearly marked **bencholap
layouts** to see how a Trino version deals with organized data:

| kind | TPC-H | ClickBench | what it tests |
|---|---|---|---|
| sorted | `date-sorted` | `sorted` | min/max row-group pruning |
| partitioned | `date-partitioned` | `date-partitioned` | partition pruning during planning |
| bloom filters | `key-bloom-filters` | `bloom-filters` | Parquet bloom filters for equality lookups |
| control | | `small-row-groups` | same row-group size as sorted / bloom, nothing else |

One request can run several layouts; every target runs on each, and the report compares any two
configurations (versions, variants or layouts). `bencholap layouts` lists them with their sources.

## What is measured

Per query and configuration, over the measured runs:

- wall time (with a 95% bootstrap interval per comparison), CPU, scheduled, planning and queued time
- physical input bytes and rows (also per table), processed rows, exchange data, peak memory, spill
- **Iceberg scan metrics** (recent Trino versions): data files and manifests scanned or skipped,
  bytes read from storage or from Trino's file cache, Parquet row-selection pushdowns, delete files,
  dynamic filters
- the distributed plan (and whether it changed), the result fingerprint, and validation status

## Making runs faster without changing the results

- **`quick` query subsets** (7 TPC-H, 10 TPC-DS, 10 ClickBench queries, one per main execution
  pattern) and the **`quick` preset** (1 warmup + 3 runs) give fast feedback while developing a
  feature; a **query filter** (e.g. `avg\s*\(`) runs only the queries that use what you changed.
- **Datasets are cached** between runs and shared across layout combinations; only missing or
  changed layouts are rebuilt.
- **Preparation runs in parallel** (image pulls overlap with the dataset build) and always finishes
  before the first measurement, so it cannot disturb timings.
- **Source builds use mvnd** (the Maven daemon, parallel builds) and a cached Maven repository;
  published images (`image:...`) avoid building at all.
- Measurement itself stays isolated: one fresh cluster per configuration, the same warmup and
  repetitions for every target, and alternating rounds.

## Automation

| workflow | trigger | what |
|---|---|---|
| `issue-benchmark.yml` | issue opened / edited / labeled | parse and validate the form, comment, run after approval |
| `benchmark.yml` | form (maintainers) / called | validate, prepare, run on the profile's runner, publish, report back |
| `release-watch.yml` | daily | new Trino release vs previous, TPC-H + TPC-DS |
| `sweep.yml` | form (maintainers) | releases every N versions in one job, so they are comparable |
| `site.yml` | after publishing / template changes | build the site from the `results` branch and deploy Pages |
| `ci.yml` | push / PR | lint, profile choices, plan every query on the latest Trino |

Requests only choose from reviewed options in `src/bencholap/profiles/`: **cluster profiles**
(where Trino runs, nodes, memory, allowed scale factors), **presets** (warmup / repetitions /
rounds) and **variants** (sets of settings). New ones are added by pull request. Results are
stored as `runs/<run_id>/result.json` on the `results` branch.

## Command reference

```
bencholap stack up|down|export FILE|import FILE
bencholap dataset build -b tpch|tpcds|clickbench --sf N [--layout NAME] [--loader 484]
bencholap dataset list
bencholap layouts [-b BENCHMARK]
bencholap queries -b tpcds [-m REGEX] [--show]      # which queries a selection runs
bencholap check-sql -b tpcds -t latest              # plan all queries on empty tables
bencholap targets resolve SPEC... | targets releases --every 10
bencholap run CONFIG.yaml [-q all|quick|q01,q06] [-m REGEX] [-n 5] [--rounds 2]
bencholap compare BASE HEAD... [-b tpcds] [--sf 10] [--layout L] [-q quick] [-m REGEX]
                  [--variants FILE] [--workers N | --cluster FILE]
bencholap sweep --every 10 [--from 405] [--to latest]
bencholap report RESULT.json [OTHER.json ...] [--markdown summary.md]
bencholap request from-inputs|from-issue|from-json|sweep|run    # used by the workflows
bencholap profiles list|check
bencholap publish RUN_DIR --results-repo PATH
bencholap site build --results PATH --out _site
```

Targets: `484` / `latest` (release image), `image:<ref>`, `tarball:<url-or-path>`,
`github:<owner>/<repo>@<ref>`, a GitHub tree/commit URL, `pr:<n>`, `pr-base:<n>` (merge base).
See `configs/example-compare.yaml` for a full run config.

## Repository layout

```
src/bencholap/
  benchmarks/<name>/      benchmark.yaml (tables, scale factors, layouts, subsets), queries/,
                          answers/, overrides/<engine>/, descriptions.yaml, schema.yaml
  engines/trino/          target resolution and builds, version profiles, engine plugin
  profiles/               cluster profiles, presets, variants (reviewed choices for requests)
  stack.py dataset.py     shared storage and catalog, dataset build
  runner.py validate.py   execution, metrics, plans, answer validation
  request.py              request parsing and validation (issues, forms)
  stats.py report/ site.py  statistics, reports, results site
scripts/                  query generation from the official tools, overrides, docs
deploy/kubernetes/        example deployer for multi-node profiles
docs/                     how-to, benchmarks, funding, research and plan
```

## Adding an engine or connector

1. Add `src/bencholap/engines/<name>/` exposing `ENGINE` with `resolve()` and `start()`
   (see `engines/base.py`) and register it in `engines/__init__.py`.
2. Point it at the shared Iceberg REST catalog (`stack.STACK`). Another table format needs a
   loader for it in `dataset.py` and a catalog section in the engine's profiles.
3. Run `bencholap check-sql -b tpch -t <target> --engine <name>` and add overrides under
   `benchmarks/<b>/overrides/<name>/` only where needed, each with a `-- reason:` line.

After changing benchmark definitions, regenerate `docs/benchmarks.md` with
`uv run python scripts/make_docs.py`.
