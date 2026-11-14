# Backtest — EMA · Supertrend · Market Structure

Dibuat 2026-11-14 04:57 UTC · data Binance spot · koin: BTCUSDT · biaya 0.15% per sisi (fee + slippage) · long/flat (spot, tanpa leverage).

- **Train** (untuk memilih formula): 2019-01-01 s/d 2024-01-01 (eksklusif).
- **Test / out-of-sample** (tidak pernah dipakai memilih): 2024-01-01 s/d data terakhir.
- Sinyal dihitung saat candle close, eksekusi di open candle berikutnya.
- Ranking = Sharpe di periode train. Dengan satu koin risiko kebetulan lebih besar, jadi perhatikan tabel per keluarga formula dan walk-forward, bukan hanya peringkat #1.

## Timeframe 1h

Buy & hold — train: Sharpe 1.06, CAGR +63%, MaxDD +77% · test: Sharpe 0.57, CAGR +17%, MaxDD +54%

**Per keluarga formula** (median semua kombinasi parameter; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1 | 1.06 | 0.57 | +17% | +54% | – |
| `EMA_CROSS` | 3 | 0.88 | 0.02 | -4% | +58% | 0% |
| `ST+HTF_ST` | 12 | 0.89 | -0.49 | -14% | +55% | 0% |
| `ST+EMA_CROSS` | 36 | 0.58 | -0.58 | -17% | +61% | 0% |
| `ST+HTF_CLOSE>EMA50` | 12 | 0.67 | -0.66 | -19% | +65% | 0% |
| `ST` | 12 | 0.71 | -0.67 | -23% | +69% | 0% |
| `STRUCT` | 3 | 0.26 | -0.70 | -24% | +62% | 0% |
| `ST+STRUCT` | 36 | 0.21 | -0.95 | -26% | +67% | 0% |
| `SCORE>=` | 36 | -0.07 | -1.12 | -24% | +63% | 0% |
| `STRUCT+CLOSE>EMA` | 9 | -0.27 | -1.23 | -32% | +72% | 0% |
| `ST+CLOSE>EMA` | 36 | 0.08 | -1.34 | -33% | +77% | 0% |
| `CLOSE>EMA` | 4 | -0.39 | -1.94 | -48% | +88% | 0% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `ST+HTF_ST(st=7/4, htf_st=10/3)` | 1.18 | +47% | +37% | **-0.33** | **-12%** | **+47%** | +36% | 50.8 | +35% |
| 2 | `ST+HTF_ST(st=20/4, htf_st=10/3)` | 1.18 | +46% | +40% | **-0.22** | **-9%** | **+45%** | +35% | 48.4 | +36% |
| 3 | `ST+HTF_CLOSE>EMA50(st=7/4)` | 1.17 | +47% | +58% | **-0.58** | **-18%** | **+61%** | +40% | 79.0 | +25% |
| 4 | `ST+HTF_ST(st=14/4, htf_st=10/3)` | 1.09 | +42% | +36% | **-0.29** | **-11%** | **+48%** | +35% | 49.1 | +36% |
| 5 | `ST+HTF_ST(st=10/4, htf_st=10/3)` | 1.09 | +42% | +36% | **-0.29** | **-11%** | **+50%** | +36% | 49.8 | +34% |
| 6 | `ST+HTF_CLOSE>EMA50(st=10/4)` | 1.05 | +40% | +60% | **-0.53** | **-17%** | **+65%** | +40% | 77.0 | +25% |
| 7 | `ST+EMA_CROSS(st=7/4, ema=50/200)` | 1.03 | +37% | +35% | **-0.31** | **-11%** | **+46%** | +35% | 52.6 | +32% |
| 8 | `ST+HTF_CLOSE>EMA50(st=20/4)` | 0.99 | +37% | +62% | **-0.43** | **-15%** | **+62%** | +40% | 76.3 | +26% |
| 9 | `ST+EMA_CROSS(st=7/4, ema=50/100)` | 0.98 | +36% | +60% | **-0.54** | **-16%** | **+59%** | +38% | 59.5 | +31% |
| 10 | `EMA_CROSS(ema=50/100)` | 0.98 | +41% | +75% | **0.02** | **-4%** | **+61%** | +52% | 40.4 | +29% |
| 11 | `ST+EMA_CROSS(st=7/4, ema=20/50)` | 0.98 | +38% | +58% | **-0.57** | **-19%** | **+61%** | +45% | 78.7 | +28% |
| 12 | `ST(st=7/4)` | 0.95 | +38% | +75% | **-0.56** | **-20%** | **+58%** | +50% | 73.1 | +32% |

<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.06 | +63% | +77% | 0.57 | +17% | +54% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 0.88 | +35% | +67% | 0.29 | +4% | +47% | 28.2 |
| `CLOSE>EMA(ema=200)` | 0.37 | +7% | +78% | -0.87 | -28% | +74% | 164.0 |
| `ST(st=10/3)` | 0.59 | +18% | +78% | -0.62 | -22% | +69% | 105.5 |
| `STRUCT(swing=5)` | 0.26 | +1% | +77% | -0.70 | -24% | +62% | 107.6 |
| `ST+CLOSE>EMA(st=10/3, ema=200)` | 0.35 | +6% | +71% | -0.80 | -22% | +71% | 131.6 |
| `ST+EMA_CROSS(st=10/3, ema=50/200)` | 0.49 | +12% | +51% | -0.28 | -9% | +54% | 67.9 |
| `ST+STRUCT(st=10/3, swing=5)` | 0.32 | +5% | +70% | -0.99 | -28% | +68% | 108.0 |
| `SCORE>=(k=3, st=10/3, ema=50/200, swing=5)` | 0.09 | -4% | +74% | -1.26 | -32% | +77% | 174.5 |
| `SCORE>=(k=4, st=10/3, ema=50/200, swing=5)` | -0.16 | -10% | +65% | -0.99 | -22% | +59% | 104.5 |
| `ST+HTF_ST(st=10/3, htf_st=10/3)` | 0.80 | +26% | +43% | -0.29 | -10% | +51% | 65.5 |

</details>

**Walk-forward 1h** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Return | Buy & hold |
|---|---|---|---|
| 2022 | `ST(st=7/4)` | -57% | -64% |
| 2023 | `ST+EMA_CROSS(st=7/4, ema=50/200)` | +18% | +156% |
| 2024 | `ST+HTF_ST(st=20/4, htf_st=10/3)` | +18% | +121% |
| 2025 | `EMA_CROSS(ema=50/200)` | -29% | -6% |
| 2026 | `BUY_HOLD` | -24% | -24% |

Total walk-forward 2022–2026: BTC -68% (B&H +44%)

## Timeframe 4h

Buy & hold — train: Sharpe 1.07, CAGR +63%, MaxDD +77% · test: Sharpe 0.58, CAGR +17%, MaxDD +53%

**Per keluarga formula** (median semua kombinasi parameter; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `STRUCT` | 3 | 0.97 | 0.80 | +23% | +40% | 100% |
| `EMA_CROSS` | 3 | 1.34 | 0.76 | +21% | +31% | 100% |
| `SCORE>=` | 36 | 1.52 | 0.73 | +15% | +26% | 83% |
| `STRUCT+CLOSE>EMA` | 9 | 1.17 | 0.70 | +17% | +32% | 67% |
| `ST+HTF_CLOSE>EMA50` | 12 | 1.34 | 0.61 | +13% | +29% | 75% |
| `ST+EMA_CROSS` | 36 | 1.41 | 0.58 | +12% | +28% | 56% |
| `BUY_HOLD` | 1 | 1.07 | 0.58 | +17% | +53% | – |
| `ST+STRUCT` | 36 | 1.16 | 0.37 | +7% | +35% | 33% |
| `ST+CLOSE>EMA` | 36 | 1.26 | 0.31 | +5% | +38% | 6% |
| `ST` | 12 | 1.25 | 0.20 | +1% | +42% | 0% |
| `ST+HTF_ST` | 12 | 1.30 | 0.07 | -1% | +42% | 0% |
| `CLOSE>EMA` | 4 | 1.00 | 0.03 | -3% | +54% | 0% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `SCORE>=(k=4, st=14/4, ema=50/200, swing=5)` | 1.72 | +71% | +33% | **0.71** | **+14%** | **+26%** | +26% | 24.0 | +33% |
| 2 | `SCORE>=(k=5, st=14/4, ema=50/200, swing=5)` | 1.72 | +71% | +33% | **0.71** | **+14%** | **+26%** | +26% | 24.0 | +33% |
| 3 | `SCORE>=(k=4, st=10/4, ema=50/200, swing=5)` | 1.67 | +69% | +33% | **0.69** | **+14%** | **+28%** | +26% | 24.4 | +34% |
| 4 | `SCORE>=(k=5, st=10/4, ema=50/200, swing=5)` | 1.67 | +69% | +33% | **0.69** | **+14%** | **+28%** | +26% | 24.4 | +34% |
| 5 | `SCORE>=(k=4, st=20/4, ema=50/200, swing=5)` | 1.67 | +68% | +33% | **0.68** | **+13%** | **+27%** | +26% | 24.4 | +33% |
| 6 | `SCORE>=(k=5, st=20/4, ema=50/200, swing=5)` | 1.67 | +68% | +33% | **0.68** | **+13%** | **+27%** | +26% | 24.4 | +33% |
| 7 | `SCORE>=(k=4, st=7/3, ema=50/200, swing=5)` | 1.67 | +68% | +32% | **0.75** | **+15%** | **+20%** | +26% | 23.7 | +34% |
| 8 | `SCORE>=(k=5, st=7/3, ema=50/200, swing=5)` | 1.67 | +68% | +32% | **0.75** | **+15%** | **+20%** | +26% | 23.7 | +34% |
| 9 | `ST+EMA_CROSS(st=20/4, ema=50/200)` | 1.65 | +72% | +36% | **0.43** | **+8%** | **+39%** | +33% | 13.2 | +26% |
| 10 | `ST+EMA_CROSS(st=10/4, ema=50/200)` | 1.62 | +71% | +38% | **0.58** | **+11%** | **+34%** | +32% | 12.9 | +27% |
| 11 | `ST+EMA_CROSS(st=7/3, ema=50/200)` | 1.60 | +68% | +34% | **0.59** | **+12%** | **+28%** | +31% | 17.1 | +35% |
| 12 | `ST+EMA_CROSS(st=14/4, ema=50/200)` | 1.60 | +70% | +37% | **0.33** | **+5%** | **+38%** | +32% | 13.6 | +26% |

<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.07 | +63% | +77% | 0.58 | +17% | +53% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 1.54 | +85% | +59% | 0.91 | +27% | +31% | 6.3 |
| `CLOSE>EMA(ema=200)` | 1.46 | +78% | +43% | 0.34 | +6% | +44% | 39.3 |
| `ST(st=10/3)` | 1.28 | +61% | +47% | 0.36 | +7% | +40% | 26.1 |
| `STRUCT(swing=5)` | 1.23 | +59% | +72% | 0.80 | +23% | +40% | 24.4 |
| `ST+CLOSE>EMA(st=10/3, ema=200)` | 1.41 | +63% | +34% | 0.47 | +9% | +28% | 33.4 |
| `ST+EMA_CROSS(st=10/3, ema=50/200)` | 1.56 | +67% | +34% | 0.74 | +16% | +26% | 16.7 |
| `ST+STRUCT(st=10/3, swing=5)` | 1.27 | +57% | +56% | 0.47 | +10% | +36% | 26.5 |
| `SCORE>=(k=3, st=10/3, ema=50/200, swing=5)` | 1.39 | +63% | +44% | 0.52 | +11% | +28% | 46.0 |
| `SCORE>=(k=4, st=10/3, ema=50/200, swing=5)` | 1.54 | +61% | +40% | 0.81 | +17% | +18% | 24.4 |
| `ST+HTF_ST(st=10/3, htf_st=10/3)` | 1.35 | +52% | +36% | 0.13 | +0% | +39% | 15.7 |

</details>

**Walk-forward 4h** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Return | Buy & hold |
|---|---|---|---|
| 2022 | `SCORE>=(k=4, st=14/4, ema=50/200, swing=5)` | -22% | -64% |
| 2023 | `SCORE>=(k=4, st=14/4, ema=50/200, swing=5)` | +73% | +156% |
| 2024 | `ST+CLOSE>EMA(st=20/4, ema=200)` | +19% | +121% |
| 2025 | `STRUCT+CLOSE>EMA(swing=5, ema=200)` | -2% | -6% |
| 2026 | `STRUCT+CLOSE>EMA(swing=10, ema=200)` | +0% | -24% |

Total walk-forward 2022–2026: BTC +59% (B&H +44%)

## Timeframe 1d

Buy & hold — train: Sharpe 1.06, CAGR +63%, MaxDD +77% · test: Sharpe 0.59, CAGR +18%, MaxDD +53%

**Per keluarga formula** (median semua kombinasi parameter; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `STRUCT+CLOSE>EMA` | 9 | 1.36 | 0.66 | +17% | +33% | 78% |
| `CLOSE>EMA` | 4 | 1.17 | 0.64 | +18% | +34% | 75% |
| `ST+CLOSE>EMA` | 36 | 1.27 | 0.62 | +14% | +35% | 53% |
| `STRUCT` | 3 | 1.05 | 0.59 | +15% | +39% | 67% |
| `BUY_HOLD` | 1 | 1.06 | 0.59 | +18% | +53% | – |
| `EMA_CROSS` | 3 | 0.89 | 0.59 | +15% | +37% | 33% |
| `ST+STRUCT` | 36 | 1.31 | 0.57 | +13% | +36% | 44% |
| `ST+EMA_CROSS` | 36 | 1.13 | 0.57 | +13% | +39% | 36% |
| `ST+HTF_ST` | 12 | 1.16 | 0.55 | +12% | +41% | 17% |
| `ST` | 12 | 1.24 | 0.53 | +13% | +45% | 33% |
| `SCORE>=` | 36 | 1.10 | 0.53 | +11% | +30% | 33% |
| `ST+HTF_CLOSE>EMA50` | 12 | 1.04 | 0.52 | +11% | +41% | 8% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `STRUCT+CLOSE>EMA(swing=10, ema=50)` | 1.54 | +82% | +34% | **0.58** | **+14%** | **+28%** | +44% | 8.4 | +33% |
| 2 | `ST+CLOSE>EMA(st=14/4, ema=50)` | 1.53 | +78% | +37% | **0.78** | **+21%** | **+34%** | +48% | 8.0 | +30% |
| 3 | `ST+STRUCT(st=7/3, swing=10)` | 1.52 | +78% | +39% | **0.42** | **+8%** | **+36%** | +41% | 4.2 | +50% |
| 4 | `STRUCT+CLOSE>EMA(swing=5, ema=100)` | 1.52 | +76% | +36% | **0.61** | **+15%** | **+34%** | +43% | 7.3 | +33% |
| 5 | `ST+CLOSE>EMA(st=7/3, ema=100)` | 1.47 | +74% | +44% | **0.55** | **+12%** | **+31%** | +44% | 5.6 | +38% |
| 6 | `ST+STRUCT(st=7/2, swing=10)` | 1.47 | +66% | +41% | **0.52** | **+11%** | **+36%** | +33% | 5.6 | +44% |
| 7 | `SCORE>=(k=3, st=7/3, ema=50/200, swing=5)` | 1.45 | +71% | +52% | **0.84** | **+24%** | **+26%** | +44% | 6.6 | +37% |
| 8 | `ST+EMA_CROSS(st=14/4, ema=20/50)` | 1.45 | +73% | +34% | **0.76** | **+21%** | **+42%** | +54% | 2.8 | +50% |
| 9 | `ST+CLOSE>EMA(st=14/4, ema=100)` | 1.45 | +73% | +31% | **0.71** | **+19%** | **+39%** | +54% | 5.2 | +33% |
| 10 | `ST+STRUCT(st=14/4, swing=3)` | 1.45 | +68% | +39% | **0.93** | **+26%** | **+28%** | +41% | 4.5 | +62% |
| 11 | `STRUCT+CLOSE>EMA(swing=5, ema=50)` | 1.45 | +73% | +46% | **0.60** | **+15%** | **+35%** | +45% | 9.8 | +32% |
| 12 | `ST+CLOSE>EMA(st=7/4, ema=100)` | 1.45 | +75% | +36% | **0.69** | **+19%** | **+40%** | +53% | 5.2 | +33% |

<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.06 | +63% | +77% | 0.59 | +18% | +53% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 0.77 | +31% | +71% | 0.77 | +26% | +35% | 0.3 |
| `CLOSE>EMA(ema=200)` | 1.07 | +50% | +56% | 0.63 | +18% | +36% | 6.6 |
| `ST(st=10/3)` | 1.18 | +55% | +54% | 0.20 | +1% | +47% | 5.2 |
| `STRUCT(swing=5)` | 1.26 | +64% | +51% | 0.66 | +18% | +38% | 4.9 |
| `ST+CLOSE>EMA(st=10/3, ema=200)` | 1.19 | +50% | +42% | 0.37 | +7% | +37% | 4.5 |
| `ST+EMA_CROSS(st=10/3, ema=50/200)` | 0.99 | +36% | +51% | 0.21 | +2% | +41% | 4.2 |
| `ST+STRUCT(st=10/3, swing=5)` | 1.28 | +59% | +54% | 0.35 | +6% | +40% | 5.6 |
| `SCORE>=(k=3, st=10/3, ema=50/200, swing=5)` | 1.34 | +63% | +52% | 0.85 | +24% | +27% | 6.6 |
| `SCORE>=(k=4, st=10/3, ema=50/200, swing=5)` | 1.01 | +35% | +51% | 0.37 | +7% | +37% | 5.6 |
| `ST+HTF_ST(st=10/3, htf_st=10/3)` | 1.10 | +39% | +43% | 0.16 | +1% | +41% | 4.2 |

</details>

**Walk-forward 1d** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Return | Buy & hold |
|---|---|---|---|
| 2022 | `ST+STRUCT(st=7/3, swing=10)` | -20% | -64% |
| 2023 | `SCORE>=(k=3, st=7/3, ema=50/200, swing=5)` | +69% | +156% |
| 2024 | `SCORE>=(k=3, st=7/3, ema=50/200, swing=5)` | +76% | +121% |
| 2025 | `ST+STRUCT(st=14/4, swing=3)` | -3% | -6% |
| 2026 | `CLOSE>EMA(ema=50)` | -5% | -22% |

Total walk-forward 2022–2026: BTC +119% (B&H +48%)

