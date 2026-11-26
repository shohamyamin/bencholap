# How to benchmark a change

You do not need to run anything locally. Everything happens on GitHub.

## 1. Open a benchmark issue

Go to **Issues → New issue → Benchmark request** and fill in the form:

| field | example (an `avg` optimization) |
|---|---|
| Baseline | `pr-base:12345`, or `github:trinodb/trino@<commit your branch started from>` |
| Change | `pr:12345`, or `github:you/trino@faster-avg` |
| Benchmark | `tpcds` (more `avg` variety than TPC-H) |
| Scale factor | `1` |
| Cluster profile | `gh-standard` |
| Repetitions | `standard` |
| Query filter | `avg\s*\(` (27 TPC-DS queries) |

**Table layouts** (pick one or more; every target runs on each): `unpartitioned` is the
published setup for every benchmark; TPC-DS also has the published `date-partitioned`. To see how
a Trino version deals with organized data, add bencholap layouts:

| benchmark | layout | what it tests |
|---|---|---|
| TPC-H | `date-sorted` | lineitem/orders sorted by date: min/max row-group pruning |
| TPC-H | `date-partitioned` | monthly partitions: partition pruning at planning time |
| TPC-H | `key-bloom-filters` | bloom filters on join keys, used by dynamic filters |
| ClickBench | `small-row-groups` | control: 4 MB row groups only (sorted and bloom-filters use the same size) |
| ClickBench | `sorted` | ClickBench's primary key order: row-group pruning for CounterID / EventDate filters |
| ClickBench | `date-partitioned` | daily partitions: Q36-Q42 date ranges |
| ClickBench | `bloom-filters` | UserID / URLHash / RefererHash point lookups (Q19, Q40, Q41) |

In the report, pick the metrics "Data files scanned", "Manifests skipped", "Bytes read from
storage" or "Input rows" to see the pruning, not only the time.

Accepted targets: a release (`484`), a published image (`image:ghcr.io/you/trino:tag`), a fork
branch or commit (`github:you/trino@branch`, or the GitHub URL of a branch or commit), a pull
request (`pr:N`) and its merge base (`pr-base:N`). Compare against the commit your change is
based on: a release contains hundreds of unrelated changes.

A bot comments what will run, or what is wrong (edit the issue to fix it).

## 2. A maintainer approves

A maintainer adds the label `benchmark: approved`. Approval is required because branches and
pull requests are built and run on the project's runners. Editing the issue afterwards removes
the approval.

## 3. Results come back to the issue

The bot comments when the run starts (with a link to the workflow) and when it finishes:
the summary table, significant per-query changes, failures, and a link to the full report on
the results site, for example `https://<owner>.github.io/bencholap/runs/<run_id>/index.html`,
and closes the issue. A failed run leaves the issue open (label `benchmark: failed`); fix the
request and re-approve it.

Building a branch or PR from source takes a long time on a free runner. If you publish an
image of your branch and use `image:...`, nothing is built.

Maintainers can also start runs directly: **Actions → benchmark → Run workflow** (same fields).

## Reading the report

- **Verdict**: the geometric mean of per-query wall-time ratios, with counts of significant
  improvements and regressions, and whether every query succeeded and matched the official
  TPC answers.
- **Totals**: any metric summed over the queries that succeeded everywhere (wall, CPU,
  scheduled, planning, input bytes and rows, peak memory, spill, exchange data, ...), as a
  chart and a table with the change against the baseline.
- **Per query**: pick a metric and a configuration; the chart shows the % change per query
  with its 95% interval (green and red are significant) or the absolute values. The table
  below sorts by any column and filters by query, significance and problems.
- **Query details** (click a query): every metric side by side, every measured run, the two
  query plans with changed lines highlighted, and the SQL.
- **Settings that differ**: what the effective configuration changed between configurations.

On shared GitHub runners, trust CPU time, input bytes and plan changes more than small wall-time
differences.

## Exploring results

- **Runs**: every published run; filter by benchmark, profile and kind, sort by change,
  improvements, regressions or total time.
- **Explore queries**: every query of every comparison; find the biggest improvements and
  regressions, filter by plan changes, and see the distribution of changes.
- `data/runs.json` and `data/queries.json` on the site hold the same data for your own analysis.

## Cluster profiles

Requests choose a reviewed cluster profile; nobody sets worker counts, memory or Trino
properties in a request. Profiles live in `src/bencholap/profiles/clusters/`:

| profile | status | what it is |
|---|---|---|
| `gh-standard` | available | free GitHub runner, single node, 10 GB |
| `gh-distributed` | available | same runner, coordinator + 2 workers (distributed plans, not scaling) |
| `oci-a1-arm` | planned | Oracle Cloud Always Free Ampere A1 VM, dedicated |
| `large-vm` | planned | dedicated 32 vCPU / 128 GB VM |
| `k8s-4-workers` | planned | Kubernetes, coordinator + 4 workers, S3 + REST catalog |

To add a profile, open a pull request with a new file; maintainers review it. Settings
variants (`src/bencholap/profiles/variants/`) and repetition presets
(`src/bencholap/profiles/presets.yaml`) work the same way. CI checks that the workflow form
and the issue form list exactly the available choices (`bencholap profiles check`).

The machine class shown in reports includes the profile, so results from different profiles
are never compared or charted together. See [funding.md](funding.md) for getting the planned
hardware.

### How the planned profiles work

- `large-vm` / `oci-a1-arm`: a VM registered as a self-hosted runner with the profile's label.
  Same code path as GitHub runners.
- `k8s-4-workers`: a runner inside the cluster deploys each build with the official Trino Helm
  chart (`deploy/kubernetes/deploy.sh`), using the catalog files rendered for that version,
  and tears it down afterwards. Data lives in S3 with an Iceberg REST catalog
  (`BENCHOLAP_STACK=external`). Not exercised yet.

## Running locally (optional, for development)

```bash
uv sync
uv run bencholap stack up
uv run bencholap dataset build -b tpch --sf 1
uv run bencholap queries -b tpcds -m 'avg\s*\('          # list a selection
uv run bencholap compare 483 484 -q q01,q06 -n 2         # any targets, any options
```
