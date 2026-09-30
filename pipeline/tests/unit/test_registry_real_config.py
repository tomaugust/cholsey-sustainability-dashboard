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

    def test_comparator_parishes_have_real_confirmed_codes(self) -> None:
        """Comparators have real GSS codes (P1.3/ADR-0003), confirmed by
        the project lead 2026-09-28 (Q-009: 'Use all 8') — no PENDING-*
        placeholders and no lingering pending_confirmation flag."""
        areas = load_geography()
        comparators = {code: a for code, a in areas.items() if a["role"] == "comparator"}
        assert comparators, "expected at least one comparator parish"
        for code, entry in comparators.items():
            assert code.startswith("E0"), (
                f"comparator '{code}' should be a real GSS code (P1.3 computed these "
                "from live ONS adjacency data, see ADR-0003) — a PENDING-* placeholder "
                "would mean P1.3's work got reverted"
            )
            assert "pending_confirmation" not in entry, (
                f"comparator '{code}' is confirmed (Q-009) — the pending_confirmation "
                "flag should have been removed, not left stale"
            )

    def test_eight_real_touching_parishes_are_comparators(self) -> None:
        """ADR-0003's proposed set: all 8 parishes P1.3 found genuinely
        touching Cholsey's polygon, not just the spec's original 5
        candidates (2 of which turned out to be wrong — see the ADR)."""
        areas = load_geography()
        comparators = {a["name"] for a in areas.values() if a["role"] == "comparator"}
        assert comparators == {
            "Wallingford",
            "Moulsford",
            "South Stoke",
            "Brightwell-cum-Sotwell",
            "Aston Tirrold",
            "Aldworth",
            "Crowmarsh",
            "South Moreton",
        }


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

    def test_every_source_has_parser_and_fetch_info(self) -> None:
        """P2.1 (development-plan.md Phase 2): every source needs a parser
        and at least one of download_url/download_urls/discovery_rule --
        already enforced by the loader, but this pins it against the real
        file so a future entry can't accidentally omit both."""
        sources = load_sources()
        for source_id, entry in sources.items():
            assert entry.get("parser"), f"source '{source_id}' has no parser"
            assert (
                "download_url" in entry or "download_urls" in entry or "discovery_rule" in entry
            ), f"source '{source_id}' has none of download_url/download_urls/discovery_rule"

    def test_real_download_urls_are_https(self) -> None:
        """Every concrete download_url/download_urls entry should be a real
        https:// URL, not a placeholder -- a source still pending
        investigation should use discovery_rule instead."""
        sources = load_sources()
        for source_id, entry in sources.items():
            if "download_url" in entry:
                assert entry["download_url"].startswith("https://"), source_id
            for name, url in entry.get("download_urls", {}).items():
                assert url.startswith("https://"), f"{source_id}.{name}"
