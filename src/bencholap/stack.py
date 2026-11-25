"""Shared data stack: S3-compatible object storage (SeaweedFS) + Iceberg REST catalog.

All engines under test read the same tables through the same catalog and storage. The
stack state (object data + catalog database) lives under $BENCHOLAP_HOME/state so a
dataset is written once and can be exported/imported as a tarball (for example as a CI
artifact shared by many benchmark jobs).
"""

from __future__ import annotations

import json
import os
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml

from .util import home, log, run, wait_until

NETWORK = "bencholap"
PROJECT = "bencholap"

SEAWEEDFS_IMAGE = os.environ.get("BENCHOLAP_SEAWEEDFS_IMAGE", "chrislusf/seaweedfs:4.55")
REST_CATALOG_IMAGE = os.environ.get("BENCHOLAP_REST_CATALOG_IMAGE", "apache/iceberg-rest-fixture:1.10.1")


@dataclass(frozen=True)
class StackInfo:
    """How engines (inside the docker network) and the harness (on the host) reach the stack."""

    s3_endpoint_internal: str = "http://storage:8333"
    s3_endpoint_host: str = "http://127.0.0.1:18333"
    catalog_uri_internal: str = "http://catalog:8181"
    catalog_uri_host: str = "http://127.0.0.1:18181"
    access_key: str = "bencholap"
    secret_key: str = "bencholap-secret"
    region: str = "us-east-1"
    warehouse_bucket: str = "warehouse"
    raw_bucket: str = "raw"

    @property
    def warehouse(self) -> str:
        return f"s3://{self.warehouse_bucket}/"


def _from_env() -> StackInfo:
    """BENCHOLAP_STACK=external uses existing object storage and an existing Iceberg REST
    catalog (for clusters on real infrastructure) instead of the local docker stack:

        BENCHOLAP_S3_ENDPOINT  BENCHOLAP_S3_ACCESS_KEY  BENCHOLAP_S3_SECRET_KEY  BENCHOLAP_S3_REGION
        BENCHOLAP_CATALOG_URI  BENCHOLAP_WAREHOUSE_BUCKET  BENCHOLAP_RAW_BUCKET

    Engines and the harness then use the same endpoints, so they must be reachable from both.
    """
    if os.environ.get("BENCHOLAP_STACK") != "external":
        return StackInfo()
    e = os.environ
    s3 = e["BENCHOLAP_S3_ENDPOINT"]
    catalog = e["BENCHOLAP_CATALOG_URI"]
    return StackInfo(s3_endpoint_internal=s3, s3_endpoint_host=s3, catalog_uri_internal=catalog,
                     catalog_uri_host=catalog, access_key=e["BENCHOLAP_S3_ACCESS_KEY"],
                     secret_key=e["BENCHOLAP_S3_SECRET_KEY"], region=e.get("BENCHOLAP_S3_REGION", "us-east-1"),
                     warehouse_bucket=e.get("BENCHOLAP_WAREHOUSE_BUCKET", "warehouse"),
                     raw_bucket=e.get("BENCHOLAP_RAW_BUCKET", "raw"))


STACK = _from_env()
EXTERNAL = os.environ.get("BENCHOLAP_STACK") == "external"


def stack_dir() -> Path:
    return home() / "stack"


def state_dir() -> Path:
    return home() / "state"


def _uid_gid() -> str:
    return f"{os.getuid()}:{os.getgid()}"


def write_compose() -> Path:
    sd = stack_dir()
    st = state_dir()
    (st / "storage").mkdir(parents=True, exist_ok=True)
    (st / "catalog").mkdir(parents=True, exist_ok=True)
    sd.mkdir(parents=True, exist_ok=True)
    s3_config = {
        "identities": [{
            "name": "bencholap",
            "credentials": [{"accessKey": STACK.access_key, "secretKey": STACK.secret_key}],
            "actions": ["Admin", "Read", "Write", "List", "Tagging"],
        }]
    }
    (sd / "s3.json").write_text(json.dumps(s3_config, indent=2))
    compose = {
        "name": PROJECT,
        "networks": {"default": {"name": NETWORK}},
        "services": {
            "storage": {
                "image": SEAWEEDFS_IMAGE,
                "user": _uid_gid(),
                "command": [
                    "server", "-dir=/data", "-ip=storage", "-ip.bind=0.0.0.0",
                    "-s3", "-s3.port=8333", "-s3.config=/etc/seaweedfs/s3.json",
                    "-volume.max=200", "-master.volumeSizeLimitMB=1024",
                ],
                "volumes": [f"{st / 'storage'}:/data", f"{sd / 's3.json'}:/etc/seaweedfs/s3.json:ro"],
                "ports": ["127.0.0.1:18333:8333"],
            },
            "catalog": {
                "image": REST_CATALOG_IMAGE,
                "user": _uid_gid(),
                "depends_on": ["storage"],
                "environment": {
                    "CATALOG_URI": "jdbc:sqlite:/state/catalog.db",
                    "CATALOG_WAREHOUSE": STACK.warehouse,
                    "CATALOG_IO__IMPL": "org.apache.iceberg.aws.s3.S3FileIO",
                    "CATALOG_S3_ENDPOINT": STACK.s3_endpoint_internal,
                    "CATALOG_S3_PATH__STYLE__ACCESS": "true",
                    "AWS_ACCESS_KEY_ID": STACK.access_key,
                    "AWS_SECRET_ACCESS_KEY": STACK.secret_key,
                    "AWS_REGION": STACK.region,
                },
                "volumes": [f"{st / 'catalog'}:/state"],
                "ports": ["127.0.0.1:18181:8181"],
            },
        },
    }
    path = sd / "docker-compose.yml"
    path.write_text(yaml.safe_dump(compose, sort_keys=False))
    return path


def _compose(*args: str, capture: bool = False):
    return run(["docker", "compose", "-f", str(stack_dir() / "docker-compose.yml"), *args], capture=capture)


def s3_filesystem():
    from pyarrow import fs

    scheme, _, host = STACK.s3_endpoint_host.partition("://")
    return fs.S3FileSystem(
        access_key=STACK.access_key, secret_key=STACK.secret_key, region=STACK.region,
        endpoint_override=host, scheme=scheme, allow_bucket_creation=not EXTERNAL,
    )


def up() -> None:
    write_compose()
    _compose("up", "-d", "--wait", "--quiet-pull")
    wait_until(lambda: requests.get(f"{STACK.catalog_uri_host}/v1/config", timeout=5).ok, 120,
               what="Iceberg REST catalog")

    def s3_ready() -> bool:
        s3 = s3_filesystem()
        for bucket in (STACK.warehouse_bucket, STACK.raw_bucket):
            s3.create_dir(bucket)
        return True

    wait_until(s3_ready, 120, interval=2, what="S3 storage")
    log.info("stack up: storage %s, catalog %s", STACK.s3_endpoint_host, STACK.catalog_uri_host)


def down() -> None:
    if (stack_dir() / "docker-compose.yml").exists():
        _compose("down", "--remove-orphans")


def is_up() -> bool:
    try:
        return requests.get(f"{STACK.catalog_uri_host}/v1/config", timeout=2).ok
    except requests.RequestException:
        return False


def ensure_up() -> None:
    if EXTERNAL:
        if not is_up():
            raise RuntimeError(f"external Iceberg REST catalog {STACK.catalog_uri_host} is not reachable")
        return
    if not is_up():
        up()


def export_state(target: Path) -> Path:
    """Stop the stack and write its state (all datasets) to a tar file."""
    down()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(target, "w") as tar:
        tar.add(state_dir(), arcname="state")
    log.info("exported stack state to %s (%.1f MB)", target, target.stat().st_size / 1e6)
    return target


def import_state(source: Path) -> None:
    down()
    if state_dir().exists():
        shutil.rmtree(state_dir())
    with tarfile.open(source, "r:*") as tar:
        tar.extractall(home(), filter="data")
    log.info("imported stack state from %s", source)
