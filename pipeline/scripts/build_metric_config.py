"""Regenerate `web/src/data/metric_config.json` from `config/metrics.yaml`
(ADR-0013). Cheap and offline -- unlike `build_metrics_csv.py`, no fetches."""

from cholsey_pipeline.export import build_metric_config_json, write_json
from cholsey_pipeline.registry import REPO_ROOT, load_metrics, load_tile_groups

PATH = REPO_ROOT / "web" / "src" / "data" / "metric_config.json"

if __name__ == "__main__":
    write_json(build_metric_config_json(load_metrics(), load_tile_groups()), PATH)
    print(f"Wrote {PATH}")
