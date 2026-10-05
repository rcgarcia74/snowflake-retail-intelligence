from __future__ import annotations

from merchant_demo.config import load_config


def test_locked_retention_windows(config_path) -> None:
    config = load_config(config_path)
    assert config.history_days == 90
    assert config.hot_days == 7
    assert config.affected_item_count == 3
    assert config.affected_store_count == 8
    assert config.degraded_fill_rate < config.healthy_fill_rate
