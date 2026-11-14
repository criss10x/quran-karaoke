---
name: crypto-mtf-analysis
description: Multi-timeframe crypto technical analysis with EMA 50/200, Supertrend (10,3) and market structure (swing HH/HL/LH/LL, BOS, CHoCH) on live Binance spot candles. Use when the user asks to analyse a coin or pair (BTC, ETH, SOL, BTCUSDT, ETHBTC, ...), asks for trend/bias, support/resistance, EMA cross, Supertrend or market structure across timeframes, or invokes /crypto-mtf-analysis. Works in Indonesian or English.
---

# Crypto multi-timeframe analysis

Tool: the `cta` package in this repository (pure Python stdlib, no install, no API key).
Data: Binance public spot klines via `data-api.binance.vision` (fallback `api.binance.com`).

## Workflow

1. **Parse the request.** Symbols (default `BTCUSDT`; a bare ticker like `sol` becomes `SOLUSDT`)
   and timeframes (default `15m 1h 4h 1d 1w`). Map the user's words: "scalping" → `1m 5m 15m 1h`,
   "intraday" → `15m 1h 4h`, "swing" → `1h 4h 1d 1w`, "jangka panjang / position" → `1d 1w 1M`.
   Only change indicator parameters if the user asks (`--ema-fast --ema-slow --st-period --st-mult --swing`).

2. **Run it from the repository root**, JSON for you to reason over:

   ```bash
   python3 -m cta BTC ETH --tf 15m 1h 4h 1d 1w --format json --out /tmp/cta.json
   ```

   and, if the user wants the full table, the Markdown report:

   ```bash
   python3 -m cta BTC ETH --tf 15m 1h 4h 1d 1w
   ```

   If every request fails with a proxy `403` / connection error, the environment's network
   policy is blocking Binance: the hosts `data-api.binance.vision` (and optionally
   `api.binance.com`) must be allowed. Say so; never invent prices or indicator values.
   HTTP 400 means an invalid symbol — suggest the correct Binance pair.

3. **Interpret, top-down** (higher timeframe first), using the JSON fields:
   - `confluence.bias`, `confluence.score_pct` (−100..+100) and `confluence.summary` — the headline.
   - Per TF: `ema.cross` (golden/death) and `ema.cross_bars_ago`; `ema.dist_fast_pct` /
     `dist_slow_pct` (price vs EMA 50/200; far from EMA = stretched); `ema.fast_slope_pct`.
   - `supertrend.direction`, `supertrend.line` (dynamic stop / trailing level),
     `supertrend.flip_bars_ago` (fresh flip = new momentum).
   - `structure.bias` (direction of the latest BOS/CHoCH), `structure.swing_trend`
     (latest HH/HL vs LH/LL), `structure.last_break` (`kind`, `direction`, `level`, `bars_ago`),
     `structure.support` / `structure.resistance` (nearest swing levels).
   - A CHoCH on a lower TF against the higher-TF bias = early reversal / end of pullback signal.
   - Disagreement between `structure.bias` and `swing_trend` = transition; say it is unconfirmed.

4. **Answer** in the user's language with:
   - one-line verdict (bias + confluence %) and last price;
   - a compact table per symbol: TF | trend EMA | Supertrend | structure | key level;
   - key levels to watch (nearest support/resistance, Supertrend line, EMA 50/200 on the HTF);
   - scenarios: what confirms continuation, what invalidates it (e.g. "close 4h di atas X = CHoCH bullish");
   - closing disclaimer: not financial advice; indicators lag; use stop losses.

## Notes

- Signals use **closed candles only** (`--include-open` to include the forming one). The weekly
  `close` is therefore last week's close — compare with `last_price` for the live picture.
- Coins with short history return `ema.slow = null` on high TFs (fewer than 200 candles); those
  score components count as 0. Mention it instead of guessing.
- Scoring, BOS/CHoCH rules and parameters are documented in `README.md`.
