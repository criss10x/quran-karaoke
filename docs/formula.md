# Formula hasil backtest — BTC

Ringkasan dari `docs/backtest.md` (laporan lengkap, dibuat ulang dengan
`python3 -m cta.research --symbols BTC --tf 1h 4h 1d`).

Komponen yang diuji: **EMA 50/200**, **Stoch RSI 14** (RSI 14, stoch 14, %K 3, %D 3) dan
**market structure** (BOS/CHoCH). Supertrend sudah dihapus dari proyek.

Data Binance spot **BTCUSDT** 2018-01 → 2026-11, timeframe 1h, 4h, 1d, 76 formula (228 backtest).
Biaya 0,15% per sisi (fee + slippage), long/flat (spot, tanpa leverage dan tanpa short). Sinyal
dihitung saat candle close lalu dieksekusi di open candle berikutnya.

## Cara memilih (anti-overfitting)

1. **Train 2019–2023** dipakai untuk meranking formula. **Test 2024 → Nov 2026** tidak pernah
   dipakai untuk memilih.
2. Karena hanya satu koin, pengamannya: lihat per **keluarga formula** (median semua variasi
   parameter), utamakan **parameter default**, dan cek **walk-forward**.

## Temuan utama

**Stoch RSI tidak memberi keunggulan sebagai aturan beli/jual mekanis untuk BTC.**

| Pemakaian Stoch RSI (4h) | Sharpe test | Catatan |
|---|---|---|
| Long saat %K > %D | −2,15 | ±270 trade/tahun, habis dimakan biaya |
| Swing: beli cross naik dari oversold, jual cross turun dari overbought | −0,68 (median 4 variasi) | 0 dari 4 variasi mengalahkan buy & hold |
| Formula A + tunggu Stoch RSI dip (entry lebih telat) | 0,65 | lebih buruk dari A murni (0,91) |
| Skor 5 komponen, semua bullish (Stoch RSI menggantikan Supertrend) | −0,72 | ±96 trade/tahun; formula B lama tidak bisa dipakai lagi |

Stoch RSI tetap ditampilkan di laporan sebagai **konteks** (overbought/oversold, cross terakhir),
tapi bukan pemicu entry.

**Per timeframe:**

- **1h: jangan dipakai.** Hanya 1 dari 76 formula yang mengalahkan buy & hold di test
  (EMA 50/200 dengan filter golden cross 4h), dan variasi parameternya gagal. Walk-forward
  2022–2026: +3% vs buy & hold +46%.
- **1d: tidak meyakinkan.** Keluarga terbaik di test (EMA cross + Stoch RSI dip) justru lemah
  di train. Walk-forward +19% vs +48%.
- **4h: tetap yang terbaik.** Dua formula teratas di train juga bertahan di test.

| BTC 4h, 2019 → Nov 2026 | Sharpe | CAGR | Total | Max DD | Di market | Trade/thn | Win rate | Profit factor | **Sharpe test** | **DD test** |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & hold | 0,92 | +44% | +1.701% | 77% | 100% | – | – | – | 0,58 | 53% |
| **A · EMA 50 > EMA 200** | 1,34 | **+61%** | **+4.162%** | 59% | 54% | 5,1 | 42% | 5,7 | 0,91 | 31% |
| **B · Struktur bullish + close > EMA 200** | **1,35** | +53% | +2.802% | **39%** | 40% | 27,4 | 29% | 2,4 | **1,02** | **26%** |
| EMA 50/200 4h + golden cross 1d | 1,23 | +49% | +2.157% | 47% | 41% | 3,4 | 44% | 7,7 | 0,97 | 31% |
| A + Stoch RSI dip (oversold 20) | 1,15 | +48% | +2.069% | 58% | 51% | 5,1 | 40% | 4,8 | 0,65 | 30% |
| Struktur + Stoch RSI dip (oversold 20) | 1,13 | +39% | +1.237% | 61% | 36% | 18,3 | 35% | 2,3 | 0,63 | 20% |

Return per tahun (BTC 4h):

| Tahun | Buy & hold | A · EMA 50/200 | B · Struktur + EMA 200 |
|---|---|---|---|
| 2019 | +94% | +134% | +93% |
| 2020 | +302% | +279% | +193% |
| 2021 | +60% | +126% | +53% |
| 2022 (bear) | −64% | −52% | −18% |
| 2023 | +156% | +125% | +107% |
| 2024 | +121% | +80% | +124% |
| 2025 | −6% | +8% | −2% |
| 2026 (s/d Nov) | −24% | +1% | −10% |
| **Total 2024 → Nov 2026 (test)** | **+58%** | **+96%** | **+98%** |

Ketahanan:

- **Parameter A:** EMA 20/50, 50/100, 50/200 semuanya mengalahkan buy & hold di test
  (0,65 / 0,76 / 0,91).
- **Parameter B:** dengan EMA 200, ketiga variasi swing (3 / 5 / 10) mengalahkan buy & hold di
  test (0,85 / 1,02 / 1,21). **Dengan EMA 50 gagal** (0,06 / −0,02 / 0,56), jadi EMA 200 adalah
  bagian penting dari formula ini, jangan diganti.
- **Biaya:** di 0,25% per sisi, A 0,87 dan B 0,79 (keduanya masih di atas buy & hold 0,58).
  Di 0,10%: A 0,93, B 1,13. B trading ±27 kali/tahun, jadi lebih peka biaya.

## Formula yang direkomendasikan untuk BTC

**Formula A (utama, paling simpel): BTC 4h, EMA 50/200 cross**

- **Beli / tahan** saat candle 4h close dengan **EMA 50 di atas EMA 200**.
- **Jual / keluar** saat candle 4h close dengan **EMA 50 di bawah EMA 200**.
- ±5 trade/tahun, win rate 42%, profit factor 5,7. Profit datang dari sedikit tren besar, jadi
  jangan skip sinyal setelah beberapa kali rugi kecil.
- Kelemahan: telat masuk di awal bull market, dan drawdown masih 59%.

**Formula B (drawdown lebih kecil): BTC 4h, market structure + EMA 200**

- **Beli / tahan** saat candle 4h close **di atas EMA 200** DAN break struktur terakhir
  (BOS/CHoCH, swing 5) **bullish**.
- **Keluar** begitu salah satu gugur: close di bawah EMA 200, atau muncul BOS/CHoCH bearish.
- Drawdown jauh lebih kecil (2022 hanya −18%, max DD 39%), tapi lebih sering trading
  (±27 kali/tahun, win rate 29%): banyak rugi kecil, sedikit untung besar.

Status kedua formula tampil otomatis di `python3 -m cta BTC ...` pada baris
*Formula teruji backtest (4h)* (pastikan `4h` ada di `--tf`).

## Batasan, baca sebelum dipakai

- Hanya **satu aset** dan satu periode sejarah. Hasil masa lalu tidak menjamin hasil masa depan.
- Walk-forward 4h (memilih ulang formula terbaik tiap tahun) hanya +31% vs buy & hold +44% di
  2022–2026. Konsisten memakai satu formula lebih baik daripada terus ganti formula.
- Tanpa short, tanpa leverage, tanpa funding, tanpa pajak. Slippage diasumsikan 0,05%.
- Bukan nasihat keuangan.
