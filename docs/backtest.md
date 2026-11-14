# Backtest — EMA · Supertrend · Market Structure

Dibuat 2026-11-14 04:51 UTC · data Binance spot · koin: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT, ADAUSDT · biaya 0.15% per sisi (fee + slippage) · long/flat (spot, tanpa leverage).

- **Train** (untuk memilih formula): 2019-01-01 s/d 2024-01-01 (eksklusif).
- **Test / out-of-sample** (tidak pernah dipakai memilih): 2024-01-01 s/d data terakhir.
- Sinyal dihitung saat candle close, eksekusi di open candle berikutnya.
- Ranking = **median** Sharpe antar koin di periode train (formula harus bagus di mayoritas koin, bukan satu koin saja). Angka di tabel adalah median antar koin.

## Timeframe 1h

Buy & hold — train: Sharpe 1.08, CAGR +74%, MaxDD +83% · test: Sharpe 0.43, CAGR +5%, MaxDD +71%

**Per keluarga formula** (median semua kombinasi parameter × semua koin; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold di koin yang sama):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1 | 1.08 | 0.43 | +5% | +71% | – |
| `EMA_CROSS` | 3 | 1.12 | 0.16 | -4% | +68% | 0% |
| `ST+HTF_ST` | 12 | 0.71 | -0.02 | -9% | +55% | 17% |
| `ST+EMA_CROSS` | 36 | 0.68 | -0.14 | -11% | +62% | 18% |
| `STRUCT` | 3 | 0.40 | -0.19 | -19% | +69% | 11% |
| `ST` | 12 | 0.58 | -0.33 | -21% | +71% | 6% |
| `ST+HTF_CLOSE>EMA50` | 12 | 0.62 | -0.40 | -19% | +67% | 10% |
| `ST+STRUCT` | 36 | 0.40 | -0.47 | -22% | +70% | 13% |
| `SCORE>=` | 36 | 0.40 | -0.49 | -21% | +60% | 10% |
| `STRUCT+CLOSE>EMA` | 9 | 0.14 | -0.87 | -34% | +78% | 2% |
| `ST+CLOSE>EMA` | 36 | 0.19 | -0.92 | -35% | +80% | 3% |
| `CLOSE>EMA` | 4 | -0.06 | -1.44 | -53% | +91% | 0% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `EMA_CROSS(ema=50/200)` | 1.33 | +89% | +63% | **0.23** | **-2%** | **+60%** | +48% | 27.2 | +29% |
| 2 | `ST+EMA_CROSS(st=7/4, ema=50/200)` | 1.20 | +68% | +53% | **0.21** | **-1%** | **+59%** | +31% | 44.1 | +29% |
| 3 | `ST+EMA_CROSS(st=10/4, ema=50/200)` | 1.20 | +67% | +54% | **0.13** | **-4%** | **+61%** | +32% | 44.6 | +30% |
| 4 | `ST+EMA_CROSS(st=14/4, ema=50/200)` | 1.16 | +63% | +54% | **0.04** | **-3%** | **+64%** | +31% | 44.9 | +32% |
| 5 | `ST+HTF_ST(st=7/4, htf_st=10/3)` | 1.11 | +54% | +64% | **0.22** | **+0%** | **+52%** | +32% | 44.2 | +31% |
| 6 | `ST+EMA_CROSS(st=7/4, ema=20/50)` | 1.11 | +52% | +59% | **0.02** | **-7%** | **+64%** | +42% | 73.7 | +29% |
| 7 | `ST+HTF_CLOSE>EMA50(st=7/4)` | 1.11 | +50% | +64% | **-0.34** | **-19%** | **+66%** | +36% | 80.4 | +23% |
| 8 | `ST+EMA_CROSS(st=20/4, ema=50/200)` | 1.10 | +58% | +52% | **0.09** | **-6%** | **+62%** | +31% | 44.6 | +33% |
| 9 | `ST+HTF_ST(st=14/4, htf_st=10/3)` | 1.09 | +55% | +65% | **0.07** | **-6%** | **+57%** | +32% | 45.1 | +33% |
| 10 | `ST+HTF_ST(st=10/4, htf_st=10/3)` | 1.08 | +56% | +68% | **0.15** | **-2%** | **+54%** | +33% | 44.7 | +32% |
| 11 | `ST+EMA_CROSS(st=10/4, ema=20/50)` | 1.07 | +53% | +64% | **-0.08** | **-9%** | **+62%** | +42% | 73.8 | +30% |
| 12 | `ST+EMA_CROSS(st=7/4, ema=50/100)` | 1.06 | +55% | +60% | **0.10** | **-4%** | **+62%** | +35% | 51.7 | +30% |

<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.08 | +74% | +83% | 0.43 | +5% | +71% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 1.33 | +89% | +63% | 0.23 | -2% | +60% | 27.2 |
| `CLOSE>EMA(ema=200)` | 0.51 | +15% | +81% | -0.83 | -37% | +84% | 176.7 |
| `ST(st=10/3)` | 0.60 | +14% | +85% | -0.49 | -25% | +72% | 105.3 |
| `STRUCT(swing=5)` | 0.40 | +6% | +83% | -0.21 | -20% | +65% | 100.6 |
| `ST+CLOSE>EMA(st=10/3, ema=200)` | 0.30 | +1% | +83% | -0.80 | -25% | +74% | 135.3 |
| `ST+EMA_CROSS(st=10/3, ema=50/200)` | 0.82 | +37% | +61% | -0.08 | -9% | +60% | 62.2 |
| `ST+STRUCT(st=10/3, swing=5)` | 0.40 | +4% | +83% | -0.52 | -26% | +70% | 102.2 |
| `SCORE>=(k=3, st=10/3, ema=50/200, swing=5)` | 0.18 | -2% | +81% | -0.81 | -33% | +77% | 172.7 |
| `SCORE>=(k=4, st=10/3, ema=50/200, swing=5)` | 0.50 | +11% | +67% | -0.43 | -17% | +58% | 97.3 |
| `ST+HTF_ST(st=10/3, htf_st=10/3)` | 0.69 | +24% | +73% | -0.17 | -11% | +54% | 62.7 |

</details>

**Walk-forward 1h** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Median return | Median buy & hold |
|---|---|---|---|
| 2022 | `ST(st=7/4)` | -50% | -66% |
| 2023 | `EMA_CROSS(ema=50/200)` | +63% | +116% |
| 2024 | `EMA_CROSS(ema=50/200)` | +57% | +104% |
| 2025 | `EMA_CROSS(ema=50/200)` | -33% | -11% |
| 2026 | `BUY_HOLD` | -38% | -38% |

Total walk-forward per koin: ADA -65% (B&H -87%), BNB -22% (B&H +20%), BTC -28% (B&H +44%), ETH -49% (B&H -49%), SOL +129% (B&H -56%), XRP -45% (B&H +19%)

## Timeframe 4h

Buy & hold — train: Sharpe 1.09, CAGR +74%, MaxDD +83% · test: Sharpe 0.42, CAGR +5%, MaxDD +70%

**Per keluarga formula** (median semua kombinasi parameter × semua koin; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold di koin yang sama):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `SCORE>=` | 36 | 1.27 | 0.62 | +14% | +43% | 67% |
| `EMA_CROSS` | 3 | 1.37 | 0.45 | +10% | +53% | 56% |
| `ST+EMA_CROSS` | 36 | 1.24 | 0.45 | +9% | +46% | 57% |
| `BUY_HOLD` | 1 | 1.09 | 0.42 | +5% | +70% | – |
| `STRUCT` | 3 | 0.90 | 0.35 | +6% | +55% | 56% |
| `ST+HTF_CLOSE>EMA50` | 12 | 1.23 | 0.33 | +6% | +44% | 60% |
| `STRUCT+CLOSE>EMA` | 9 | 1.06 | 0.31 | +4% | +57% | 48% |
| `ST+STRUCT` | 36 | 0.98 | 0.31 | +5% | +50% | 46% |
| `ST+HTF_ST` | 12 | 1.35 | 0.28 | +4% | +45% | 49% |
| `ST` | 12 | 1.18 | 0.26 | +2% | +62% | 39% |
| `ST+CLOSE>EMA` | 36 | 1.21 | 0.25 | +2% | +53% | 38% |
| `CLOSE>EMA` | 4 | 1.10 | -0.07 | -13% | +69% | 17% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `EMA_CROSS(ema=50/200)` | 1.50 | +105% | +67% | **0.74** | **+22%** | **+50%** | +48% | 6.1 | +31% |
| 2 | `ST+EMA_CROSS(st=10/4, ema=50/200)` | 1.45 | +77% | +51% | **0.62** | **+16%** | **+50%** | +31% | 10.4 | +35% |
| 3 | `CLOSE>EMA(ema=200)` | 1.45 | +90% | +67% | **0.38** | **+7%** | **+53%** | +48% | 39.3 | +16% |
| 4 | `ST+EMA_CROSS(st=14/4, ema=50/200)` | 1.45 | +77% | +49% | **0.57** | **+14%** | **+48%** | +30% | 9.9 | +34% |
| 5 | `ST+EMA_CROSS(st=20/4, ema=50/200)` | 1.44 | +86% | +50% | **0.58** | **+15%** | **+46%** | +30% | 9.9 | +36% |
| 6 | `ST+EMA_CROSS(st=7/4, ema=50/200)` | 1.44 | +82% | +51% | **0.63** | **+17%** | **+47%** | +32% | 10.4 | +36% |
| 7 | `ST+EMA_CROSS(st=20/4, ema=50/100)` | 1.44 | +84% | +53% | **0.58** | **+16%** | **+46%** | +33% | 11.7 | +36% |
| 8 | `ST+CLOSE>EMA(st=20/4, ema=200)` | 1.44 | +82% | +55% | **0.48** | **+13%** | **+50%** | +35% | 27.0 | +22% |
| 9 | `ST+EMA_CROSS(st=14/3, ema=50/100)` | 1.43 | +73% | +57% | **0.34** | **+6%** | **+43%** | +29% | 15.5 | +36% |
| 10 | `ST+HTF_ST(st=20/4, htf_st=10/3)` | 1.43 | +85% | +48% | **0.46** | **+10%** | **+48%** | +27% | 9.8 | +36% |
| 11 | `ST+EMA_CROSS(st=14/4, ema=50/100)` | 1.43 | +75% | +52% | **0.53** | **+14%** | **+49%** | +33% | 11.3 | +35% |
| 12 | `ST+HTF_ST(st=7/3, htf_st=10/3)` | 1.41 | +71% | +50% | **0.31** | **+5%** | **+42%** | +26% | 13.4 | +35% |

<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.09 | +74% | +83% | 0.42 | +5% | +70% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 1.50 | +105% | +67% | 0.74 | +22% | +50% | 6.1 |
| `CLOSE>EMA(ema=200)` | 1.45 | +90% | +67% | 0.38 | +7% | +53% | 39.3 |
| `ST(st=10/3)` | 1.15 | +61% | +73% | 0.15 | -4% | +63% | 25.8 |
| `STRUCT(swing=5)` | 1.02 | +49% | +79% | 0.36 | +6% | +59% | 25.1 |
| `ST+CLOSE>EMA(st=10/3, ema=200)` | 1.31 | +66% | +63% | 0.47 | +10% | +40% | 28.4 |
| `ST+EMA_CROSS(st=10/3, ema=50/200)` | 1.27 | +63% | +59% | 0.60 | +13% | +41% | 14.5 |
| `ST+STRUCT(st=10/3, swing=5)` | 1.00 | +42% | +71% | 0.23 | -0% | +56% | 25.6 |
| `SCORE>=(k=3, st=10/3, ema=50/200, swing=5)` | 1.29 | +68% | +56% | 0.51 | +12% | +47% | 43.0 |
| `SCORE>=(k=4, st=10/3, ema=50/200, swing=5)` | 1.14 | +50% | +61% | 0.65 | +14% | +41% | 22.6 |
| `ST+HTF_ST(st=10/3, htf_st=10/3)` | 1.37 | +63% | +48% | 0.36 | +6% | +41% | 13.6 |

</details>

**Walk-forward 4h** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Median return | Median buy & hold |
|---|---|---|---|
| 2022 | `EMA_CROSS(ema=50/200)` | -50% | -66% |
| 2023 | `ST+HTF_ST(st=7/4, htf_st=10/3)` | +46% | +116% |
| 2024 | `ST+HTF_ST(st=14/4, htf_st=10/3)` | +25% | +104% |
| 2025 | `ST+CLOSE>EMA(st=14/4, ema=200)` | -6% | -11% |
| 2026 | `ST+CLOSE>EMA(st=10/4, ema=200)` | -8% | -38% |

Total walk-forward per koin: ADA -12% (B&H -87%), BNB -40% (B&H +20%), BTC -18% (B&H +44%), ETH -7% (B&H -49%), SOL +658% (B&H -56%), XRP -51% (B&H +19%)

## Timeframe 1d

Buy & hold — train: Sharpe 1.05, CAGR +67%, MaxDD +81% · test: Sharpe 0.43, CAGR +6%, MaxDD +70%

**Per keluarga formula** (median semua kombinasi parameter × semua koin; *% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan buy & hold di koin yang sama):

| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |
|---|---|---|---|---|---|---|
| `ST+STRUCT` | 36 | 1.31 | 0.46 | +11% | +48% | 48% |
| `STRUCT` | 3 | 1.09 | 0.45 | +10% | +53% | 56% |
| `BUY_HOLD` | 1 | 1.05 | 0.43 | +6% | +70% | – |
| `STRUCT+CLOSE>EMA` | 9 | 1.16 | 0.43 | +9% | +46% | 61% |
| `ST+CLOSE>EMA` | 36 | 1.36 | 0.42 | +9% | +48% | 53% |
| `CLOSE>EMA` | 4 | 1.21 | 0.41 | +8% | +50% | 50% |
| `ST` | 12 | 1.29 | 0.39 | +8% | +56% | 44% |
| `EMA_CROSS` | 3 | 1.00 | 0.38 | +7% | +51% | 28% |
| `SCORE>=` | 36 | 1.16 | 0.35 | +6% | +46% | 39% |
| `ST+HTF_CLOSE>EMA50` | 12 | 1.14 | 0.27 | +2% | +51% | 24% |
| `ST+EMA_CROSS` | 36 | 1.24 | 0.27 | +3% | +52% | 28% |
| `ST+HTF_ST` | 12 | 1.06 | 0.19 | +0% | +48% | 21% |

**Top 12 formula berdasarkan train** (lalu lihat apakah bertahan di test):

| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | **Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `ST+STRUCT(st=7/3, swing=10)` | 1.47 | +94% | +57% | **0.57** | **+15%** | **+47%** | +41% | 3.5 | +45% |
| 2 | `ST+CLOSE>EMA(st=7/3, ema=100)` | 1.44 | +98% | +48% | **0.55** | **+13%** | **+45%** | +35% | 5.9 | +31% |
| 3 | `ST+EMA_CROSS(st=14/4, ema=20/50)` | 1.43 | +97% | +65% | **0.61** | **+18%** | **+50%** | +41% | 2.8 | +54% |
| 4 | `ST+CLOSE>EMA(st=10/3, ema=50)` | 1.43 | +110% | +54% | **0.51** | **+13%** | **+44%** | +39% | 8.0 | +32% |
| 5 | `ST+STRUCT(st=20/3, swing=10)` | 1.43 | +84% | +62% | **0.59** | **+15%** | **+50%** | +37% | 3.8 | +49% |
| 6 | `ST+STRUCT(st=7/3, swing=5)` | 1.42 | +102% | +55% | **0.45** | **+10%** | **+54%** | +42% | 4.5 | +42% |
| 7 | `ST+CLOSE>EMA(st=14/4, ema=50)` | 1.42 | +96% | +59% | **0.66** | **+19%** | **+49%** | +37% | 7.7 | +28% |
| 8 | `ST+EMA_CROSS(st=7/3, ema=20/50)` | 1.42 | +99% | +50% | **0.47** | **+10%** | **+49%** | +38% | 3.7 | +38% |
| 9 | `ST+STRUCT(st=10/3, swing=5)` | 1.41 | +104% | +58% | **0.40** | **+9%** | **+53%** | +41% | 4.7 | +42% |
| 10 | `ST+CLOSE>EMA(st=20/3, ema=100)` | 1.41 | +84% | +50% | **0.29** | **+4%** | **+51%** | +31% | 6.6 | +32% |
| 11 | `ST+STRUCT(st=7/2, swing=5)` | 1.41 | +102% | +57% | **0.44** | **+10%** | **+48%** | +39% | 6.3 | +40% |
| 12 | `ST+CLOSE>EMA(st=7/3, ema=50)` | 1.41 | +102% | +55% | **0.53** | **+13%** | **+46%** | +40% | 8.4 | +29% |

<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>

| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |
|---|---|---|---|---|---|---|---|
| `BUY_HOLD` | 1.05 | +67% | +81% | 0.43 | +6% | +70% | 0.0 |
| `EMA_CROSS(ema=50/200)` | 0.93 | +53% | +78% | 0.35 | +3% | +55% | 1.0 |
| `CLOSE>EMA(ema=200)` | 1.06 | +60% | +71% | 0.52 | +14% | +47% | 6.4 |
| `ST(st=10/3)` | 1.32 | +97% | +55% | 0.34 | +5% | +54% | 4.7 |
| `STRUCT(swing=5)` | 1.32 | +90% | +67% | 0.57 | +15% | +61% | 4.7 |
| `ST+CLOSE>EMA(st=10/3, ema=200)` | 1.35 | +91% | +46% | 0.38 | +7% | +46% | 4.9 |
| `ST+EMA_CROSS(st=10/3, ema=50/200)` | 1.22 | +74% | +46% | 0.22 | +1% | +50% | 3.1 |
| `ST+STRUCT(st=10/3, swing=5)` | 1.41 | +104% | +58% | 0.40 | +9% | +53% | 4.7 |
| `SCORE>=(k=3, st=10/3, ema=50/200, swing=5)` | 1.27 | +74% | +54% | 0.36 | +6% | +44% | 7.0 |
| `SCORE>=(k=4, st=10/3, ema=50/200, swing=5)` | 1.16 | +66% | +47% | 0.38 | +7% | +44% | 4.7 |
| `ST+HTF_ST(st=10/3, htf_st=10/3)` | 1.06 | +50% | +59% | 0.21 | +1% | +47% | 2.8 |

</details>

**Walk-forward 1d** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu dipakai tahun itu):

| Tahun | Formula terpilih | Median return | Median buy & hold |
|---|---|---|---|
| 2022 | `ST(st=7/2)` | -31% | -66% |
| 2023 | `ST+CLOSE>EMA(st=7/3, ema=200)` | +38% | +116% |
| 2024 | `ST+EMA_CROSS(st=10/2, ema=50/200)` | +73% | +104% |
| 2025 | `STRUCT+CLOSE>EMA(swing=3, ema=200)` | -15% | -11% |
| 2026 | `BUY_HOLD` | -36% | -36% |

Total walk-forward per koin: ADA -68% (B&H -87%), BNB -24% (B&H +23%), BTC +20% (B&H +48%), ETH -46% (B&H -48%), SOL +21% (B&H -54%), XRP -59% (B&H +22%)

