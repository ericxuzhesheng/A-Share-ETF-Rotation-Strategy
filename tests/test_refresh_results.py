import pandas as pd
import pytest

from src.refresh_results import load_saved_parameters, validate_prices


def test_saved_boolean_is_not_a_truthy_string(tmp_path):
    path = tmp_path / "parameters.csv"
    path.write_text("parameter,value\nuse_relative_strength_filter,False\nema_window,30\nexposure_map_version,aggressive\n")
    assert load_saved_parameters(path) == {
        "use_relative_strength_filter": False, "ema_window": 30, "exposure_map_version": "aggressive",
    }


@pytest.mark.parametrize("dates, close", [
    (["2026-09-29"], [1.0]),
    (["2026-09-30", "2026-09-30"], [1.0, 1.0]),
    (["2026-09-30"], [0.0]),
])
def test_incomplete_or_invalid_prices_block_publication(dates, close):
    frame = pd.DataFrame({"date": pd.to_datetime(dates), **{col: close for col in ["open", "high", "low", "close"]}})
    with pytest.raises(ValueError):
        validate_prices(frame, "512200.SH", pd.Timestamp("2026-09-30"))
