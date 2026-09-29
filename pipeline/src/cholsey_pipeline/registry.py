"""Load and validate the project's YAML config registries.

config/sources.yaml, config/geography.yaml and config/metrics.yaml (see
development-plan.md §2.2 and §0.4) are the single source of truth for what
datasets, areas and metrics the pipeline knows about. This module loads them
into plain dict/list structures and checks the invariants the later phases
rely on, so a malformed entry fails fast and loudly (development-plan.md §1,
principle 4) rather than surfacing as a confusing failure deep in the
pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Repo root is three levels up from this file: pipeline/src/cholsey_pipeline/registry.py
REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config"


class RegistryError(ValueError):
    """Raised when a config file is missing a required field or is inconsistent."""


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise RegistryError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_metrics(config_dir: Path = CONFIG_DIR) -> dict[str, dict]:
    """Load config/metrics.yaml and validate each entry has the required fields.

    Returns a dict keyed by metric_id. Required fields per metric, per
    development-plan.md §2.3/§3: label, unit, direction. Optional but
    recommended: valid_range, max_yoy_change_pct, similar_band_pct, spec_ref.
    """
    data = _load_yaml(config_dir / "metrics.yaml") or {}
    metrics = data.get("metrics", {})
    if not metrics:
        raise RegistryError("metrics.yaml has no 'metrics' entries")

    required_fields = ("label", "unit", "direction")
    valid_directions = {"higher_is_better", "lower_is_better", "neutral"}

    for metric_id, entry in metrics.items():
        if not isinstance(entry, dict):
            raise RegistryError(f"metric '{metric_id}': entry must be a mapping")
        missing = [f for f in required_fields if f not in entry]
        if missing:
            raise RegistryError(f"metric '{metric_id}': missing required field(s) {missing}")
        if entry["direction"] not in valid_directions:
            raise RegistryError(
                f"metric '{metric_id}': direction '{entry['direction']}' is not "
                f"one of {sorted(valid_directions)}"
            )
    return metrics


def load_geography(config_dir: Path = CONFIG_DIR) -> dict[str, dict]:
    """Load config/geography.yaml and validate each area has the required fields.

    Returns a dict keyed by area_code (GSS code). Required fields per
    development-plan.md §2.3: name, role (subject/comparator/district/national).
    """
    data = _load_yaml(config_dir / "geography.yaml") or {}
    areas = data.get("areas", {})
    if not areas:
        raise RegistryError("geography.yaml has no 'areas' entries")

    required_fields = ("name", "role")
    valid_roles = {"subject", "comparator", "district", "national"}

    for area_code, entry in areas.items():
        if not isinstance(entry, dict):
            raise RegistryError(f"area '{area_code}': entry must be a mapping")
        missing = [f for f in required_fields if f not in entry]
        if missing:
            raise RegistryError(f"area '{area_code}': missing required field(s) {missing}")
        if entry["role"] not in valid_roles:
            raise RegistryError(
                f"area '{area_code}': role '{entry['role']}' is not one of {sorted(valid_roles)}"
            )
    return areas


def load_sources(config_dir: Path = CONFIG_DIR) -> dict[str, dict]:
    """Load config/sources.yaml and validate each source has the required fields.

    Returns a dict keyed by source_id. Required fields per
    development-plan.md §2.3/§4 traceability requirements: name, publisher,
    licence, attribution_text.
    """
    data = _load_yaml(config_dir / "sources.yaml") or {}
    sources = data.get("sources", {})
    if not sources:
        raise RegistryError("sources.yaml has no 'sources' entries")

    required_fields = ("name", "publisher", "licence", "attribution_text")

    for source_id, entry in sources.items():
        if not isinstance(entry, dict):
            raise RegistryError(f"source '{source_id}': entry must be a mapping")
        missing = [f for f in required_fields if f not in entry]
        if missing:
            raise RegistryError(f"source '{source_id}': missing required field(s) {missing}")
        if not entry["licence"]:
            raise RegistryError(f"source '{source_id}': licence must not be empty")
        if not entry["attribution_text"]:
            raise RegistryError(f"source '{source_id}': attribution_text must not be empty")
    return sources
