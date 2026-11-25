"""Small shared helpers: workspace paths, subprocess, logging, hashing."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

log = logging.getLogger("bencholap")

PACKAGE_DIR = Path(__file__).resolve().parent


def home() -> Path:
    """Workspace for generated data, stack state and build caches (default ./.bencholap)."""
    p = Path(os.environ.get("BENCHOLAP_HOME", ".bencholap")).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def run(cmd: list[str], *, check: bool = True, capture: bool = False, cwd: Path | None = None,
        env: dict[str, str] | None = None, timeout: float | None = None) -> subprocess.CompletedProcess:
    log.debug("$ %s", " ".join(cmd))
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(cmd, check=check, text=True, cwd=cwd, env=full_env, timeout=timeout,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def wait_until(fn: Callable[[], bool], timeout: float, interval: float = 1.0, what: str = "condition") -> None:
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if fn():
                return
        except Exception as e:  # noqa: BLE001 - retried until timeout
            last_err = e
        time.sleep(interval)
    raise TimeoutError(f"timed out after {timeout:.0f}s waiting for {what}" + (f": {last_err}" if last_err else ""))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def stable_hash(obj: Any, length: int = 12) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, default=str))[:length]


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=False, default=str) + "\n")
    tmp.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())
