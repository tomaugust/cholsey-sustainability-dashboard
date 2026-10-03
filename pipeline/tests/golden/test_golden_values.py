"""P3.10: golden-value tests (development-plan.md Phase 3 "Tests of
success": a hand-computed value per metric, for Cholsey's latest year,
must equal the real pipeline output).

See `golden_values.py`'s own module docstring for how each value was
independently re-derived from raw source data.
"""

from __future__ import annotations

import pandas as pd
import pytest

from cholsey_pipeline.registry import REPO_ROOT

from .golden_values import GOLDEN_VALUES

METRICS_CSV_PATH = REPO_ROOT / "data" / "processed" / "metrics.csv"
CHOLSEY_CODE = "E04012474"


@pytest.fixture(scope="module")
def metrics_df() -> pd.DataFrame:
    return pd.read_csv(METRICS_CSV_PATH)


class TestGoldenValues:
    @pytest.mark.parametrize("metric_id", sorted(GOLDEN_VALUES))
    def test_cholsey_latest_year_matches_hand_computed_value(
        self, metrics_df: pd.DataFrame, metric_id: str
    ) -> None:
        rows = metrics_df[
            (metrics_df["area_code"] == CHOLSEY_CODE)
            & (metrics_df["area_role"] == "subject")
            & (metrics_df["metric_id"] == metric_id)
        ]
        assert not rows.empty, f"No Cholsey subject row for {metric_id} in metrics.csv"
        latest_row = rows.loc[rows["year"].idxmax()]
        assert latest_row["value"] == pytest.approx(GOLDEN_VALUES[metric_id], rel=1e-9)

    def test_every_built_metric_has_a_golden_value(self, metrics_df: pd.DataFrame) -> None:
        """Catches the inverse mistake: a metric built into metrics.csv
        with no golden value ever added for it."""
        built_metric_ids = set(
            metrics_df.loc[
                (metrics_df["area_code"] == CHOLSEY_CODE) & (metrics_df["area_role"] == "subject"),
                "metric_id",
            ]
        )
        assert built_metric_ids <= set(GOLDEN_VALUES)
