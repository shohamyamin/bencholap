# bencholap

Engine-agnostic benchmark harness for analytical query engines and table formats.
It runs standard TPC-H and TPC-DS derived workloads against engines that all read the
**same Iceberg tables** through the same REST catalog and object storage, records much more
than wall time, validates results against the official TPC answer sets, and publishes
reports to a static site.

Trino (and its Iceberg connector) is the first engine. Adding an engine means adding a
plugin under `src/bencholap/engines/`; datasets, queries, validation, statistics, reports
and the site are shared.

> Results are derived from TPC-H / TPC-DS and are not comparable to published TPC results.

**Results site:** https://shohamyamin.github.io/bencholap/ ·
**Benchmark your change:** [open a benchmark request](https://github.com/shohamyamin/bencholap/issues/new?template=benchmark.yml)
(a maintainer approves it, it runs on GitHub, results come back to the issue) ·
**Guide:** [docs/how-to.md](docs/how-to.md)

## What it does

- **Standard workloads, unchanged.** Canonical queries come from the official generators:
  TPC-H `qgen -d` (validation parameters) and the TPC-DS kit templates rendered with the
  specification's qualification parameters (Appendix B). Only mechanical, documented
  normalizations are applied (see the header of every query file). Engines that cannot run
  a canonical query use an explicit override file with a stated reason; every override
  used is shown in the report.
- **Validated table layouts.** Tables are built exactly like published setups and the
  source is recorded: unpartitioned CTAS (Trino's own benchmark setup) and date-partitioned
  TPC-DS fact tables (LST-Bench, Databricks spark-sql-perf). `bencholap layouts` lists them.
- **Write once, read by everyone.** Data is generated with `tpcgen-cli` (byte-identical to
  dbgen/dsdgen), loaded once by a pinned Trino into Iceberg, and then read by every engine
  and version under test.
- **Any Trino build.** Releases, any image, a tarball, any fork + branch/tag/commit, or a
  pull request. Published images are used whenever possible; anything else is built once
  from source and cached by commit.
- **Version-aware configuration.** Trino renames catalog properties between releases
  (for example `hive.s3.*` → `fs.native-s3.enabled` → `fs.s3.enabled`). Version profiles in
  `src/bencholap/engines/trino/profiles.yaml` pick the right settings per version, and run
  configs can add or remove properties per target and per variant.
- **Variants.** Run the same targets with and without specific settings (session
  properties, catalog properties, `config.properties`).
- **Metrics.** Wall time, CPU, scheduled time, planning time, physical input bytes/rows per
  query and per table, peak memory, spill, the distributed plan (and whether it changed),
  result fingerprints, and validation status.
- **Reports and site.** One self-contained HTML report and a Markdown summary per run;
  a static site with release history, latest release and all runs. Every report shows the
  settings that differ between configurations.
- **Clusters.** Single node by default; a coordinator plus workers in docker; or any real
  infrastructure through a deploy/teardown command (an example for the Trino Helm chart is in
  `deploy/kubernetes/`), with external S3 and Iceberg REST catalog.
- **Honest comparisons.** Each run records a machine fingerprint. Timings are only put side
  by side for the same machine class. A sweep runs many versions in one job, so they share
  a machine.

## Running locally (development)

Not needed for benchmarking a change (use an issue). Requirements: Docker, [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run bencholap stack up                                  # SeaweedFS (S3) + Iceberg REST catalog
uv run bencholap dataset build -b tpch --sf 1              # generate + load once (~2 min)
uv run bencholap run configs/smoke.yaml                    # 3 queries, 1 repetition
uv run bencholap compare 483 484 -n 5 --rounds 2           # full TPC-H, 483 is the baseline
```

Results go to `results/<run_id>/{result.json,report.html,summary.md}`.

### Targets

| form | meaning |
|---|---|
| `484`, `release:484`, `latest` | official image `trinodb/trino:<n>` |
| `image:ghcr.io/me/trino:tag` | any image |
| `tarball:<url-or-path>` | a `trino-server-*.tar.gz` placed on an official image |
| `github:<owner>/<repo>@<ref>` | fork + branch / tag / commit |
| `git:<clone-url>@<ref>`, `https://github.com/<o>/<r>/tree/<ref>` | any git remote |
| `pr:<n>`, `pr:<owner>/<repo>#<n>` | pull request head commit (default repo trinodb/trino) |
| `pr-base:<n>` | merge base of that pull request |

Source builds run Maven inside the closest older release image (so the JDK matches) and
overlay the built `lib/` and `plugin/` onto that image.

### Commands

```
bencholap stack up|down|export FILE|import FILE
bencholap dataset build -b tpch|tpcds --sf N [--layout NAME] [--loader 484]
bencholap dataset list
bencholap layouts
bencholap targets resolve SPEC...
bencholap targets releases --every 10           # versions for a sweep
bencholap queries -b tpcds -m 'avg\s*\('         # which queries a selection runs
bencholap check-sql -b tpcds -t latest          # plan all queries on empty tables
bencholap run CONFIG.yaml [-q q01,q06] [-m REGEX] [-n 5] [--rounds 2]
bencholap compare BASE HEAD... [-b tpcds] [--sf 10] [--layout date-partitioned] [-m REGEX]
                  [--variants FILE] [--workers N | --cluster FILE]
bencholap sweep --every 10 [--from 405] [--to latest]
bencholap report RESULT.json [OTHER.json ...] [--markdown summary.md]
bencholap publish RUN_DIR --results-repo PATH   # a checkout of the results branch
bencholap profiles list|check
bencholap site build --results PATH --out _site
```

See `configs/example-compare.yaml` for a complete run config with per-target catalog
overrides and variants.

## Automation (GitHub Actions)

Nobody needs to run anything locally. To benchmark a change, open a **Benchmark request**
issue; a maintainer approves it with the `benchmark: approved` label; the run happens on
GitHub; the results are posted back to the issue and published on the results site
(GitHub Pages). Details: [docs/how-to.md](docs/how-to.md).

Requests only choose from reviewed options (`src/bencholap/profiles/`): cluster profiles
(where Trino runs and how many nodes), repetition presets and settings variants. New options
are added by pull request.

| workflow | trigger | what |
|---|---|---|
| `issue-benchmark.yml` | issue opened / edited / labeled | parse and validate the form, comment, run after approval |
| `benchmark.yml` | form (maintainers) / called | validate, run on the profile's runner, publish, report back |
| `release-watch.yml` | daily | new Trino release vs previous, TPC-H + TPC-DS |
| `sweep.yml` | form (maintainers) | releases every N versions in one job |
| `site.yml` | after publishing | build the site from the `results` branch and deploy Pages |
| `ci.yml` | push / PR | lint, profile choices, plan every query on the latest Trino |

Results are stored as `runs/<run_id>/result.json` on the `results` branch, so the site can
always be rebuilt and anyone can analyze the raw data. Getting dedicated hardware:
[docs/funding.md](docs/funding.md).

## Repository layout

```
src/bencholap/
  benchmarks/{tpch,tpcds}/   benchmark.yaml (tables, scale factors, validated layouts),
                             queries/, answers/, overrides/<engine>/, schema.yaml
  engines/trino/             target resolution, version profiles, engine plugin
  stack.py dataset.py        shared storage/catalog, dataset build
  runner.py validate.py      execution, metrics, plans, answer validation
  stats.py report/ site.py   statistics, HTML/Markdown reports, static site
scripts/generate-queries/    regenerate canonical queries from the official TPC tools
scripts/make_trino_overrides.py
docs/                        how-to.md, funding.md, research-and-plan.md
src/bencholap/profiles/      cluster profiles, presets, variants (reviewed choices)
deploy/kubernetes/           example deployer for multi-node profiles
```

## Adding an engine

1. Add `src/bencholap/engines/<name>/` exposing `ENGINE` with `resolve()` and `start()`
   (see `engines/base.py`), and register it in `engines/__init__.py`.
2. Point it at the shared Iceberg REST catalog (`stack.STACK`).
3. Run `bencholap check-sql -b tpch -t <target> --engine <name>`; add overrides under
   `benchmarks/<b>/overrides/<name>/` only where needed, each with a `-- reason:` line.
   SQLGlot can translate the canonical SQL for engines whose dialect differs.
