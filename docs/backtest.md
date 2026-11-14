# Backtest — EMA · Stoch RSI · Market Structure

Dibuat 2026-11-14 07:46 UTC · data Binance spot · koin: BTCUSDT · biaya 0.15% per sisi (fee + slippage) · long/flat (spot, tanpa leverage).

- **Train** (untuk memilih formula): 2019-01-01 s/d 2024-01-01 (eksklusif).
- **Test / out-of-sample** (tidak pernah dipakai memilih): 2024-01-01 s/d data terakhir.
- Sinyal dihitung saat candle close, eksekusi di open candle berikutnya.
- Ranking = Sharpe di periode train. Dengan satu koin risiko kebetulan lebih besar, jadi perhatikan tabel per keluarga formula dan walk-forward, bukan hanya peringkat #1.

## Timeframe 1h

Buy & hold — train: Sharpe 1.06, CAGR +63%, MaxDD +77% · test: Sharpe 0.58, CAGR +18%, MaxDD +54%

**Per keluarga formula** (median semua kombinasi parameter; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1 | 1.06 | 0.58 | +18% | +54% | – |
| `EMA_CROSS+HTF_EMA_CROSS` | 3 | 1.36 | 0.49 | +10% | +35% | 33% |
| `EMA_CROSS+STOCH_DIP` | 9 | 0.81 | 0.09 | -2% | +47% | 0% |
| `EMA_CROSS` | 3 | 0.88 | 0.02 | -4% | +58% | 0% |
| `STRUCT+STOCH_DIP` | 9 | 0.11 | -0.64 | -17% | +50% | 0% |
| `STRUCT` | 3 | 0.26 | -0.70 | -24% | +62% | 0% |
| `STRUCT+CLOSE>EMA` | 9 | -0.27 | -1.23 | -32% | +72% | 0% |
| `CLOSE>EMA` | 4 | -0.39 | -1.94 | -48% | +88% | 0% |
| `EMA_CROSS+STOCH_SWING` | 18 | -0.89 | -2.03 | -39% | +77% | 0% |
| `STOCH_SWING` | 4 | -1.48 | -2.48 | -59% | +93% | 0% |
| `SCORE>=` | 9 | -4.00 | -6.25 | -67% | +96% | 0% |
| `EMA_CROSS+STOCH_K>D` | 3 | -5.25 | -7.71 | -83% | +99% | 0% |
| `STOCH_K>D` | 1 | -6.76 | -9.82 | -96% | +100% | 0% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | 1.37 | +61% | +48% | **0.72** | **+17%** | **+25%** | +38% | 17.1 | +39% |
| 2 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/100)` | 1.36 | +58% | +45% | **0.49** | **+10%** | **+35%** | +37% | 25.1 | +32% |
| 3 | `EMA_CROSS+STOCH_DIP(ema=50/100, os=30)` | 1.00 | +40% | +70% | **0.09** | **-2%** | **+55%** | +47% | 36.9 | +28% |
| 4 | `EMA_CROSS(ema=50/100)` | 0.98 | +41% | +75% | **0.02** | **-4%** | **+61%** | +52% | 40.4 | +29% |
| 5 | `EMA_CROSS+STOCH_DIP(ema=50/100, os=20)` | 0.97 | +39% | +70% | **0.15** | **-0%** | **+56%** | +46% | 36.2 | +29% |
| 6 | `EMA_CROSS+HTF_EMA_CROSS(ema=20/50)` | 0.96 | +35% | +43% | **0.04** | **-2%** | **+39%** | +36% | 52.6 | +32% |
| 7 | `EMA_CROSS+STOCH_DIP(ema=50/100, os=50)` | 0.93 | +37% | +73% | **-0.04** | **-6%** | **+61%** | +48% | 37.6 | +28% |
| 8 | `EMA_CROSS(ema=50/200)` | 0.88 | +35% | +67% | **0.29** | **+4%** | **+47%** | +52% | 28.2 | +30% |
| 9 | `EMA_CROSS+STOCH_DIP(ema=50/200, os=50)` | 0.84 | +32% | +75% | **0.42** | **+9%** | **+35%** | +50% | 26.1 | +29% |
| 10 | `EMA_CROSS(ema=20/50)` | 0.84 | +32% | +69% | **-0.22** | **-11%** | **+58%** | +52% | 82.9 | +27% |
| 11 | `EMA_CROSS+STOCH_DIP(ema=50/200, os=30)` | 0.81 | +30% | +76% | **0.49** | **+11%** | **+32%** | +49% | 25.8 | +31% |
| 12 | `EMA_CROSS+STOCH_DIP(ema=50/200, os=20)` | 0.77 | +27% | +76% | **0.52** | **+12%** | **+31%** | +49% | 25.8 | +31% |

<details><summary>Parameter default (EMA 50/200, Stoch RSI 14/14/3/3 level 20/80, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.06 | +63% | +77% | 0.58 | +18% | +54% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 0.88 | +35% | +67% | 0.29 | +4% | +47% | 28.2 |
| `CLOSE>EMA(ema=200)` | 0.37 | +7% | +78% | -0.87 | -28% | +74% | 164.0 |
| `STOCH_K>D` | -6.76 | -96% | +100% | -9.82 | -96% | +100% | 1087.7 |
| `STOCH_SWING(os=20, ob=80)` | -1.20 | -50% | +98% | -2.33 | -57% | +91% | 247.2 |
| `STRUCT(swing=5)` | 0.26 | +1% | +77% | -0.70 | -24% | +62% | 107.6 |
| `EMA_CROSS+STOCH_K>D(ema=50/200)` | -5.28 | -83% | +100% | -7.57 | -83% | +99% | 580.8 |
| `EMA_CROSS+STOCH_DIP(ema=50/200, os=20)` | 0.77 | +27% | +76% | 0.52 | +12% | +31% | 25.8 |
| `EMA_CROSS+STOCH_SWING(ema=50/200, os=20, ob=80)` | -0.83 | -29% | +89% | -1.67 | -34% | +72% | 137.9 |
| `STRUCT+STOCH_DIP(swing=5, os=20)` | 0.16 | -1% | +71% | -0.42 | -12% | +41% | 84.3 |
| `SCORE>=(k=3, ema=50/200, swing=5)` | -1.42 | -47% | +97% | -3.15 | -58% | +92% | 324.9 |
| `SCORE>=(k=4, ema=50/200, swing=5)` | -4.23 | -69% | +100% | -6.58 | -70% | +97% | 382.7 |
| `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | 1.37 | +61% | +48% | 0.72 | +17% | +25% | 17.1 |

</details>

**Walk-forward 1h** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Return | Buy & hold |
|---|---|---|---|
| 2022 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/100)` | -28% | -64% |
| 2023 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/100)` | +51% | +156% |
| 2024 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | +57% | +121% |
| 2025 | `STRUCT+STOCH_DIP(swing=10, os=20)` | -21% | -6% |
| 2026 | `BUY_HOLD` | -23% | -23% |

Total walk-forward 2022–2026: BTC +3% (B&H +46%)

## Timeframe 4h

Buy & hold — train: Sharpe 1.07, CAGR +63%, MaxDD +77% · test: Sharpe 0.58, CAGR +17%, MaxDD +53%

**Per keluarga formula** (median semua kombinasi parameter; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `STRUCT+STOCH_DIP` | 9 | 0.98 | 0.88 | +20% | +24% | 78% |
| `STRUCT` | 3 | 0.97 | 0.80 | +23% | +40% | 100% |
| `EMA_CROSS` | 3 | 1.34 | 0.76 | +21% | +31% | 100% |
| `EMA_CROSS+HTF_EMA_CROSS` | 3 | 1.36 | 0.72 | +17% | +31% | 100% |
| `STRUCT+CLOSE>EMA` | 9 | 1.17 | 0.70 | +17% | +32% | 67% |
| `EMA_CROSS+STOCH_DIP` | 9 | 1.23 | 0.65 | +17% | +33% | 56% |
| `BUY_HOLD` | 1 | 1.07 | 0.58 | +17% | +53% | – |
| `CLOSE>EMA` | 4 | 1.00 | 0.03 | -3% | +54% | 0% |
| `EMA_CROSS+STOCH_SWING` | 18 | 0.56 | -0.23 | -8% | +44% | 0% |
| `SCORE>=` | 9 | 0.43 | -0.68 | -12% | +48% | 0% |
| `STOCH_SWING` | 4 | 0.51 | -0.68 | -24% | +63% | 0% |
| `EMA_CROSS+STOCH_K>D` | 3 | -0.11 | -1.45 | -29% | +72% | 0% |
| `STOCH_K>D` | 1 | -0.53 | -2.15 | -53% | +91% | 0% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `EMA_CROSS(ema=50/200)` | 1.54 | +85% | +59% | **0.91** | **+27%** | **+31%** | +54% | 6.3 | +39% |
| 2 | `STRUCT+CLOSE>EMA(swing=5, ema=200)` | 1.50 | +71% | +39% | **1.02** | **+27%** | **+26%** | +39% | 30.6 | +27% |
| 3 | `EMA_CROSS+STOCH_DIP(ema=50/200, os=50)` | 1.50 | +81% | +58% | **0.78** | **+21%** | **+30%** | +52% | 6.3 | +39% |
| 4 | `CLOSE>EMA(ema=200)` | 1.46 | +78% | +43% | **0.34** | **+6%** | **+44%** | +53% | 39.3 | +18% |
| 5 | `STRUCT+STOCH_DIP(swing=5, os=30)` | 1.45 | +63% | +62% | **0.60** | **+13%** | **+22%** | +37% | 18.8 | +35% |
| 6 | `EMA_CROSS+STOCH_DIP(ema=50/200, os=30)` | 1.37 | +70% | +59% | **0.71** | **+19%** | **+30%** | +51% | 6.3 | +39% |
| 7 | `EMA_CROSS+STOCH_DIP(ema=50/200, os=20)` | 1.37 | +69% | +58% | **0.65** | **+17%** | **+30%** | +50% | 6.3 | +39% |
| 8 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | 1.36 | +62% | +47% | **0.97** | **+27%** | **+31%** | +44% | 4.5 | +46% |
| 9 | `EMA_CROSS+HTF_EMA_CROSS(ema=20/50)` | 1.36 | +59% | +34% | **0.72** | **+16%** | **+31%** | +35% | 11.5 | +36% |
| 10 | `EMA_CROSS(ema=50/100)` | 1.34 | +68% | +51% | **0.76** | **+21%** | **+30%** | +53% | 9.1 | +38% |
| 11 | `STRUCT+STOCH_DIP(swing=5, os=20)` | 1.34 | +56% | +61% | **0.63** | **+14%** | **+20%** | +36% | 18.5 | +36% |
| 12 | `STRUCT+STOCH_DIP(swing=5, os=50)` | 1.33 | +58% | +66% | **0.94** | **+25%** | **+23%** | +41% | 20.2 | +41% |

<details><summary>Parameter default (EMA 50/200, Stoch RSI 14/14/3/3 level 20/80, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.07 | +63% | +77% | 0.58 | +17% | +53% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 1.54 | +85% | +59% | 0.91 | +27% | +31% | 6.3 |
| `CLOSE>EMA(ema=200)` | 1.46 | +78% | +43% | 0.34 | +6% | +44% | 39.3 |
| `STOCH_K>D` | -0.53 | -29% | +91% | -2.15 | -53% | +91% | 270.9 |
| `STOCH_SWING(os=20, ob=80)` | 0.52 | +14% | +70% | -0.65 | -23% | +62% | 60.6 |
| `STRUCT(swing=5)` | 1.23 | +59% | +72% | 0.80 | +23% | +40% | 24.4 |
| `EMA_CROSS+STOCH_K>D(ema=50/200)` | 0.19 | +1% | +67% | -1.43 | -29% | +71% | 149.0 |
| `EMA_CROSS+STOCH_DIP(ema=50/200, os=20)` | 1.37 | +69% | +58% | 0.65 | +17% | +30% | 6.3 |
| `EMA_CROSS+STOCH_SWING(ema=50/200, os=20, ob=80)` | 0.71 | +21% | +53% | -0.22 | -8% | +35% | 33.4 |
| `STRUCT+STOCH_DIP(swing=5, os=20)` | 1.34 | +56% | +61% | 0.63 | +14% | +20% | 18.5 |
| `SCORE>=(k=3, ema=50/200, swing=5)` | 1.14 | +46% | +52% | 0.19 | +2% | +44% | 76.3 |
| `SCORE>=(k=4, ema=50/200, swing=5)` | 0.47 | +9% | +49% | -0.72 | -12% | +48% | 96.5 |
| `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | 1.36 | +62% | +47% | 0.97 | +27% | +31% | 4.5 |

</details>

**Walk-forward 4h** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Return | Buy & hold |
|---|---|---|---|
| 2022 | `EMA_CROSS(ema=50/200)` | -52% | -64% |
| 2023 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | +55% | +156% |
| 2024 | `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | +80% | +121% |
| 2025 | `STRUCT+CLOSE>EMA(swing=5, ema=200)` | -2% | -6% |
| 2026 | `STRUCT+CLOSE>EMA(swing=10, ema=200)` | +0% | -24% |

Total walk-forward 2022–2026: BTC +31% (B&H +44%)

## Timeframe 1d

Buy & hold — train: Sharpe 1.06, CAGR +63%, MaxDD +77% · test: Sharpe 0.59, CAGR +18%, MaxDD +53%

**Per keluarga formula** (median semua kombinasi parameter; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `EMA_CROSS+STOCH_DIP` | 9 | 0.79 | 0.73 | +19% | +34% | 67% |
| `STRUCT+CLOSE>EMA` | 9 | 1.36 | 0.66 | +17% | +33% | 78% |
| `CLOSE>EMA` | 4 | 1.17 | 0.64 | +18% | +34% | 75% |
| `STRUCT` | 3 | 1.05 | 0.59 | +15% | +39% | 67% |
| `BUY_HOLD` | 1 | 1.06 | 0.59 | +18% | +53% | – |
| `EMA_CROSS` | 3 | 0.89 | 0.59 | +15% | +37% | 33% |
| `EMA_CROSS+HTF_EMA_CROSS` | 3 | 0.61 | 0.58 | +15% | +37% | 33% |
| `STRUCT+STOCH_DIP` | 9 | 1.05 | 0.57 | +13% | +33% | 44% |
| `SCORE>=` | 9 | 0.36 | 0.48 | +9% | +24% | 22% |
| `EMA_CROSS+STOCH_K>D` | 3 | 0.38 | 0.29 | +4% | +25% | 0% |
| `EMA_CROSS+STOCH_SWING` | 18 | 0.43 | 0.17 | +1% | +34% | 0% |
| `STOCH_K>D` | 1 | 0.30 | 0.17 | -0% | +48% | 0% |
| `STOCH_SWING` | 4 | 0.74 | 0.09 | -3% | +53% | 0% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `STRUCT+CLOSE>EMA(swing=10, ema=50)` | 1.54 | +82% | +34% | **0.58** | **+14%** | **+28%** | +44% | 8.4 | +33% |
| 2 | `STRUCT+CLOSE>EMA(swing=5, ema=100)` | 1.52 | +76% | +36% | **0.61** | **+15%** | **+34%** | +43% | 7.3 | +33% |
| 3 | `STRUCT+CLOSE>EMA(swing=5, ema=50)` | 1.45 | +73% | +46% | **0.60** | **+15%** | **+35%** | +45% | 9.8 | +32% |
| 4 | `STRUCT+CLOSE>EMA(swing=10, ema=100)` | 1.38 | +69% | +40% | **0.58** | **+14%** | **+28%** | +47% | 5.6 | +38% |
| 5 | `CLOSE>EMA(ema=100)` | 1.38 | +74% | +39% | **0.65** | **+18%** | **+32%** | +60% | 8.0 | +30% |
| 6 | `STRUCT+CLOSE>EMA(swing=5, ema=200)` | 1.36 | +62% | +39% | **0.66** | **+17%** | **+33%** | +41% | 5.6 | +38% |
| 7 | `EMA_CROSS(ema=20/50)` | 1.35 | +73% | +52% | **0.59** | **+15%** | **+41%** | +57% | 3.5 | +40% |
| 8 | `STRUCT+CLOSE>EMA(swing=10, ema=200)` | 1.33 | +63% | +45% | **0.70** | **+18%** | **+26%** | +45% | 2.4 | +71% |
| 9 | `STRUCT+CLOSE>EMA(swing=3, ema=100)` | 1.33 | +63% | +46% | **0.83** | **+23%** | **+33%** | +44% | 7.3 | +43% |
| 10 | `STRUCT+CLOSE>EMA(swing=3, ema=50)` | 1.29 | +62% | +48% | **0.79** | **+22%** | **+36%** | +46% | 10.4 | +37% |
| 11 | `STRUCT(swing=5)` | 1.26 | +64% | +51% | **0.66** | **+18%** | **+38%** | +56% | 4.9 | +50% |
| 12 | `CLOSE>EMA(ema=50)` | 1.25 | +63% | +57% | **0.74** | **+21%** | **+31%** | +54% | 12.5 | +28% |

<details><summary>Parameter default (EMA 50/200, Stoch RSI 14/14/3/3 level 20/80, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.06 | +63% | +77% | 0.59 | +18% | +53% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 0.77 | +31% | +71% | 0.77 | +26% | +35% | 0.3 |
| `CLOSE>EMA(ema=200)` | 1.07 | +50% | +56% | 0.63 | +18% | +36% | 6.6 |
| `STOCH_K>D` | 0.30 | +4% | +78% | 0.17 | -0% | +48% | 42.8 |
| `STOCH_SWING(os=20, ob=80)` | 0.76 | +28% | +54% | -0.03 | -8% | +57% | 11.1 |
| `STRUCT(swing=5)` | 1.26 | +64% | +51% | 0.66 | +18% | +38% | 4.9 |
| `EMA_CROSS+STOCH_K>D(ema=50/200)` | 0.30 | +5% | +58% | 0.54 | +13% | +23% | 31.0 |
| `EMA_CROSS+STOCH_DIP(ema=50/200, os=20)` | 0.63 | +21% | +74% | 0.78 | +26% | +34% | 0.3 |
| `EMA_CROSS+STOCH_SWING(ema=50/200, os=20, ob=80)` | 0.42 | +9% | +63% | 0.19 | +1% | +36% | 8.4 |
| `STRUCT+STOCH_DIP(swing=5, os=20)` | 1.13 | +46% | +47% | 0.72 | +18% | +32% | 3.8 |
| `SCORE>=(k=3, ema=50/200, swing=5)` | 1.21 | +52% | +40% | 0.56 | +13% | +31% | 14.6 |
| `SCORE>=(k=4, ema=50/200, swing=5)` | 0.22 | +2% | +57% | 0.41 | +7% | +24% | 19.2 |
| `EMA_CROSS+HTF_EMA_CROSS(ema=50/200)` | 0.21 | +2% | +49% | 0.77 | +26% | +35% | 0.3 |

</details>

**Walk-forward 1d** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Return | Buy & hold |
|---|---|---|---|
| 2022 | `STRUCT+CLOSE>EMA(swing=10, ema=50)` | -20% | -64% |
| 2023 | `STRUCT+CLOSE>EMA(swing=10, ema=50)` | +61% | +156% |
| 2024 | `STOCH_SWING(os=20, ob=70)` | +41% | +121% |
| 2025 | `EMA_CROSS+STOCH_SWING(ema=50/200, os=30, ob=70)` | -0% | -6% |
| 2026 | `STOCH_SWING(os=30, ob=70)` | -34% | -22% |

Total walk-forward 2022–2026: BTC +19% (B&H +48%)

