"""Integration tests: load the project's REAL config/*.yaml files (P0.4).

Unlike test_registry.py (which uses small tmp_path fixtures independent of
any real config), these tests load config/ at the repo root through the
default CONFIG_DIR, so they catch a genuinely broken or incomplete config
file — not just a bug in the loader itself.
"""

from __future__ import annotations

from cholsey_pipeline.registry import load_geography, load_metrics, load_sources


class TestRealMetricsYaml:
    def test_loads_without_error(self) -> None:
        metrics = load_metrics()
        assert len(metrics) >= 6  # 6 core metrics + optional EPC stretch

    def test_has_expected_core_metric_ids(self) -> None:
        metrics = load_metrics()
        expected = {"canopy", "greenspace", "electricity", "gas", "solar_pv", "heat_pump"}
        assert expected.issubset(metrics.keys())

    def test_electricity_and_gas_are_lower_is_better(self) -> None:
        metrics = load_metrics()
        assert metrics["electricity"]["direction"] == "lower_is_better"
        assert metrics["gas"]["direction"] == "lower_is_better"

    def test_home_energy_tile_group_combines_electricity_and_gas(self) -> None:
        """Q-002 resolution: electricity + gas render as one home-page tile."""
        import yaml

        from cholsey_pipeline.registry import CONFIG_DIR

        raw = yaml.safe_load((CONFIG_DIR / "metrics.yaml").read_text(encoding="utf-8"))
        tile_groups = raw.get("tile_groups", {})
        assert "home_energy" in tile_groups
        assert set(tile_groups["home_energy"]["metrics"]) == {"electricity", "gas"}


class TestRealGeographyYaml:
    def test_loads_without_error(self) -> None:
        areas = load_geography()
        assert len(areas) >= 2  # at least the subject parish and the district

    def test_cholsey_is_the_subject(self) -> None:
        areas = load_geography()
        assert areas["E04012474"]["role"] == "subject"
        assert areas["E04012474"]["name"] == "Cholsey"

    def test_district_present(self) -> None:
        areas = load_geography()
        assert areas["E07000179"]["role"] == "district"

    def test_national_present_and_is_england_by_default(self) -> None:
        """Q-003 resolution: England is the default national comparator."""
        areas = load_geography()
        national = {code: a for code, a in areas.items() if a["role"] == "national"}
        assert national, "expected at least one area with role=national"
        assert "E92000001" in national
        assert national["E92000001"]["name"] == "England"

    def test_comparator_parishes_are_explicitly_flagged_pending(self) -> None:
        """Comparators aren't confirmed yet (Phase 1) — must not look 'real'."""
        areas = load_geography()
        comparators = {code: a for code, a in areas.items() if a["role"] == "comparator"}
        assert comparators, "expected at least one candidate comparator parish"
        for code, entry in comparators.items():
            assert code.startswith("PENDING-"), (
                f"comparator '{code}' should be a PENDING-* placeholder until "
                "Phase 1 confirms its real GSS code"
            )
            assert entry.get("pending_confirmation") is True


class TestRealSourcesYaml:
    def test_loads_without_error(self) -> None:
        sources = load_sources()
        assert len(sources) >= 7  # 6 metric sources + at least one boundary source

    def test_every_source_has_a_url(self) -> None:
        """Not enforced by the loader (url is optional there), but every real
        entry should have one — a source without a URL fails spec §4's
        traceability requirement in practice, even if the schema allows it."""
        sources = load_sources()
        for source_id, entry in sources.items():
            assert entry.get("url"), f"source '{source_id}' has no url"

    def test_desnz_sources_present(self) -> None:
        sources = load_sources()
        assert "desnz_lsoa_energy" in sources
        assert "desnz_postcode_energy" in sources
        assert sources["desnz_lsoa_energy"]["publisher"] == "DESNZ"
