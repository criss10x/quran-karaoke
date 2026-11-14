# crypto MTF analysis — notes for coding agents

Multi-timeframe crypto TA from Binance spot candles: EMA 50/200, Supertrend, market structure.
Pipeline: `cta/data.py` (klines) → `cta/indicators.py` + `cta/structure.py` → `cta/analysis.py`
(per-TF score, confluence) → `cta/report.py` (Markdown) ← `cta/cli.py`.

## Invariants

- **Stdlib only.** No pandas/numpy/requests — the skill and the GitHub workflow run with a bare
  Python ≥ 3.9. Don't use 3.12-only syntax (nested same-quote f-strings).
- **No look-ahead in structure.** A swing at bar `i` is only usable from bar `i + right + 1`
  (`find_breaks`). `tests/test_cta.py::test_no_lookahead` guards it.
- **Closed candles by default.** `fetch_klines` drops the forming candle unless `include_open`.
- **Indicator definitions match TradingView** (`ta.ema`, `ta.rma`, `ta.supertrend`), SMA-seeded.
  Supertrend direction here is `+1 = up` (Pine's sign is inverted).
- Report text is Indonesian; code, JSON keys and comments are English.

## Checks

```bash
python3 tests/test_cta.py                 # offline unit tests
python3 -m cta BTC --tf 1h 4h 1d          # live smoke test (needs data-api.binance.vision)
```

Network: the cloud environment must allow `data-api.binance.vision`; `api.binance.com` returns
HTTP 451 from restricted regions (handled as "try next host").
