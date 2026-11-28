"""bencholap command line."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from pathlib import Path

import click
import yaml

from . import benchmarks, dataset, report, runconfig, site, stack
from .engines import get as get_engine
from .engines.trino import target as trino_target


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Debug logging.")
def main(verbose: bool) -> None:
    """Benchmark query engines on shared Iceberg tables with TPC-H / TPC-DS derived workloads."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")


# ---------------------------------------------------------------- stack
@main.group("stack")
def stack_cmd() -> None:
    """Shared storage + Iceberg REST catalog."""


@stack_cmd.command("up")
def stack_up() -> None:
    stack.up()


@stack_cmd.command("down")
def stack_down() -> None:
    stack.down()


@stack_cmd.command("export")
@click.argument("path", type=click.Path(path_type=Path))
def stack_export(path: Path) -> None:
    """Save all built datasets (storage + catalog state) to a tar file."""
    stack.export_state(path)


@stack_cmd.command("import")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def stack_import(path: Path) -> None:
    """Restore datasets saved with `stack export`."""
    stack.import_state(path)


# ---------------------------------------------------------------- datasets
@main.group("dataset")
def dataset_cmd() -> None:
    """Build benchmark datasets once into the shared Iceberg catalog."""


@dataset_cmd.command("build")
@click.option("--benchmark", "-b", default="tpch", show_default=True)
@click.option("--sf", default="1", show_default=True, help="Scale factor.")
@click.option("--layout", "-l", default=None, help="Validated layout (default: the benchmark's default).")
@click.option("--loader", default=dataset.DEFAULT_LOADER, show_default=True, help="Trino target that writes the tables.")
@click.option("--loader-memory", default="10g", show_default=True)
@click.option("--force", is_flag=True, help="Rebuild even if the dataset exists.")
@click.option("--keep-raw", is_flag=True, help="Keep the generated Parquet files.")
def dataset_build(benchmark, sf, layout, loader, loader_memory, force, keep_raw) -> None:
    m = dataset.build(benchmark, sf, layout, loader=loader, force=force, keep_raw=keep_raw,
                      resources={"memory": loader_memory})
    click.echo(f"{m['id']}: {sum(t['rows'] for t in m['tables'].values()):,} rows")


@dataset_cmd.command("list")
def dataset_list() -> None:
    for m in dataset.list_manifests():
        size = sum(t["data_bytes"] or 0 for t in m["tables"].values()) / 1e6
        click.echo(f"{m['id']:40s} {m['benchmark']} SF{m['scale_factor']} layout={m['layout']['name']} "
                   f"{size:.0f} MB loader=Trino {m['loader']['version']} built {m['built_at']}")


@main.command("layouts")
@click.option("--benchmark", "-b", default=None)
def layouts(benchmark) -> None:
    """Show the validated table layouts and their sources."""
    for name in [benchmark] if benchmark else benchmarks.available():
        b = benchmarks.load(name)
        click.echo(f"{b.title}  (scale factors: {', '.join(b.scale_factors())})")
        for lay in b.layouts.values():
            default = " (default)" if lay.name == b.default_layout else ""
            click.echo(f"  {lay.name}{default}  validated={lay.validated}  analyze={lay.analyze}")
            for t, tl in lay.tables.items():
                click.echo(f"      {t}: {tl.as_dict()}")
            for s in lay.sources:
                click.echo(f"      source: {s['name']} <{s['url']}>")


# ---------------------------------------------------------------- targets
@main.group("targets")
def targets_cmd() -> None:
    """Engine targets.

    \b
    Trino target forms:
      484 | release:484 | latest          official image trinodb/trino:<n>
      image:<ref>                        any image (e.g. a fork's published image)
      tarball:<url-or-path>              trino-server tarball on top of an official image
      github:<owner>/<repo>@<ref>        fork + branch / tag / commit (built if needed)
      git:<clone-url>@<ref>              any git remote
      https://github.com/<o>/<r>/tree/<ref>
      pr:<n> | pr:<owner>/<repo>#<n>     pull request head commit
      pr-base:<n>                        merge base of that pull request
    """


@targets_cmd.command("resolve")
@click.argument("specs", nargs=-1, required=True)
@click.option("--engine", default="trino", show_default=True)
def targets_resolve(specs, engine) -> None:
    for s in specs:
        t = get_engine(engine).resolve(s)
        click.echo(json.dumps(t.__dict__, indent=2))


@targets_cmd.command("releases")
@click.option("--every", default=10, show_default=True, help="Step between versions.")
@click.option("--from", "from_", type=int, default=None, help="Oldest version (default: oldest supported).")
@click.option("--to", default="latest", show_default=True, help="Newest version.")
def targets_releases(every, from_, to) -> None:
    """List release versions for a sweep, newest first."""
    click.echo(" ".join(map(str, sweep_versions(every, from_, to))))


def sweep_versions(every: int, from_: int | None, to: str) -> list[int]:
    from .engines.trino.config import load_profiles

    tags = trino_target.release_tags()
    newest = tags[-1] if to == "latest" else int(to)
    oldest = max(from_ or 0, load_profiles()["min_version"])
    wanted = list(range(newest, oldest - 1, -every))
    return [v for v in wanted if v in tags]


@main.command("queries")
@click.option("--benchmark", "-b", default="tpch", show_default=True)
@click.option("--sf", default="1", show_default=True)
@click.option("--match", "-m", default=None, help="Regex searched in the canonical SQL.")
@click.option("--engine", default="trino", show_default=True, help="Show overrides for this engine.")
@click.option("--show", is_flag=True, help="Print the SQL that would run.")
def queries_cmd(benchmark, sf, match, engine, show) -> None:
    """List the queries a selection would run, e.g. `bencholap queries -b tpcds -m 'avg\\s*\\('`."""
    bench = benchmarks.load(benchmark)
    for qid in runconfig.select_queries(bench, benchmarks.format_sf(sf), "all", match):
        q = bench.query(qid, sf, engine)
        click.echo(f"{qid}{'  [override: ' + q.override['reason'] + ']' if q.override else ''}")
        if show:
            click.echo(q.sql)


@main.command("check-sql")
@click.option("--benchmark", "-b", default="tpch", show_default=True)
@click.option("--target", "-t", default="latest", show_default=True)
@click.option("--engine", default="trino", show_default=True)
def check_sql(benchmark, target, engine) -> None:
    """Plan every query on empty tables (no data, no execution) to find needed overrides."""
    from . import sqlcheck

    results = sqlcheck.check(benchmark, target, engine)
    for r in results:
        mark = "ok " if r["status"] == "ok" else "ERR"
        click.echo(f"{mark} {r['query']}{' (override)' if r['override'] else ''} {r.get('error', '')}")
    sys.exit(1 if any(r["status"] != "ok" for r in results) else 0)


# ---------------------------------------------------------------- running
def _finish(result_path: Path) -> None:
    run_dir = result_path.parent
    report.write_report([result_path], run_dir / "report.html", run_dir / "summary.md")
    summary = (run_dir / "summary.md").read_text()
    click.echo(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(summary + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"run_dir={run_dir}\nrun_id={run_dir.name}\n")
    click.echo(f"report: {run_dir / 'report.html'}")


def _execute(cfg_dict: dict, output: Path, build_dataset: bool) -> None:
    from . import runner

    cfg = runconfig.from_dict(cfg_dict)
    # Preparation (pulling or building every target, building datasets) runs in parallel; it
    # finishes before the first measurement, so it cannot affect the results.
    # Source builds need most of the CPU and memory, so they run alone and one at a time;
    # image pulls overlap with the dataset build.
    import re as _re
    from concurrent.futures import ThreadPoolExecutor

    def is_pull(t) -> bool:
        return bool(_re.fullmatch(r"(?:latest|(?:release:|trino:)?\d+|image:.+)", t.source.strip()))

    for t in cfg.targets:
        if not is_pull(t):
            get_engine(t.engine).resolve(t.source)
    with ThreadPoolExecutor(max_workers=len(cfg.targets) + 1) as pool:
        jobs = [pool.submit(get_engine(t.engine).resolve, t.source) for t in cfg.targets if is_pull(t)]
        if build_dataset:
            loaders = {key: t.source for key in cfg.layouts if (t := cfg.dataset_loader(key))}
            jobs.append(pool.submit(dataset.build_many, cfg.benchmark, cfg.scale_factor, cfg.layouts, loaders))
        for j in jobs:
            j.result()
    _finish(runner.run_benchmark(cfg, output))


_run_options = [
    click.option("--output", "-o", type=click.Path(path_type=Path), default=Path("results"), show_default=True),
    click.option("--queries", "-q", default=None, help="Comma-separated subset, e.g. q01,q06."),
    click.option("--match", "-m", default=None,
                 help="Only queries whose canonical SQL matches this regex, e.g. 'avg\\s*\\('."),
    click.option("--warmup", type=int, default=None),
    click.option("--repetitions", "-n", type=int, default=None),
    click.option("--rounds", type=int, default=None),
    click.option("--build-dataset", is_flag=True, help="Build the dataset first if it is missing."),
]


def run_options(f):
    for opt in reversed(_run_options):
        f = opt(f)
    return f


def _apply(d: dict, queries, warmup, repetitions, rounds, match=None) -> dict:
    for k, v in (("queries", queries), ("warmup", warmup), ("repetitions", repetitions), ("rounds", rounds),
                 ("match", match)):
        if v is not None:
            d[k] = v
    return d


@main.command("run")
@click.argument("config", type=click.Path(exists=True, path_type=Path))
@run_options
def run_cmd(config, output, queries, match, warmup, repetitions, rounds, build_dataset) -> None:
    """Run a benchmark described by a YAML run config (see configs/)."""
    d = _apply(yaml.safe_load(config.read_text()), queries, warmup, repetitions, rounds, match)
    _execute(d, output, build_dataset)


def _compare_dict(targets, benchmark, sf, layout, memory, cpus, variants, name, kind, workers=0,
                  cluster_file=None) -> dict:
    cluster = yaml.safe_load(Path(cluster_file).read_text()) if cluster_file else {"type": "docker"}
    cluster = cluster.get("cluster", cluster)
    if workers:
        cluster["workers"] = workers
    d: dict = {"name": name, "kind": kind, "benchmark": benchmark, "scale_factor": sf, "layout": layout,
               "cluster": cluster,
               "resources": {k: v for k, v in (("memory", memory), ("cpus", cpus)) if v},
               "targets": [{"name": f"t{i}-{t.split('@')[-1].split(':')[-1].split('/')[-1]}"[:40], "source": t}
                           for i, t in enumerate(targets)]}
    if variants:
        extra = yaml.safe_load(Path(variants).read_text())
        d["variants"] = extra["variants"] if isinstance(extra, dict) else extra
    return d


_compare_options = [
    click.option("--benchmark", "-b", default="tpch", show_default=True),
    click.option("--sf", default="1", show_default=True),
    click.option("--layout", "-l", default=None),
    click.option("--memory", default="10g", show_default=True, help="Engine container memory limit."),
    click.option("--cpus", default=None, help="Engine container CPU limit."),
    click.option("--workers", type=int, default=0, show_default=True,
                 help="Worker nodes besides the coordinator (docker cluster on this host)."),
    click.option("--cluster", "cluster_file", type=click.Path(exists=True), default=None,
                 help="YAML with a cluster section (type: docker | command | external)."),
    click.option("--variants", type=click.Path(exists=True), default=None,
                 help="YAML file with a list of variants (config/catalog/session overrides)."),
    click.option("--name", default=None),
]


@main.command("compare")
@click.argument("targets", nargs=-1, required=True)
@click.option("--kind", default="manual", show_default=True, help="Recorded run kind: manual, pr, release, sweep.")
@run_options
def compare_cmd(targets, kind, output, queries, match, warmup, repetitions, rounds, build_dataset, **kw) -> None:
    """Compare targets, e.g. `bencholap compare 483 github:me/trino@my-branch`. The first is the baseline."""
    d = _compare_dict(targets, kw["benchmark"], kw["sf"], kw["layout"], kw["memory"], kw["cpus"],
                      kw["variants"], kw["name"] or " vs ".join(targets), kind, kw["workers"], kw["cluster_file"])
    _execute(_apply(d, queries, warmup, repetitions, rounds, match), output, build_dataset)


for _opt in reversed(_compare_options):
    compare_cmd = _opt(compare_cmd)


@main.command("sweep")
@click.option("--every", default=10, show_default=True, help="Step between release versions.")
@click.option("--from", "from_", type=int, default=None, help="Oldest version.")
@click.option("--to", default="latest", show_default=True, help="Newest version.")
@run_options
def sweep_cmd(every, from_, to, output, queries, match, warmup, repetitions, rounds, build_dataset, **kw) -> None:
    """Run many releases (newest, newest-10, ...) in ONE run on one machine so they are comparable."""
    versions = sweep_versions(every, from_, to)
    click.echo(f"sweeping Trino releases: {' '.join(map(str, versions))}")
    d = _compare_dict([str(v) for v in sorted(versions)], kw["benchmark"], kw["sf"], kw["layout"], kw["memory"],
                      kw["cpus"], kw["variants"], kw["name"] or f"Trino releases every {every}: "
                      f"{min(versions)}..{max(versions)}", "sweep", kw["workers"], kw["cluster_file"])
    for t, v in zip(d["targets"], sorted(versions)):
        t["name"] = f"trino-{v}"
    _execute(_apply(d, queries, warmup, repetitions, rounds, match), output, build_dataset)


for _opt in reversed(_compare_options):
    sweep_cmd = _opt(sweep_cmd)


# ---------------------------------------------------------------- reports & site
@main.command("report")
@click.argument("results", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--html", "out_html", type=click.Path(path_type=Path), default=Path("report.html"), show_default=True)
@click.option("--markdown", "out_md", type=click.Path(path_type=Path), default=None)
@click.option("--baseline", default=None, help="Configuration id to compare against (default: first).")
def report_cmd(results, out_html, out_md, baseline) -> None:
    """Render one result file, or several merged for comparison."""
    report.write_report(list(results), out_html, out_md, baseline)
    click.echo(f"wrote {out_html}" + (f" and {out_md}" if out_md else ""))


@main.command("publish")
@click.argument("run_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--results-repo", type=click.Path(file_okay=False, path_type=Path), required=True,
              help="Checkout of the results repository.")
def publish(run_dir: Path, results_repo: Path) -> None:
    """Copy a run (result.json + summary.md) into a results repository checkout."""
    dest = results_repo / "runs" / run_dir.name
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("result.json", "summary.md"):
        if (run_dir / name).exists():
            shutil.copy(run_dir / name, dest / name)
    click.echo(f"published {run_dir.name} to {dest}")


@main.group("site")
def site_cmd() -> None:
    """Static results site."""


@site_cmd.command("build")
@click.option("--results", "results_dir", type=click.Path(exists=True, file_okay=False, path_type=Path),
              required=True, help="Directory containing runs/<run_id>/result.json.")
@click.option("--out", type=click.Path(path_type=Path), default=Path("_site"), show_default=True)
@click.option("--repo", default=None, help="owner/name for links to the issue form (default: $GITHUB_REPOSITORY).")
def site_build(results_dir: Path, out: Path, repo: str | None) -> None:
    site.build(results_dir, out, repo)
    click.echo(f"site written to {out}/index.html")


# ---------------------------------------------------------------- requests (GitHub form / issues)
@main.group("request")
def request_cmd() -> None:
    """Validated benchmark requests: the only way shared (GitHub) runs are started."""


def _gh_output(**kv) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a") as f:
        for k, v in kv.items():
            v = str(v)
            if "\n" in v:
                f.write(f"{k}<<__EOF__\n{v}\n__EOF__\n")
            else:
                f.write(f"{k}={v}\n")


def _finish_request(req, out: Path) -> None:
    from . import request as rq

    out.mkdir(parents=True, exist_ok=True)
    (out / "request.json").write_text(req.to_json())
    status = "valid" if not req.errors else "invalid"
    comment = rq.describe(req)
    if req.errors:
        comment += "\n\n**Problems:**\n" + "\n".join(f"- {e}" for e in req.errors)
    (out / "request.md").write_text(comment + "\n")
    runner = None
    if not req.errors:
        from . import profiles

        runner = profiles.cluster(req.profile)["runner"]
    _gh_output(status=status, runner=runner or "", request=req.to_json(),
               dataset_key=f"dataset-{req.benchmark}-sf{req.scale_factor}-{'+'.join(sorted(req.layouts))}",
               dataset_prefix=f"dataset-{req.benchmark}-sf{req.scale_factor}-",
               # copies written by targets under test are rebuilt every run and stay out of the shared cache
               dataset_save="false" if req.loaders else "true")
    click.echo(comment)
    if req.errors:
        sys.exit(2)


@request_cmd.command("from-inputs")
@click.option("--out", type=click.Path(path_type=Path), default=Path("request"), show_default=True)
def request_from_inputs(out: Path) -> None:
    """Build a request from REQ_* environment variables (workflow form inputs)."""
    from . import request as rq

    e = os.environ
    targets = [e.get("REQ_BASELINE", ""), e.get("REQ_CHANGE", "")] + e.get("REQ_MORE_TARGETS", "").split()
    req = rq.validate(rq.Request(
        targets=[t for t in targets if t.strip()], benchmark=e.get("REQ_BENCHMARK", "tpch"),
        scale_factor=e.get("REQ_SCALE_FACTOR", "1"), profile=e.get("REQ_PROFILE", "gh-standard"),
        preset=e.get("REQ_PRESET", "standard"), queries=e.get("REQ_QUERIES") or "all",
        layouts=e.get("REQ_LAYOUTS", ""), loaders=e.get("REQ_LOADERS", ""),
        match=e.get("REQ_MATCH") or None,
        variants=None if e.get("REQ_VARIANTS", "none") in ("", "none") else e["REQ_VARIANTS"],
        publish=e.get("REQ_PUBLISH", "true") == "true", profile_mode=e.get("REQ_PROFILE_MODE") == "true",
        title=e.get("REQ_TITLE") or None,
        kind=e.get("REQ_KIND", "request"), requested_by=e.get("GITHUB_ACTOR"),
        issue=int(e["REQ_ISSUE"]) if e.get("REQ_ISSUE") else None,
    ))
    _finish_request(req, out)


@request_cmd.command("from-json")
@click.option("--out", type=click.Path(path_type=Path), default=Path("request"), show_default=True)
def request_from_json(out: Path) -> None:
    """Validate a request passed as JSON in REQ_JSON (used by workflows calling each other)."""
    from . import request as rq

    d = json.loads(os.environ["REQ_JSON"])
    d.pop("errors", None)
    _finish_request(rq.validate(rq.Request(**d)), out)


@request_cmd.command("sweep")
@click.option("--every", default=10, show_default=True)
@click.option("--from", "from_", type=int, default=None)
@click.option("--to", default="latest", show_default=True)
@click.option("--benchmark", "-b", default="tpch")
@click.option("--sf", default="1")
@click.option("--profile", default="gh-standard")
@click.option("--preset", default="standard")
@click.option("--layouts", default="", help="Comma-separated layouts (default: the benchmark's default).")
@click.option("--kind", default="sweep")
@click.option("--out", type=click.Path(path_type=Path), default=Path("request"), show_default=True)
def request_sweep(every, from_, to, benchmark, sf, profile, preset, layouts, kind, out) -> None:
    """Request for a release sweep (newest, newest-N, ...), oldest version as baseline.
    With --every 1 --kind release it compares the newest release with the previous one."""
    from . import request as rq

    versions = sorted(sweep_versions(every, from_, to))
    if kind == "release":
        versions = versions[-2:]
    title = (f"Trino {versions[-1]} vs {versions[0]} (new release)" if kind == "release"
             else f"Trino releases every {every}: {versions[0]}..{versions[-1]}")
    req = rq.validate(rq.Request(targets=[str(v) for v in versions], benchmark=benchmark, scale_factor=sf,
                                 profile=profile, preset=preset, kind=kind, title=title, layouts=layouts,
                                 requested_by=os.environ.get("GITHUB_ACTOR")))
    _finish_request(req, out)


@request_cmd.command("from-issue")
@click.option("--out", type=click.Path(path_type=Path), default=Path("request"), show_default=True)
def request_from_issue(out: Path) -> None:
    """Parse the benchmark issue form from ISSUE_BODY / ISSUE_TITLE / ISSUE_NUMBER / ISSUE_AUTHOR."""
    from . import request as rq

    e = os.environ
    req = rq.parse_issue(e.get("ISSUE_BODY", ""), e.get("ISSUE_TITLE"), int(e.get("ISSUE_NUMBER") or 0) or None,
                         e.get("ISSUE_AUTHOR"))
    _finish_request(req, out)


@request_cmd.command("run")
@click.argument("request_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=Path("results"), show_default=True)
def request_run(request_file: Path, output: Path) -> None:
    """Run a validated request (builds the dataset if needed)."""
    from . import request as rq

    req = rq.load(request_file)
    if req.errors:
        raise click.ClickException("; ".join(req.errors))
    _execute(rq.to_run_config(req), output, build_dataset=True)


@main.group("profiles")
def profiles_cmd() -> None:
    """Cluster profiles, presets and variants that requests can choose from."""


@profiles_cmd.command("list")
def profiles_list() -> None:
    from . import profiles

    for name, p in profiles.clusters().items():
        click.echo(f"{name:16s} {p['status']:9s} runner={p['runner']:20s} SF {p['scale_factors']}  {p['title']}")
    click.echo("presets: " + ", ".join(profiles.presets()))
    click.echo("variants: " + ", ".join(profiles.variants()))


@profiles_cmd.command("check")
@click.option("--repo-root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=Path("."))
def profiles_check(repo_root: Path) -> None:
    """Check that the workflow form and the issue form offer exactly the available choices."""
    from . import profiles

    expected = {
        "profile": [n for n, p in profiles.clusters().items() if p["status"] == "available"],
        "preset": list(profiles.presets()),
        "variants": ["none", *profiles.variants()],
    }
    wf = yaml.safe_load((repo_root / ".github/workflows/benchmark.yml").read_text())
    inputs = wf.get("on", wf.get(True))["workflow_dispatch"]["inputs"]
    form = yaml.safe_load((repo_root / ".github/ISSUE_TEMPLATE/benchmark.yml").read_text())
    form_opts = {b["id"]: [o.split()[0] for o in b["attributes"].get("options", [])]
                 for b in form["body"] if b.get("type") == "dropdown"}
    problems = []
    for key, want in expected.items():
        if inputs[key].get("options") != want:
            problems.append(f"benchmark.yml input {key}: {inputs[key].get('options')} != {want}")
        # GitHub issue forms reserve the option "None"; the form says "defaults" instead
        form_want = ["defaults" if w == "none" else w for w in want]
        if form_opts.get(key) != form_want:
            problems.append(f"issue form {key}: {form_opts.get(key)} != {form_want}")
    for b in form["body"]:
        for o in (b.get("attributes") or {}).get("options", []) or []:
            if str(o).strip().lower() == "none":
                problems.append(f"issue form {b.get('id')}: option 'None' is reserved by GitHub")
    for p in problems:
        click.echo(p)
    if problems:
        sys.exit(1)
    click.echo("workflow and issue form choices match the profiles")


if __name__ == "__main__":
    main()
