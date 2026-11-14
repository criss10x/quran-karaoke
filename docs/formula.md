# Formula hasil backtest — BTC

Ringkasan dari `docs/backtest.md` (laporan lengkap, dibuat ulang dengan
`python3 -m cta.research --symbols BTC --tf 1h 4h 1d`).

Data Binance spot **BTCUSDT** 2018-01 → 2026-11, timeframe 1h, 4h, 1d, 200 kombinasi formula
(600 backtest). Biaya 0,15% per sisi (fee + slippage), long/flat (spot, tanpa leverage dan tanpa
short). Sinyal dihitung saat candle close lalu dieksekusi di open candle berikutnya.

## Cara memilih (anti-overfitting)

1. **Train 2019–2023** dipakai untuk meranking formula. **Test 2024 → Nov 2026** tidak pernah
   dipakai untuk memilih.
2. Karena hanya satu koin, risiko "kebetulan bagus" lebih besar. Pengamannya:
   - dilihat per **keluarga formula** (median semua kombinasi parameter): logika yang benar
     harus bagus di hampir semua variasi parameter, bukan di satu titik saja;
   - **parameter default** (EMA 50/200, Supertrend 10/3, swing 5) diutamakan, bukan hasil tuning;
   - **walk-forward**: tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu jalankan di tahun itu.

## Hasil per timeframe

**1h: jangan dipakai.** Tidak ada satu pun dari 200 kombinasi yang mengalahkan buy & hold di
periode test (0%). Walk-forward 2022–2026: −68% vs buy & hold +44%.

**1d: tidak meyakinkan.** Beberapa keluarga sedikit di atas buy & hold di test (Sharpe
0,62–0,66 vs 0,59), tapi formula EMA 50/200 di 1d hanya trading ±0,8 kali/tahun dan kalah di
periode penuh (Sharpe 0,76 vs 0,92). Walk-forward bagus (+119% vs +48%), tapi formula yang
terpilih berganti-ganti tiap tahun, jadi tidak ada satu aturan yang stabil.

**4h: paling bagus dan konsisten.**

| BTC 4h, 2019 → Nov 2026 | Sharpe | CAGR | Total | Max DD | Di market | Trade/thn | Win rate | Profit factor | **Sharpe test** | **DD test** |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & hold | 0,92 | +44% | +1.701% | 77% | 100% | – | – | – | 0,58 | 53% |
| **A · EMA 50 > EMA 200** | **1,34** | **+61%** | **+4.162%** | 59% | 54% | 5,1 | 42% | 5,7 | **0,91** | 31% |
| **B · Semua komponen bullish** | 1,32 | +43% | +1.569% | 40% | 28% | 22,9 | 34% | 2,4 | 0,81 | **18%** |
| EMA 50/200 + Supertrend(10,3) | 1,31 | +46% | +1.891% | 34% | 33% | 15,1 | 44% | 2,6 | 0,74 | 26% |
| Market structure saja (swing 5) | 1,09 | +45% | +1.764% | 72% | 55% | 24,5 | 38% | 1,9 | 0,80 | 40% |

Return per tahun (BTC 4h):

| Tahun | Buy & hold | A · EMA 50/200 | B · Semua bullish |
|---|---|---|---|
| 2019 | +94% | +134% | +141% |
| 2020 | +302% | +279% | +120% |
| 2021 | +60% | +126% | +48% |
| 2022 (bear) | −64% | −52% | −21% |
| 2023 | +156% | +125% | +73% |
| 2024 | +121% | +80% | +51% |
| 2025 | −6% | +8% | +9% |
| 2026 (s/d Nov) | −24% | +1% | −6% |

Ketahanan:

- **Parameter:** ketiga varian EMA cross (20/50, 50/100, 50/200) mengalahkan buy & hold di
  test (Sharpe 0,65 / 0,76 / 0,91), dan 50/200 yang terbaik. Formula B mengalahkan buy & hold di
  test pada **12 dari 12** variasi Supertrend (Sharpe test 0,62–1,02, DD test 17–28%).
- **Biaya:** pada 0,25% per sisi, Sharpe test A masih 0,87. B turun ke 0,59 (≈ buy & hold),
  karena trading ±23 kali/tahun. Pada 0,10% per sisi: A 0,93, B 0,92.
- **Walk-forward 4h** 2022–2026: +59% vs buy & hold +44%.

## Formula yang direkomendasikan untuk BTC

**Formula A (utama): BTC 4h, EMA 50/200 cross**

- **Beli / tahan** saat candle 4h close dengan **EMA 50 di atas EMA 200**.
- **Jual / keluar** saat candle 4h close dengan **EMA 50 di bawah EMA 200**.
- Rata-rata 5 trade per tahun. Win rate 42%, tapi rata-rata untung jauh lebih besar dari rugi
  (profit factor 5,7). Profit datang dari sedikit tren besar, jadi **jangan skip sinyal**
  setelah beberapa kali rugi kecil.
- Kelemahan: tertinggal di awal bull market (2020, 2023, 2024) karena cross datang terlambat.

**Formula B (konservatif): BTC 4h, semua komponen bullish**

- **Beli / tahan** hanya saat **semua** syarat ini terpenuhi di candle 4h: close > EMA 50,
  close > EMA 200, EMA 50 > EMA 200, Supertrend(10,3) arah up, dan BOS/CHoCH terakhir bullish
  (skor analisa = +5).
- **Keluar** begitu salah satu syarat gugur.
- Drawdown paling kecil (2022 hanya −21%, DD test 18%), tapi hanya 28% waktu di market sehingga
  tertinggal jauh di tahun bull. Butuh biaya trading rendah (pakai limit order / diskon fee).

Status kedua formula tampil otomatis di `python3 -m cta BTC ...` pada baris
*Formula teruji backtest (4h)* (pastikan `4h` ada di `--tf`).

## Batasan, baca sebelum dipakai

- Hanya **satu aset** dan satu periode sejarah. Hasil masa lalu tidak menjamin hasil masa depan.
- Drawdown tetap besar untuk formula A (59%). Formula ini mengurangi kerugian dibanding
  buy & hold, bukan menghilangkannya. Pakai ukuran posisi yang wajar.
- Tanpa short, tanpa leverage, tanpa funding, tanpa pajak. Slippage diasumsikan 0,05%.
- Bukan nasihat keuangan.
