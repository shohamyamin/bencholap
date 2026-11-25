"""Render version-specific Trino configuration (catalog files + config.properties)."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from ...stack import STACK

PROFILES = Path(__file__).with_name("profiles.yaml")


def load_profiles() -> dict:
    return yaml.safe_load(PROFILES.read_text())


def placeholders() -> dict[str, str]:
    return {
        "s3_endpoint": STACK.s3_endpoint_internal, "s3_access_key": STACK.access_key,
        "s3_secret_key": STACK.secret_key, "s3_region": STACK.region,
        "catalog_uri": STACK.catalog_uri_internal, "warehouse": STACK.warehouse,
        "raw_bucket": STACK.raw_bucket,
    }


def merge(base: dict[str, Any], *overlays: dict[str, Any] | None) -> dict[str, Any]:
    """Merge property maps; a None value removes the property."""
    out = dict(base)
    for ov in overlays:
        for k, v in (ov or {}).items():
            if v is None:
                out.pop(k, None)
            else:
                out[k] = v
    return out


def profile_properties(section: dict, version: int | None) -> tuple[dict[str, Any], list[str]]:
    entries = section.get("when") or []
    if version is None:
        # Unknown version (custom image without a detectable version): newest profile wins.
        chosen = entries[-1:]
    else:
        chosen = [e for e in entries if Version(str(version)) in SpecifierSet(e["versions"])]
    props = merge(dict(section.get("base") or {}), *[e["properties"] for e in chosen])
    return props, [e["versions"] for e in chosen]


def _fill(props: dict[str, Any]) -> dict[str, str]:
    ph = placeholders()
    return {k: str(v).format(**ph) for k, v in props.items()}


def render_catalogs(version: int | None, catalogs: list[str], overrides: dict[str, dict] | None
                    ) -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    prof = load_profiles()
    out, applied = {}, {}
    for name in catalogs:
        props, used = profile_properties(prof["catalogs"][name], version)
        out[name] = _fill(merge(props, (overrides or {}).get(name)))
        applied[name] = used
    return out, applied


def parse_properties(text: str) -> dict[str, str]:
    props = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")) or "=" not in line:
            continue
        k, _, v = line.partition("=")
        props[k.strip()] = v.strip()
    return props


def format_properties(props: dict[str, str]) -> str:
    return "".join(f"{k}={v}\n" for k, v in props.items())


def render_config(version: int | None, image_defaults: dict[str, str], overrides: dict | None) -> dict[str, str]:
    prof = load_profiles()
    props, _ = profile_properties(prof.get("config") or {}, version)
    return {k: str(v) for k, v in merge(copy.copy(image_defaults), props, overrides).items()}


def check_supported(version: int | None) -> None:
    minimum = load_profiles().get("min_version")
    if version is not None and minimum and version < minimum:
        raise ValueError(f"Trino {version} is older than the oldest supported version {minimum} "
                         "(no Iceberg REST catalog support)")
