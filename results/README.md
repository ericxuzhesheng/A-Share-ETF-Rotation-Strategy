# Results / 回测结果

本次刷新截止 **2026-09-30**：37 只策略 ETF 与 510300.SH 基准均通过行情截止日检查。
沿用 `best_parameters.csv`，没有重新搜索参数。9 月 30 日信号计划于 **2026-10-08**
执行；该日期不计入回测，也不代表已成交。

Current data cutoff: **2026-09-30** for all 37 strategy ETFs and the benchmark.
Published parameters are unchanged. The next execution session is **2026-10-08**;
this is a future plan, not an executed backtest trade.

## 文件一览 · Files

| 文件 | 说明 |
| --- | --- |
| `best_parameters.csv` | 沿用的已保存参数，本次未重新优化 |
| `market_data.csv.gz` | 本次使用的完整 OHLCV 输入，经过现有拆分异常修复 |
| `refresh_manifest.json` | 截止日、下一交易日、逐标的起止日期与行数 |
| `metrics_comparison.csv` | 训练期与样本外区间完整指标 |
| `equity_curve_train.csv`, `equity_curve_test.csv` | 日频净值、仓位、基准及回撤 |
| `trading_log_train.csv`, `trading_log_test.csv` | 交易明细 |
| `top10_scored_targets_train.csv`, `top10_scored_targets_test.csv` | 各区间末日候选评分 |
| `next_trade_holdings_20260930_to_20261008.csv` | 当前节后持仓计划 |
| `train_test_comparison.png` | 最新样本外净值、超额净值与回撤图 |
| `timing_fix_compare/` | 2026 年 4 月时序审计历史对照，非本次结果 |

旧的带日期持仓文件保留为历史快照。全网格搜索结果不由固定参数刷新生成。
Dated older holdings are historical snapshots; this refresh does not generate a new search grid.

## 关键指标 · Metrics

训练窗配置为 2009–2019，实际可用策略行情从 2013-12-16 开始。
The configured training window is 2009–2019; actual strategy coverage starts on 2013-12-16.

| Metric | Training (through 2019-12-31) | OOS (2020-01-02 to 2026-09-30) |
| --- | ---: | ---: |
| Annual return | 2.25% | 8.65% |
| Sharpe ratio | 0.2717 | 0.4726 |
| Max drawdown | -21.48% | -36.26% |
| Calmar ratio | 0.10 | 0.24 |
| Win rate | 38.38% | 39.67% |
| Avg holding days | 16.1 | 13.3 |

结果使用已修正交易时序的现有引擎。保留现有成本参数：单边手续费 0.03%、
单边滑点 0.05%，以及引擎中的额外卖出费用 0.1%。与旧快照相比，结果变化包含
新增行情、此前的时序修正以及房地产 ETF 代码纠正带来的标的覆盖变化。

Results use the existing engine with corrected execution timing and unchanged cost assumptions:
0.03% one-way commission, 0.05% slippage, plus the engine's 0.1% additional sell charge.
Changes versus older snapshots reflect the extended data, prior timing corrections and restored
coverage of the real-estate ETF (512200.SH).

## 复现 · Reproduction

```bash
export TUSHARE_TOKEN=<your_token>
python -m src.refresh_results --as-of 2026-10-02
```

国庆休市日期会解析到 9 月 30 日。输出在 `results/`；行情缺失会报错，不能静默跳过标的。
复用已保存行情（交易日历仍需联网）：

```bash
python -m src.refresh_results --as-of 2026-10-02 --from-snapshot
```

The holiday date resolves to September 30. Outputs go to `results/`. Missing or stale symbols
block publication. `--from-snapshot` reuses saved prices; calendar verification still needs network access.

`python -m src.pipeline` 继续用于完整参数搜索，输出至 `ETF_Result/`。
每周任务使用固定参数刷新，结果保存在 Actions 的 `etf-rotation-results` artifact，保留 30 天。

The original full parameter-search pipeline writes to `ETF_Result/`. Weekly jobs refresh saved
parameters and retain outputs in the `etf-rotation-results` Actions artifact for 30 days.
