"""Trino engine plugin."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import trino

from ...stack import NETWORK
from ...util import home, log, run, wait_until
from ..base import ResolvedTarget, StatementResult
from . import config as cfg
from . import target as tgt

HOST_PORT = 18080
CONTAINER = "bencholap-trino"
USER = "bencholap"
SECRET_KEYS = re.compile(r"(secret|password|access-key)", re.IGNORECASE)

_DURATION_UNITS = {"ns": 1e-6, "us": 1e-3, "ms": 1.0, "s": 1e3, "m": 6e4, "h": 3.6e6, "d": 8.64e7}
_SIZE_UNITS = {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12, "PB": 1e15}

# QueryStats fields kept from /v1/query/{id}. Durations -> *_ms, data sizes -> *_bytes.
_DURATIONS = ["elapsedTime", "queuedTime", "analysisTime", "planningTime", "executionTime",
              "totalCpuTime", "totalScheduledTime", "totalBlockedTime", "physicalInputReadTime"]
_SIZES = ["peakUserMemoryReservation", "peakTotalMemoryReservation", "spilledDataSize",
          "physicalInputDataSize", "processedInputDataSize", "rawInputDataSize",
          "internalNetworkInputDataSize", "outputDataSize", "physicalWrittenDataSize"]
_COUNTS = ["physicalInputPositions", "processedInputPositions", "rawInputPositions",
           "outputPositions", "totalDrivers"]


def _duration_ms(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"\s*([\d.]+)\s*([a-z]+)\s*", str(v))
    return float(m.group(1)) * _DURATION_UNITS[m.group(2)] if m and m.group(2) in _DURATION_UNITS else None


def _size_bytes(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"\s*([\d.]+)\s*([A-Za-z]+)\s*", str(v))
    return float(m.group(1)) * _SIZE_UNITS[m.group(2)] if m and m.group(2) in _SIZE_UNITS else None


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def extract_stats(info: dict) -> dict[str, Any]:
    qs = info.get("queryStats") or {}
    out: dict[str, Any] = {}
    for k in _DURATIONS:
        out[_snake(k).removesuffix("_time") + "_ms" if k.endswith("Time") else _snake(k)] = _duration_ms(qs.get(k))
    for k in _SIZES:
        out[_snake(k).removesuffix("_data_size") + "_bytes"] = _size_bytes(qs.get(k))
    for k in _COUNTS:
        out[_snake(k)] = qs.get(k)
    inputs = []
    for i in info.get("inputs") or []:
        inputs.append({
            "table": f"{i.get('catalogName')}.{i.get('schema')}.{i.get('table')}",
            "columns": len(i.get("columns") or []),
            "physical_input_bytes": _size_bytes(i.get("physicalInputBytes")),
            "physical_input_rows": i.get("physicalInputRows"),
        })
    if inputs:
        out["inputs"] = inputs
    return {k: v for k, v in out.items() if v is not None}


class TrinoSession:
    def __init__(self, base_url: str, schema: str, session_properties: dict[str, Any], user: str = USER):
        u = urlparse(base_url)
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.conn = trino.dbapi.connect(
            host=u.hostname, port=u.port or (443 if u.scheme == "https" else 80), http_scheme=u.scheme,
            user=user, catalog="iceberg", schema=schema,
            session_properties={k: str(v) for k, v in session_properties.items()},
            request_timeout=3600,
        )

    def _query_info(self, query_id: str | None) -> dict:
        if not query_id:
            return {}
        try:
            r = requests.get(f"{self.base_url}/v1/query/{query_id}", headers={"X-Trino-User": self.user},
                             timeout=30)
            return r.json() if r.ok else {}
        except (requests.RequestException, ValueError):
            return {}

    def execute(self, sql: str, fetch: bool = True) -> StatementResult:
        cur = self.conn.cursor()
        t0 = time.perf_counter()
        cur.execute(sql)
        rows = cur.fetchall()
        wall_ms = (time.perf_counter() - t0) * 1000
        columns = [d[0] for d in cur.description] if cur.description else None
        info = self._query_info(cur.query_id)
        return StatementResult(rows if fetch else None, columns, cur.query_id, wall_ms, extract_stats(info))

    def explain(self, sql: str) -> str | None:
        cur = self.conn.cursor()
        cur.execute(f"EXPLAIN (TYPE DISTRIBUTED) {sql}")
        rows = cur.fetchall()
        return rows[0][0] if rows else None

    def close(self) -> None:
        self.conn.close()


def _cluster_info(base_url: str, user: str = USER) -> dict:
    """Version and active nodes as reported by the running cluster."""
    info = requests.get(f"{base_url}/v1/info", timeout=5).json()
    conn = trino.dbapi.connect(**_conn_args(base_url, user))
    cur = conn.cursor()
    cur.execute("SELECT node_id, coordinator, node_version FROM system.runtime.nodes WHERE state = 'active'")
    nodes = cur.fetchall()
    return {"starting": info.get("starting", True), "version": (info.get("nodeVersion") or {}).get("version"),
            "nodes": len(nodes), "workers": sum(1 for n in nodes if not n[1]),
            "node_versions": sorted({n[2] for n in nodes})}


def _conn_args(base_url: str, user: str) -> dict:
    u = urlparse(base_url)
    return {"host": u.hostname, "port": u.port or (443 if u.scheme == "https" else 80),
            "http_scheme": u.scheme, "user": user}


class RunningTrino:
    def __init__(self, target: ResolvedTarget, effective_config: dict[str, Any], workdir: Path,
                 base_url: str, containers: list[str], teardown: str | None = None, env: dict | None = None):
        self.target = target
        self.effective_config = effective_config
        self.workdir = workdir
        self.base_url = base_url
        self.containers = containers
        self.teardown = teardown
        self.env = env or {}

    def session(self, schema: str, session_properties: dict[str, Any]) -> TrinoSession:
        return TrinoSession(self.base_url, schema, session_properties)

    def stop(self) -> None:
        for c in self.containers:
            (self.workdir / f"{c}.log").write_text(run(["docker", "logs", c], capture=True, check=False).stdout or "")
            run(["docker", "rm", "-f", c], capture=True, check=False)
        if self.teardown:
            log.info("cluster teardown: %s", self.teardown)
            run(["bash", "-c", self.teardown], env=self.env, check=False)


def _mask(props: dict[str, str]) -> dict[str, str]:
    return {k: ("***" if SECRET_KEYS.search(k) else v) for k, v in props.items()}


def _worker_config(coordinator_cfg: dict[str, str]) -> dict[str, str]:
    props = {k: v for k, v in coordinator_cfg.items() if k not in ("node-scheduler.include-coordinator",)}
    props.update({"coordinator": "false", "http-server.http.port": "8080",
                  "discovery.uri": f"http://{CONTAINER}:8080"})
    return props


class TrinoEngine:
    """Starts a Trino cluster for a target.

    Cluster types (``cluster:`` in the run config, globally or per target):

    * ``docker`` (default): coordinator plus ``workers`` worker containers on this host, each
      limited by ``resources`` (memory/cpus per container). ``workers: 0`` is a single node.
    * ``command``: your own infrastructure. ``deploy`` is a shell command that must bring up
      the given image with the rendered configuration (see the BENCHOLAP_* environment
      variables) and ``url`` is the coordinator URL; ``teardown`` runs at the end. Use it
      with Helm, Terraform, Ansible, etc. (example: deploy/kubernetes/).
    * ``external``: an already running cluster at ``url``. Nothing is deployed and no
      configuration can be applied; the reported version must match the target.
    """

    name = "trino"

    def resolve(self, spec: str) -> ResolvedTarget:
        return tgt.resolve(spec)

    def _render(self, target: ResolvedTarget, overrides: dict, catalogs, workdir: Path, workers: int):
        image_cfg = run(["docker", "run", "--rm", "--entrypoint", "cat", target.image,
                         "/etc/trino/config.properties"], capture=True).stdout
        image_jvm = run(["docker", "run", "--rm", "--entrypoint", "cat", target.image,
                         "/etc/trino/jvm.config"], capture=True, check=False).stdout or ""
        base_cfg = cfg.parse_properties(image_cfg)
        if workers > 0:
            base_cfg.update({"node-scheduler.include-coordinator": "false",
                             "discovery.uri": f"http://{CONTAINER}:8080"})
        config_props = cfg.render_config(target.version_number, base_cfg, overrides.get("config"))
        catalog_props, applied = cfg.render_catalogs(target.version_number, list(catalogs), overrides.get("catalog"))
        (workdir / "catalog").mkdir(parents=True, exist_ok=True)
        for old in (workdir / "catalog").glob("*.properties"):
            old.unlink()
        (workdir / "config.properties").write_text(cfg.format_properties(config_props))
        (workdir / "worker-config.properties").write_text(cfg.format_properties(_worker_config(config_props)))
        for name, props in catalog_props.items():
            (workdir / "catalog" / f"{name}.properties").write_text(cfg.format_properties(props))
        return config_props, catalog_props, applied, image_jvm

    def start(self, target: ResolvedTarget, overrides: dict[str, Any], resources: dict[str, Any],
              catalogs: tuple[str, ...] = ("iceberg",), label: str = "run",
              cluster: dict[str, Any] | None = None) -> RunningTrino:
        cfg.check_supported(target.version_number)
        cluster = dict(cluster or {"type": "docker"})
        ctype = cluster.get("type", "docker")
        workers = int(cluster.get("workers", 0))
        workdir = home() / "engines" / re.sub(r"[^A-Za-z0-9._-]", "_", label)
        workdir.mkdir(parents=True, exist_ok=True)

        if ctype == "external":
            if overrides.get("config") or overrides.get("catalog"):
                raise ValueError("an external cluster cannot apply config/catalog overrides; use session properties")
            base_url = cluster["url"].rstrip("/")
            info = _cluster_info(base_url)
            if target.version not in ("unknown", info["version"]):
                raise RuntimeError(f"external cluster runs Trino {info['version']}, target is {target.version}")
            return RunningTrino(target, {"cluster": {**cluster, **info}, "resources": "managed externally"},
                                workdir, base_url, [])

        config_props, catalog_props, applied, image_jvm = self._render(target, overrides, catalogs, workdir, workers)
        containers: list[str] = []
        teardown, env = None, {}
        if ctype == "docker":
            base_url = f"http://127.0.0.1:{HOST_PORT}"
            if run(["docker", "network", "inspect", NETWORK], capture=True, check=False).returncode != 0:
                run(["docker", "network", "create", NETWORK], capture=True)
            names = [CONTAINER] + [f"{CONTAINER}-worker-{i}" for i in range(1, workers + 1)]
            for n in names:
                run(["docker", "rm", "-f", n], capture=True, check=False)
            limits = []
            if resources.get("memory"):
                limits += ["--memory", str(resources["memory"])]
            if resources.get("cpus"):
                limits += ["--cpus", str(resources["cpus"])]
            for i, n in enumerate(names):
                conf = "config.properties" if i == 0 else "worker-config.properties"
                cmd = ["docker", "run", "-d", "--name", n, "--hostname", n, "--network", NETWORK, *limits,
                       "-v", f"{workdir / 'catalog'}:/etc/trino/catalog:ro",
                       "-v", f"{workdir / conf}:/etc/trino/config.properties:ro"]
                if i == 0:
                    cmd += ["-p", f"127.0.0.1:{HOST_PORT}:8080"]
                run(cmd + [target.image], capture=True)
                containers.append(n)
            log.info("starting Trino %s (%s): coordinator + %d worker(s)", target.version, target.image, workers)
        elif ctype == "command":
            base_url = cluster["url"].rstrip("/")
            env = {"BENCHOLAP_IMAGE": target.image, "BENCHOLAP_VERSION": target.version,
                   "BENCHOLAP_WORKERS": str(workers), "BENCHOLAP_CONFIG_DIR": str(workdir),
                   "BENCHOLAP_LABEL": label, "BENCHOLAP_MEMORY": str(resources.get("memory", "")),
                   "BENCHOLAP_CPUS": str(resources.get("cpus", ""))}
            teardown = cluster.get("teardown")
            (workdir / "deployment.yaml").unlink(missing_ok=True)
            log.info("cluster deploy: %s", cluster["deploy"])
            run(["bash", "-c", cluster["deploy"]], env=env)
        else:
            raise ValueError(f"unknown cluster type {ctype!r}")

        def ready() -> bool:
            for c in containers:
                if run(["docker", "inspect", "-f", "{{.State.Running}}", c], capture=True,
                       check=False).stdout.strip() == "false":
                    raise RuntimeError(f"{c} exited:\n" + (run(["docker", "logs", "--tail", "80", c],
                                                                 capture=True, check=False).stdout or ""))
            info = _cluster_info(base_url)
            return not info["starting"] and info["nodes"] >= workers + 1

        try:
            wait_until(ready, float(cluster.get("startup_timeout", 300)), interval=2,
                       what=f"Trino {target.version} with {workers} worker(s)")
        except Exception:
            for c in containers:
                log.error("%s last log lines:\n%s", c, run(["docker", "logs", "--tail", "40", c], capture=True,
                                                             check=False).stdout)
            RunningTrino(target, {}, workdir, base_url, containers, teardown, env).stop()
            raise
        info = _cluster_info(base_url)
        effective = {
            "config.properties": config_props,
            "jvm.config": [ln for ln in image_jvm.splitlines() if ln.strip()],
            "catalogs": {n: _mask(p) for n, p in catalog_props.items()},
            "profiles_applied": applied,
            "resources": resources,
            "cluster": {"type": ctype, "workers": info["workers"], "nodes": info["nodes"],
                        "node_versions": info["node_versions"],
                        **({"url": base_url} if ctype != "docker" else {})},
        }
        if ctype == "command":
            effective["cluster"]["deploy"] = cluster["deploy"]
            deployed = workdir / "deployment.yaml"
            if deployed.exists():
                # what the deploy script actually applied (e.g. Helm values: heap, resources)
                effective["deployment"] = deployed.read_text()
        return RunningTrino(target, effective, workdir, base_url, containers, teardown, env)


ENGINE = TrinoEngine()
