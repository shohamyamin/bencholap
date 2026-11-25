"""Engine plugin interface.

An engine plugin knows how to turn a user-supplied target string (release, image, fork
and branch, ...) into something runnable, how to start it against the shared stack, and
how to execute SQL and report engine-native metrics. Everything else (datasets, query
selection, repetitions, validation, results, reports) is engine-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ResolvedTarget:
    """A concrete, reproducible engine build."""

    engine: str
    spec: str                      # what the user asked for, e.g. "github:me/trino@my-branch"
    image: str                     # runnable docker image
    version: str                   # engine version string, e.g. "484" or "485-SNAPSHOT"
    version_number: int | None     # numeric version used to pick version-specific config profiles
    source: dict[str, Any] = field(default_factory=dict)   # kind, repo, ref, commit, image digest...


@dataclass
class StatementResult:
    rows: list[tuple] | None
    columns: list[str] | None
    query_id: str | None
    wall_ms: float
    engine_stats: dict[str, Any]


class EngineSession(Protocol):
    def execute(self, sql: str, fetch: bool = True) -> StatementResult: ...
    def explain(self, sql: str) -> str | None: ...
    def close(self) -> None: ...


class RunningEngine(Protocol):
    target: ResolvedTarget
    effective_config: dict[str, Any]

    def session(self, schema: str, session_properties: dict[str, Any]) -> EngineSession: ...
    def stop(self) -> None: ...


class Engine(Protocol):
    name: str

    def resolve(self, spec: str) -> ResolvedTarget: ...
    def start(self, target: ResolvedTarget, overrides: dict[str, Any], resources: dict[str, Any]) -> RunningEngine: ...
