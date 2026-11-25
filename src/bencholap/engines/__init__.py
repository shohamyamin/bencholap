"""Engine registry. Adding an engine = adding a sub-package that exposes ENGINE."""

from __future__ import annotations

from importlib import import_module

from .base import Engine

_ENGINES = {"trino": "bencholap.engines.trino"}


def get(name: str) -> Engine:
    if name not in _ENGINES:
        raise ValueError(f"unknown engine {name!r}; available: {sorted(_ENGINES)}")
    return import_module(_ENGINES[name]).ENGINE


def available() -> list[str]:
    return sorted(_ENGINES)
