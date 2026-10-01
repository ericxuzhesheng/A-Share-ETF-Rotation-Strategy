"""Regressions for holiday-shortened signal weeks and unavailable calendars."""

import pandas as pd
import pytest

from src import data_loader


@pytest.fixture(autouse=True)
def public_calendar(monkeypatch):
    monkeypatch.setattr(data_loader, "_retry_fetch", lambda fetcher, **kwargs: fetcher())
    monkeypatch.setattr(data_loader.ak, "tool_trade_date_hist_sina", lambda: pd.DataFrame({
        "trade_date": ["2026-09-23", "2026-09-24", "2026-09-28", "2026-09-29", "2026-09-30", "2026-10-08", "2026-10-09", "2026-10-12"],
    }))


@pytest.mark.parametrize("day, expected", [
    ("2026-09-23", False), ("2026-09-24", True), ("2026-09-25", False),
    ("2026-09-28", False), ("2026-09-30", True), ("2026-10-01", False),
    ("2026-10-08", False), ("2026-10-09", True), ("2026-10-10", False),
])
def test_weekly_signal_respects_exchange_holidays(day, expected):
    assert data_loader.is_last_trading_day_of_week(day) == expected


def test_calendar_outage_does_not_run_on_a_holiday_friday(monkeypatch):
    def fail():
        raise OSError("calendar unavailable")
    monkeypatch.setattr(data_loader.ak, "tool_trade_date_hist_sina", fail)
    with pytest.raises(RuntimeError, match="Cannot verify the weekly trading calendar"):
        data_loader.is_last_trading_day_of_week("2026-09-25")


@pytest.mark.parametrize("day", ["2025-09-25", "2026-10-12", "2027-01-01"])
def test_unknown_calendar_coverage_does_not_guess(day):
    with pytest.raises(RuntimeError, match="Cannot verify the weekly trading calendar"):
        data_loader.is_last_trading_day_of_week(day)


@pytest.mark.parametrize("day, expected", [
    ("2026-09-24", "2026-09-28"), ("2026-09-30", "2026-10-08"),
    ("2026-10-01", "2026-10-08"), ("2026-10-09", "2026-10-12"),
])
def test_next_execution_skips_exchange_holidays(day, expected):
    assert data_loader.get_next_trading_day(day) == pd.Timestamp(expected)


def test_next_execution_fails_without_future_calendar():
    with pytest.raises(ValueError, match="coverage"):
        data_loader.get_next_trading_day("2026-10-12")
