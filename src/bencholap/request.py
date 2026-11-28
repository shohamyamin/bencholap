"""Benchmark requests from the GitHub form or an issue: parse, validate, turn into a run.

Everything in a request is untrusted text. It is only ever read by this module (never
interpolated into shell commands) and every field is checked against a whitelist:
target syntax, benchmark, scale factor allowed by the cluster profile, preset and variant
names that exist in the repository, and a bounded query filter.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import benchmarks, profiles, runconfig

# Targets allowed in shared runs: releases, published images, GitHub forks/branches/commits
# and pull requests. Local paths and arbitrary URLs are not accepted.
_NAME = r"[A-Za-z0-9_.-]+"
_REF = r"[A-Za-z0-9_./-]+"
TARGET_PATTERNS = [
    r"latest",
    r"(?:release:|trino:)?\d{3,4}",
    rf"image:[a-z0-9.-]+(?::\d+)?(?:/{_NAME})+(?::{_NAME}|@sha256:[0-9a-f]{{64}})?",
    rf"github:{_NAME}/{_NAME}@{_REF}",
    rf"https://github\.com/{_NAME}/{_NAME}/(?:tree|commit)/{_REF}",
    rf"pr(?:-base)?:(?:{_NAME}/{_NAME}#)?\d+",
]
_TARGET_RX = re.compile("^(?:" + "|".join(TARGET_PATTERNS) + ")$")

BENCHMARK_LABELS = {"tpch": "tpch", "tpc-h": "tpch", "tpcds": "tpcds", "tpc-ds": "tpcds"}


class RequestError(ValueError):
    pass


@dataclass
class Request:
    targets: list[str]
    benchmark: str = "tpch"
    scale_factor: str = "1"
    profile: str = "gh-standard"
    preset: str = "standard"
    layouts: list[str] = field(default_factory=list)
    queries: str = "all"
    match: str | None = None
    variants: str | None = None
    publish: bool = True
    profile_mode: bool = False
    # which engines write the datasets: "default" (the pinned loader) and/or target roles
    # ("baseline", "change", "target2", ...); each one writes its own copy of every layout
    loaders: list[str] = field(default_factory=list)
    title: str | None = None
    description: str | None = None
    kind: str = "request"
    issue: int | None = None
    requested_by: str | None = None
    errors: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        d = asdict(self)
        d.pop("errors")
        return json.dumps(d)


def _none(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return None if v in ("", "_No response_", "None", "none", "-") else v


def validate(req: Request) -> Request:
    errs: list[str] = []
    req.targets = [t.strip() for t in req.targets if t and t.strip()]
    if not req.targets:
        errs.append("at least one target is required")
    for t in req.targets:
        if len(t) > 200 or not _TARGET_RX.match(t):
            errs.append(f"target `{t[:80]}` is not an accepted form (release number, `image:...`, "
                        "`github:owner/repo@ref`, a GitHub tree/commit URL, `pr:N`, `pr-base:N`)")
    req.benchmark = BENCHMARK_LABELS.get((req.benchmark or "").strip().lower().split(" ")[0], req.benchmark)
    if req.benchmark not in benchmarks.available():
        errs.append(f"unknown benchmark `{req.benchmark}`")
    try:
        prof = profiles.cluster(req.profile)
        if prof.get("status") != "available":
            errs.append(f"cluster profile `{req.profile}` is {prof.get('status')}: it has no hardware yet")
        req.scale_factor = benchmarks.format_sf(req.scale_factor)
        allowed = profiles.scale_factors(prof, req.benchmark)
        if req.scale_factor not in allowed:
            errs.append(f"profile `{req.profile}` supports scale factors {allowed} for {req.benchmark}, "
                        f"not {req.scale_factor}")
        if req.kind != "sweep" and len(req.targets) > prof.get("max_targets", 3):
            errs.append(f"profile `{req.profile}` allows at most {prof['max_targets']} targets")
    except (ValueError, TypeError) as e:
        errs.append(str(e))
    if req.preset not in profiles.presets():
        errs.append(f"unknown preset `{req.preset}`; choose one of {', '.join(profiles.presets())}")
    if req.variants and req.variants not in profiles.variants():
        errs.append(f"unknown variants `{req.variants}`; choose one of {', '.join(profiles.variants())}")
    if req.match:
        if len(req.match) > 100:
            errs.append("query filter is longer than 100 characters")
        else:
            try:
                re.compile(req.match)
            except re.error as e:
                errs.append(f"query filter is not a valid regular expression: {e}")
    if isinstance(req.layouts, str):
        req.layouts = [x for x in re.split(r"[,\s]+", req.layouts) if x]
    req.layouts = list(dict.fromkeys(req.layouts or []))
    if req.benchmark in benchmarks.available():
        bench = benchmarks.load(req.benchmark)
        req.layouts = req.layouts or [bench.default_layout]
        unknown = [x for x in req.layouts if x not in bench.layouts]
        if unknown:
            errs.append(f"{req.benchmark} has no layout {', '.join(f'`{x}`' for x in unknown)}; "
                        f"available: {', '.join(bench.layouts)}")
        if len(req.layouts) > 6:
            errs.append("at most 6 layouts per request")
    if isinstance(req.loaders, str):
        req.loaders = [x for x in re.split(r"[,\s]+", req.loaders) if x]
    req.loaders = list(dict.fromkeys(x.strip().lower() for x in req.loaders or [] if x.strip()))
    if req.loaders == ["default"]:
        req.loaders = []
    roles = loader_roles(len(req.targets))
    unknown = [x for x in req.loaders if x not in roles]
    if unknown:
        errs.append(f"unknown loaders {', '.join(f'`{x[:40]}`' for x in unknown)}; choose from {', '.join(roles)}")
    if len(req.loaders) > 3:
        errs.append("at most 3 loaders per request")
    if len(req.layouts or []) * max(1, len(req.loaders)) > 6:
        errs.append("at most 6 datasets (layouts x loaders) per request")
    if not errs:
        try:
            bench = benchmarks.load(req.benchmark)
            runconfig.select_queries(bench, req.scale_factor, req.queries or "all", req.match)
        except ValueError as e:
            errs.append(str(e))
    req.errors = errs
    return req


def loader_roles(target_count: int) -> list[str]:
    """Names a request can use in `loaders`: the pinned default loader or a target by role."""
    return ["default"] + [_role(i) for i in range(target_count)]


def _role(i: int) -> str:
    return "baseline" if i == 0 else "change" if i == 1 else f"target{i}"


def selected_queries(req: Request) -> list[str]:
    return runconfig.select_queries(benchmarks.load(req.benchmark), req.scale_factor, req.queries or "all",
                                    req.match)


def to_run_config(req: Request) -> dict:
    if req.errors:
        raise RequestError("; ".join(req.errors))
    prof = profiles.cluster(req.profile)
    preset = profiles.presets()[req.preset]
    targets = []
    for i, t in enumerate(req.targets):
        short = re.sub(r"[^A-Za-z0-9._-]+", "-", t.split("@")[-1].split("/")[-1].split(":")[-1])[:30]
        if req.kind in ("sweep", "release") and re.fullmatch(r"\d+", t):
            name = f"trino-{t}"
        else:
            name = f"{_role(i)}-{short}"
        targets.append({"name": name, "source": t})
    names_by_role = {_role(i): t["name"] for i, t in enumerate(targets)}
    d = {
        "name": req.title or " vs ".join(req.targets),
        "kind": req.kind,
        "description": req.description,
        "benchmark": req.benchmark, "scale_factor": req.scale_factor, "layouts": req.layouts,
        "queries": req.queries or "all", "match": req.match,
        "warmup": preset["warmup"], "repetitions": preset["repetitions"], "rounds": preset["rounds"],
        "resources": prof["resources"], "cluster": prof["cluster"],
        "targets": targets,
        "profile": prof["name"], "preset": req.preset,
        "profile_mode": bool(req.profile_mode),
        "loaders": [names_by_role.get(x, "default") for x in req.loaders] if req.loaders else ["default"],
        "request": {"issue": req.issue, "requested_by": req.requested_by, "variants": req.variants,
                    "repo": os.environ.get("GITHUB_REPOSITORY")},
    }
    if req.variants:
        d["variants"] = profiles.variants()[req.variants]["variants"]
    return d


# --------------------------------------------------------------------------- issue forms
ISSUE_FIELDS = {
    "baseline": "targets0", "change": "targets1", "more targets": "targets_more",
    "benchmark": "benchmark", "scale factor": "scale_factor", "cluster profile": "profile",
    "repetitions": "preset", "queries": "queries", "query filter": "match",
    "settings variants": "variants", "publish results": "publish", "what are you testing?": "description",
    "table layouts": "layouts", "profile mode": "profile_mode",
}


def parse_issue(body: str, title: str | None = None, number: int | None = None,
                author: str | None = None) -> Request:
    """Parse the Markdown that GitHub renders for the benchmark issue form."""
    sections: dict[str, str] = {}
    current = None
    for line in (body or "").splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    v = {key: _none(sections.get(label)) for label, key in ISSUE_FIELDS.items()}
    targets = [v["targets0"], v["targets1"]] + (v["targets_more"] or "").split()
    def first_word(x, default):
        return (x or default).split()[0] if (x or default) else default
    req = Request(
        targets=[t for t in targets if t],
        benchmark=first_word(v["benchmark"], "tpch"),
        scale_factor=first_word(v["scale_factor"], "1"),
        profile=first_word(v["profile"], "gh-standard"),
        preset=first_word(v["preset"], "standard"),
        queries=v["queries"] or "all",
        match=v["match"],
        layouts=[x.split()[0] for x in (v["layouts"] or "").split(",") if x.strip()],
        variants=None if (v["variants"] or "none").split()[0] in ("none", "defaults") else v["variants"].split()[0],
        publish=(v["publish"] or "yes").lower().startswith("yes"),
        profile_mode=(v["profile_mode"] or "no").lower().startswith(("yes", "true")),
        title=(title or "")[:150] or None,
        description=(v["description"] or "")[:2000] or None,
        kind="request", issue=number, requested_by=author,
    )
    return validate(req)


def describe(req: Request) -> str:
    """Markdown description of a parsed request (for the issue comment)."""
    lines = ["| | |", "|---|---|"]
    roles = ["baseline", "change"] + [f"target {i}" for i in range(3, 10)]
    for role, t in zip(roles, req.targets):
        shown = t[:120].replace("|", "\\|")  # keep the Markdown table intact
        lines.append(f"| {role} | `{shown}` |")
    lines.append(f"| benchmark | {req.benchmark} SF{req.scale_factor} |")
    if not req.errors and req.benchmark in benchmarks.available():
        bench = benchmarks.load(req.benchmark)
        shown = [f"`{x}`" + ("" if bench.layouts[x].validated else " (bencholap layout)")
                 for x in req.layouts if x in bench.layouts]
        lines.append(f"| table layouts | {', '.join(shown)} |")
    if not req.errors:
        try:
            p = profiles.cluster(req.profile)
            lines.append(f"| cluster profile | `{req.profile}`: {p['title']} |")
            pr = profiles.presets()[req.preset]
            lines.append(f"| repetitions | `{req.preset}`: {pr['description']} |")
            qs = selected_queries(req)
            lines.append(f"| queries | {len(qs)}: {', '.join(qs[:30])}{' …' if len(qs) > 30 else ''} |")
        except ValueError:
            pass
    if req.variants:
        lines.append(f"| settings variants | `{req.variants}`: {profiles.variants()[req.variants].get('title', '')} |")
    if req.loaders:
        lines.append(f"| dataset loaders | {', '.join(f'`{x}`' for x in req.loaders)}: every layout is written by "
                     "each of them and every configuration reads every copy |")
    if req.profile_mode:
        lines.append("| profile mode | yes: after the measurements, one more profiled pass per configuration |")
    lines.append(f"| publish | {'yes' if req.publish else 'no (results only in the workflow artifact)'} |")
    return "\n".join(lines)


def load(path: Path) -> Request:
    return validate(Request(**json.loads(Path(path).read_text())))
