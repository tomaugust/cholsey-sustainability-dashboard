"""Tests for cholsey_pipeline.fetch.desnz_postcode_energy.

Uses a committed, real fixture (trimmed real OX10 rows from the live 2024
electricity/gas postcode-level CSVs, P2.6) -- no network, per
development-plan.md §5.1. The live network calls (fetch_latest_year,
fetch_current_download_url, fetch_postcode_energy) are thin wrappers, same
pattern as every other Phase 1/2 fetcher.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cholsey_pipeline.fetch.desnz_postcode_energy import (
    FILENAME_PATTERNS,
    DesnzDiscoveryError,
    discover_download_url,
    find_latest_year,
    parse_postcode_csv,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "desnz_postcode_energy"

# Real snippet of the sub-national electricity collection page's HTML,
# verified live 2026-09-29 -- includes both modern (2022-2024) and older
# "experimental" postcode-level slugs, to confirm the pattern only matches
# the modern ones.
REAL_COLLECTION_HTML_SNIPPET = """
<a href="/government/statistics/postcode-level-electricity-statistics-2022">2022</a>
<a href="/government/statistics/postcode-level-electricity-statistics-2023">2023</a>
<a href="/government/statistics/postcode-level-electricity-statistics-2024">2024</a>
<a href="/government/statistics/postcode-level-electricity-estimates-2013-experimental">2013</a>
"""

REAL_LANDING_HTML_SNIPPET = """
<a href="https://assets.publishing.service.gov.uk/media/694282a1fdbd8404f9e1f1da/
Postcode_level_all_meters_electricity_2024.csv">All meters</a>
<a href="https://assets.publishing.service.gov.uk/media/694283c0143d960161547d54/
Postcode_level_economy_7_electricity_2024.csv">Economy 7</a>
""".replace("/\n", "/")


class TestFindLatestYear:
    def test_finds_max_year_from_real_snippet(self) -> None:
        assert find_latest_year(REAL_COLLECTION_HTML_SNIPPET, "electricity") == 2024

    def test_ignores_experimental_slug(self) -> None:
        """The 2013 "experimental" page uses a different slug shape and
        must not be picked up as year 2013 by accident."""
        html = (
            '<a href="/government/statistics/'
            'postcode-level-electricity-estimates-2013-experimental">x</a>'
        )
        with pytest.raises(DesnzDiscoveryError):
            find_latest_year(html, "electricity")

    def test_no_match_raises(self) -> None:
        with pytest.raises(DesnzDiscoveryError, match="No postcode-level"):
            find_latest_year("<html>nothing</html>", "gas")


class TestDiscoverDownloadUrl:
    def test_finds_all_meters_link_not_economy_7(self) -> None:
        url = discover_download_url(REAL_LANDING_HTML_SNIPPET, FILENAME_PATTERNS["electricity"])
        assert url.endswith("Postcode_level_all_meters_electricity_2024.csv")

    def test_no_match_raises(self) -> None:
        with pytest.raises(DesnzDiscoveryError):
            discover_download_url("<html></html>", FILENAME_PATTERNS["gas"])


class TestParsePostcodeCsv:
    def test_real_ox10_electricity_values(self) -> None:
        """Real values verified live 2026-09-29 while building this
        module."""
        csv_text = (FIXTURES_DIR / "ox10_electricity_2024_sample.csv").read_text()
        records = parse_postcode_csv(csv_text, 2024)
        total_row = next(r for r in records if r.is_outcode_total)
        assert total_row.outcode == "OX10"
        assert total_row.number_of_meters == 13168
        assert total_row.total_consumption_kwh == pytest.approx(51917017.12, abs=0.1)

        specific = next(r for r in records if r.postcode == "OX10 0AD")
        assert specific.number_of_meters == 11
        assert not specific.is_outcode_total

    def test_real_ox10_gas_values(self) -> None:
        csv_text = (FIXTURES_DIR / "ox10_gas_2024_sample.csv").read_text()
        records = parse_postcode_csv(csv_text, 2024)
        total_row = next(r for r in records if r.is_outcode_total)
        assert total_row.number_of_meters == 11078
        assert total_row.total_consumption_kwh == pytest.approx(127598611.87, abs=1)

    def test_filters_to_requested_outcodes(self) -> None:
        csv_text = (FIXTURES_DIR / "ox10_electricity_2024_sample.csv").read_text()
        records = parse_postcode_csv(csv_text, 2024, outcodes={"OX9"})
        assert records == []

    def test_year_is_attached(self) -> None:
        csv_text = (FIXTURES_DIR / "ox10_electricity_2024_sample.csv").read_text()
        records = parse_postcode_csv(csv_text, 2024)
        assert all(r.year == 2024 for r in records)
