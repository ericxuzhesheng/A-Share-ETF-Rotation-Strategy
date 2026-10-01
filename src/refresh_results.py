"""Refresh market data and results using the published, fixed parameters."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

import pandas as pd

from .config import BASE_DIR, BENCHMARK_CODE, OOS_START_DATE, START_DATE, THREE_CLASS_MAP, TRAIN_END_DATE
from .data_loader import load_trading_calendar, load_tushare_daily
from .pipeline import plot_results, run_backtest_on_period


def load_saved_parameters(path: Path) -> dict:
    parameters = {}
    for row in pd.read_csv(path, dtype=str).itertuples(index=False):
        try:
            parameters[row.parameter] = ast.literal_eval(row.value)
        except (ValueError, SyntaxError):
            parameters[row.parameter] = row.value
    return parameters


def validate_prices(frame: pd.DataFrame, symbol: str, cutoff: pd.Timestamp) -> None:
    if frame.empty or frame["date"].max() != cutoff:
        raise ValueError(f"{symbol}: market data does not reach {cutoff.date()}")
    if frame["date"].duplicated().any() or not frame["date"].is_monotonic_increasing:
        raise ValueError(f"{symbol}: duplicate or unordered market dates")
    prices = frame[["open", "high", "low", "close"]]
    if prices.isna().any().any() or (prices <= 0).any().any():
        raise ValueError(f"{symbol}: invalid OHLC prices")


def refresh_results(as_of: str | None = None, output_dir: Path = BASE_DIR / "results", *, from_snapshot: bool = False) -> dict:
    requested = pd.Timestamp(as_of or pd.Timestamp.now(tz="Asia/Shanghai").strftime("%Y-%m-%d"))
    calendar = load_trading_calendar()
    if not calendar.iloc[0] <= requested <= calendar.iloc[-1]:
        raise ValueError("Requested date is outside verified calendar coverage")
    cutoff = calendar[calendar <= requested].iloc[-1]
    future_sessions = calendar[calendar > cutoff]
    if future_sessions.empty:
        raise ValueError("Next execution session is not available in the calendar")
    cutoff_text = cutoff.strftime("%Y-%m-%d")
    parameters = load_saved_parameters(BASE_DIR / "results" / "best_parameters.csv")
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / "market_data.csv.gz"
    snapshot = pd.read_csv(snapshot_path, parse_dates=["date"]) if from_snapshot else None
    data = {}
    for symbol in dict.fromkeys([*THREE_CLASS_MAP, BENCHMARK_CODE]):
        frame = (snapshot.loc[snapshot["symbol"] == symbol].copy() if snapshot is not None
                 else load_tushare_daily(symbol, START_DATE, cutoff_text))
        frame = frame.loc[frame["date"] <= cutoff].reset_index(drop=True)
        validate_prices(frame, symbol, cutoff)
        if not frame["date"].isin(calendar).all():
            raise ValueError(f"{symbol}: prices include a non-trading date")
        data[symbol] = frame
        print(f"Loaded {symbol}: {len(frame)} rows through {cutoff_text}", flush=True)

    if not from_snapshot:
        pd.concat(data.values(), ignore_index=True).to_csv(snapshot_path, index=False, encoding="utf-8")
    universe = {symbol: data[symbol] for symbol in THREE_CLASS_MAP}
    benchmark = data[BENCHMARK_CODE]
    train = run_backtest_on_period(parameters, universe, benchmark, "Training Set", START_DATE, TRAIN_END_DATE, output_dir)
    test = run_backtest_on_period(parameters, universe, benchmark, "Test Set (OOS)", OOS_START_DATE, cutoff_text, output_dir)
    for label, result in [("train", train), ("test", test)]:
        equity, trades, metrics, targets = result
        if equity is None or equity.empty or metrics is None:
            raise ValueError(f"No valid {label} backtest output")
        equity.to_csv(output_dir / f"equity_curve_{label}.csv", index=False, encoding="utf-8-sig")
        trades.to_csv(output_dir / f"trading_log_{label}.csv", index=False, encoding="utf-8-sig")
        targets.to_csv(output_dir / f"top10_scored_targets_{label}.csv", index=False, encoding="utf-8-sig")
    if test[0]["date"].max() != cutoff:
        raise ValueError("Backtest did not reach the market-data cutoff")
    pd.DataFrame([
        {"period": "Training (2009-2019)", **train[2]},
        {"period": "Test (2020-Present)", **test[2]},
    ]).to_csv(output_dir / "metrics_comparison.csv", index=False, encoding="utf-8-sig")
    plot_results(train[0], test[0], parameters, output_dir)
    manifest = {
        "requested_as_of": requested.strftime("%Y-%m-%d"),
        "data_cutoff": cutoff_text,
        "next_execution_date": future_sessions.iloc[0].strftime("%Y-%m-%d"),
        "parameter_source": "results/best_parameters.csv",
        "parameters_retuned": False,
        "universe_count": len(universe),
        "benchmark": BENCHMARK_CODE,
        "data_loader": "Tushare fund_daily with existing AkShare fallback and split repair",
        "asset_coverage": {
            symbol: {"first_date": frame["date"].min().strftime("%Y-%m-%d"),
                     "last_date": frame["date"].max().strftime("%Y-%m-%d"), "rows": len(frame)}
            for symbol, frame in data.items()
        },
    }
    (output_dir / "refresh_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Refresh complete: {cutoff_text}; next execution {manifest['next_execution_date']}")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", help="Resolve the last exchange session on or before YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, default=BASE_DIR / "results")
    parser.add_argument("--from-snapshot", action="store_true", help="Reuse the saved market_data.csv.gz")
    args = parser.parse_args()
    refresh_results(args.as_of, args.output_dir, from_snapshot=args.from_snapshot)
