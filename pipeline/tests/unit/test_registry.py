"""Unit tests for cholsey_pipeline.registry.

These use small, self-contained YAML fixtures written to a temp directory
rather than the real config/ directory (that doesn't exist until P0.4), so
this test suite doesn't depend on later work packages. Once config/*.yaml
exist for real, P0.4 should add an integration test that loads them via the
default CONFIG_DIR.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cholsey_pipeline.registry import RegistryError, load_geography, load_metrics, load_sources

VALID_METRICS_YAML = """
metrics:
  canopy:
    label: "Tree canopy cover"
    unit: "%"
    direction: higher_is_better
  electricity:
    label: "Domestic electricity consumption"
    unit: "kWh/meter/year"
    direction: lower_is_better
"""

VALID_GEOGRAPHY_YAML = """
areas:
  E04012474:
    name: Cholsey
    role: subject
  E07000179:
    name: South Oxfordshire
    role: district
"""

VALID_SOURCES_YAML = """
sources:
  desnz_lsoa_elec:
    name: "DESNZ Sub-national electricity consumption, LSOA"
    publisher: DESNZ
    licence: "Open Government Licence v3.0"
    attribution_text: "Contains public sector information licensed under the OGL v3.0."
    parser: xlsx
    download_url: "https://example.invalid/data.xlsx"
"""


def _write(tmp_path: Path, filename: str, content: str) -> None:
    (tmp_path / filename).write_text(content, encoding="utf-8")


class TestLoadMetrics:
    def test_loads_valid_metrics(self, tmp_path: Path) -> None:
        _write(tmp_path, "metrics.yaml", VALID_METRICS_YAML)
        metrics = load_metrics(tmp_path)
        assert set(metrics) == {"canopy", "electricity"}
        assert metrics["canopy"]["unit"] == "%"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="not found"):
            load_metrics(tmp_path)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "metrics.yaml",
            "metrics:\n  canopy:\n    label: 'Tree canopy cover'\n",
        )
        with pytest.raises(RegistryError, match="missing required field"):
            load_metrics(tmp_path)

    def test_invalid_direction_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "metrics.yaml",
            "metrics:\n  canopy:\n    label: x\n    unit: '%'\n    direction: sideways\n",
        )
        with pytest.raises(RegistryError, match="direction"):
            load_metrics(tmp_path)

    def test_empty_metrics_raises(self, tmp_path: Path) -> None:
        _write(tmp_path, "metrics.yaml", "metrics: {}\n")
        with pytest.raises(RegistryError, match="no 'metrics' entries"):
            load_metrics(tmp_path)


class TestLoadGeography:
    def test_loads_valid_geography(self, tmp_path: Path) -> None:
        _write(tmp_path, "geography.yaml", VALID_GEOGRAPHY_YAML)
        areas = load_geography(tmp_path)
        assert areas["E04012474"]["role"] == "subject"
        assert areas["E07000179"]["role"] == "district"

    def test_invalid_role_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "geography.yaml",
            "areas:\n  E00000000:\n    name: Nowhere\n    role: made_up\n",
        )
        with pytest.raises(RegistryError, match="role"):
            load_geography(tmp_path)


class TestLoadSources:
    def test_loads_valid_sources(self, tmp_path: Path) -> None:
        _write(tmp_path, "sources.yaml", VALID_SOURCES_YAML)
        sources = load_sources(tmp_path)
        assert sources["desnz_lsoa_elec"]["publisher"] == "DESNZ"

    def test_missing_licence_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "sources.yaml",
            (
                "sources:\n"
                "  bad:\n"
                "    name: x\n"
                "    publisher: y\n"
                "    licence: ''\n"
                "    attribution_text: z\n"
                "    parser: csv\n"
                "    download_url: 'https://example.invalid/x.csv'\n"
            ),
        )
        with pytest.raises(RegistryError, match="licence"):
            load_sources(tmp_path)

    def test_missing_attribution_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "sources.yaml",
            (
                "sources:\n"
                "  bad:\n"
                "    name: x\n"
                "    publisher: y\n"
                "    licence: OGL\n"
                "    attribution_text: ''\n"
                "    parser: csv\n"
                "    download_url: 'https://example.invalid/x.csv'\n"
            ),
        )
        with pytest.raises(RegistryError, match="attribution_text"):
            load_sources(tmp_path)

    def test_missing_parser_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "sources.yaml",
            (
                "sources:\n"
                "  bad:\n"
                "    name: x\n"
                "    publisher: y\n"
                "    licence: OGL\n"
                "    attribution_text: z\n"
                "    download_url: 'https://example.invalid/x.csv'\n"
            ),
        )
        with pytest.raises(RegistryError, match="missing required field"):
            load_sources(tmp_path)

    def test_empty_parser_raises(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "sources.yaml",
            (
                "sources:\n"
                "  bad:\n"
                "    name: x\n"
                "    publisher: y\n"
                "    licence: OGL\n"
                "    attribution_text: z\n"
                "    parser: ''\n"
                "    download_url: 'https://example.invalid/x.csv'\n"
            ),
        )
        with pytest.raises(RegistryError, match="parser"):
            load_sources(tmp_path)

    def test_missing_fetch_info_raises(self, tmp_path: Path) -> None:
        """A source with a parser but none of download_url/download_urls/
        discovery_rule should fail -- P2.1 requires at least one, so a
        fetcher always has a real URL or an explicit note on how to find
        one, never silence."""
        _write(
            tmp_path,
            "sources.yaml",
            (
                "sources:\n"
                "  bad:\n"
                "    name: x\n"
                "    publisher: y\n"
                "    licence: OGL\n"
                "    attribution_text: z\n"
                "    parser: csv\n"
            ),
        )
        with pytest.raises(RegistryError, match="download_url"):
            load_sources(tmp_path)

    def test_discovery_rule_alone_is_sufficient(self, tmp_path: Path) -> None:
        """A source not yet ready to fetch can use discovery_rule instead of
        a real download_url -- e.g. one still pending an access
        investigation (P2.7)."""
        _write(
            tmp_path,
            "sources.yaml",
            (
                "sources:\n"
                "  pending:\n"
                "    name: x\n"
                "    publisher: y\n"
                "    licence: OGL\n"
                "    attribution_text: z\n"
                "    parser: 'TBD'\n"
                "    discovery_rule: 'Investigate access first (P2.7).'\n"
            ),
        )
        sources = load_sources(tmp_path)
        assert sources["pending"]["discovery_rule"] == "Investigate access first (P2.7)."
