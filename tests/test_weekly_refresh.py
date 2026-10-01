import sys

import pytest

from scripts import send_weekly_signal as weekly


def test_historical_run_passes_data_cutoff_without_retuning(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["send_weekly_signal.py", "--date", "2026-09-30", "--force-run"])
    monkeypatch.setattr(weekly, "run_pipeline", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(weekly, "NOTIFY_AFTER_WEEKLY_SIGNAL", False)
    weekly.main()
    assert calls == [{"as_of": "2026-09-30", "output_dir": weekly.OUTPUT_DIR}]


def test_closed_session_never_fetches_or_notifies(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["send_weekly_signal.py", "--date", "2026-09-25"])
    monkeypatch.setattr(weekly, "is_last_trading_day_of_week", lambda date: False)
    def unexpected(*args, **kwargs):
        pytest.fail("A closed session must not fetch data or notify")
    monkeypatch.setattr(weekly, "run_pipeline", unexpected)
    monkeypatch.setattr(weekly, "push_serverchan_notification", unexpected)
    with pytest.raises(SystemExit) as result:
        weekly.main()
    assert result.value.code == 0
