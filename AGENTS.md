# crypto MTF analysis — notes for coding agents

Multi-timeframe crypto TA from Binance spot candles: EMA 50/200, Stoch RSI 14, market structure.
Pipeline: `cta/data.py` (klines) → `cta/indicators.py` + `cta/structure.py` → `cta/analysis.py`
(per-TF score, confluence) → `cta/report.py` (Markdown) ← `cta/cli.py`.
Backtest: `cta/backtest.py` (rules, simulation, metrics) ← `cta/research.py` (grid, train/test,
walk-forward, `docs/backtest.md`). Conclusions live in `docs/formula.md`, which is hand-written.
Update it only after re-running the research.

## Invariants

- **Stdlib only.** No pandas/numpy/requests — the skill and the GitHub workflow run with a bare
  Python ≥ 3.9. Don't use 3.12-only syntax (nested same-quote f-strings).
- **No look-ahead in structure.** A swing at bar `i` is only usable from bar `i + right + 1`
  (`find_breaks`). `tests/test_cta.py::test_no_lookahead` guards it.
- **Closed candles by default.** `fetch_klines` drops the forming candle unless `include_open`.
- **Indicator definitions match TradingView** (`ta.ema`, `ta.rma`, `ta.rsi`, "Stoch RSI"
  14/14/3/3), SMA-seeded. `tests/test_cta.py::test_rsi_matches_wilder_reference` pins RSI to the
  StockCharts worked example. Supertrend was removed on request; don't reintroduce it.
- **Live formula signals reuse `backtest.Features`** so they match the tested rules exactly
  (`test_formula_b_matches_backtest_rule`, `test_live_score_matches_backtest_features`).
- **Backtest execution:** signal at bar close, fill at the next bar's open, costs on every change.
  Choose rules on the train window only; `tests/test_cta.py::test_simulate_*` guard the fill model.
- `data/` (candle cache, research JSON) is gitignored and regenerated.
- Report text is Indonesian; code, JSON keys and comments are English.

## Checks

```bash
python3 tests/test_cta.py                 # offline unit tests
python3 -m cta BTC --tf 1h 4h 1d          # live smoke test (needs data-api.binance.vision)
python3 -m cta.research --symbols BTC --tf 1d   # quick backtest smoke test (~10 s once cached)
```

Network: the cloud environment must allow `data-api.binance.vision`; `api.binance.com` returns
HTTP 451 from restricted regions (handled as "try next host").
