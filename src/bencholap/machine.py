"""Describe the machine a run executed on.

Timing results are only comparable between runs on the same kind of machine. The
``fingerprint`` groups runs by hardware class (CPU model, cores, memory, runner type);
the report and site only put timings side by side when fingerprints match.
"""

from __future__ import annotations

import os
import platform
import re
from pathlib import Path

from .util import stable_hash


def _cpu_model() -> str:
    try:
        m = re.search(r"^model name\s*:\s*(.+)$", Path("/proc/cpuinfo").read_text(), re.MULTILINE)
        if m:
            return m.group(1).strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def _memory_gb() -> float | None:
    try:
        m = re.search(r"^MemTotal:\s+(\d+) kB", Path("/proc/meminfo").read_text(), re.MULTILINE)
        return round(int(m.group(1)) / 1024 / 1024, 1) if m else None
    except OSError:
        return None


def describe(topology: dict | None = None) -> dict:
    """``topology`` (cluster type, worker count, per-container limits) is part of the machine
    class: one node and three workers on the same host are not comparable."""
    gh = os.environ.get("GITHUB_ACTIONS") == "true"
    runner = {
        "kind": ("github-hosted" if os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted" else
                 "github-self-hosted") if gh else "local",
        "name": os.environ.get("RUNNER_NAME"),
        "image": os.environ.get("ImageOS"),
        "image_version": os.environ.get("ImageVersion"),
        "label": os.environ.get("BENCHOLAP_MACHINE_LABEL"),
    }
    info = {
        "cpu_model": _cpu_model(),
        "cpu_count": os.cpu_count(),
        "memory_gb": _memory_gb(),
        "arch": platform.machine(),
        "os": f"{platform.system()} {platform.release()}",
        "runner": {k: v for k, v in runner.items() if v},
    }
    # Memory is bucketed so small reporting differences do not split a machine class.
    mem_bucket = round((info["memory_gb"] or 0) / 4) * 4
    info["topology"] = topology or {}
    info["fingerprint"] = stable_hash([info["cpu_model"], info["cpu_count"], mem_bucket, info["arch"],
                                       runner["kind"], runner.get("label"), topology or {}])
    cl = (topology or {}).get("cluster", {})
    res = (topology or {}).get("resources", {})
    shape = f"{cl.get('type', 'docker')}, {cl.get('workers', 0)} worker(s)" + (
        f", {res.get('memory', '')} / {res.get('cpus', 'all')} cpus per node" if res else "")
    profile = (topology or {}).get("profile")
    info["profile"] = profile
    info["display"] = (f"{profile or runner.get('label') or runner['kind']}: {info['cpu_count']}x {info['cpu_model']}, "
                       f"{info['memory_gb']} GB · {shape}")
    return info
