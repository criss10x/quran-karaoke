# Formula hasil backtest

Ringkasan dari `docs/backtest.md` (laporan lengkap, dibuat ulang dengan `python3 -m cta.research`).
Data Binance spot 2018-01 → 2026-11, 6 koin (BTC, ETH, BNB, SOL, XRP, ADA), 3 timeframe
(1h, 4h, 1d), 200 kombinasi formula, total 3.600 backtest. Biaya 0,15% per sisi, long/flat
(spot, tanpa leverage dan tanpa short), sinyal dihitung saat candle close lalu dieksekusi di
open candle berikutnya.

## Cara memilih (anti-overfitting)

1. **Train 2019–2023** dipakai untuk meranking formula, **test 2024 → Nov 2026** tidak pernah
   dipakai untuk memilih.
2. Ranking memakai **median antar 6 koin**: formula harus jalan di mayoritas koin.
3. Dilihat juga per **keluarga formula** (median semua kombinasi parameter). Kalau hanya satu
   kombinasi parameter yang bagus, itu kebetulan, bukan edge.
4. Walk-forward: tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, lalu jalankan di tahun itu.

## Hasil utama

**1h: jangan dipakai untuk formula ini.** Semua keluarga formula kalah dari buy & hold di periode
test setelah biaya (median Sharpe test negatif untuk hampir semua keluarga). Terlalu banyak whipsaw.

**1d: tidak ada edge yang jelas.** Median Sharpe test per keluarga formula 0,19–0,46, buy & hold 0,43. Manfaatnya hanya
drawdown lebih kecil (±48% vs 70%).

**4h: timeframe terbaik.** Formula yang menang di train ternyata bertahan di test:

| Formula 4h (median 6 koin, 2019 → Nov 2026) | Sharpe | CAGR | Max DD | Waktu di market | Trade/thn | Win rate | Profit factor |
|---|---|---|---|---|---|---|---|
| Buy & hold | 0,87 | +42% | 83% | 100% | – | – | – |
| **A · EMA 50 > EMA 200** | **1,15** | **+63%** | 69% | 51% | 5,5 | 34% | 5,8 |
| **B · EMA 50 > EMA 200 + Supertrend(10,3) up** | 1,04 | +43% | **60%** | 31% | 14,7 | 40% | 2,2 |
| C · Semua 5 komponen bullish (skor +5) | 0,91 | +40% | 62% | 26% | 22,4 | 30% | 2,0 |

Hanya periode test (2024 → Nov 2026), median Sharpe: buy & hold 0,42 · **A 0,74** · B 0,60 · C 0,65.
Formula A mengalahkan buy & hold di test pada 5 dari 6 koin (kecuali SOL).

Median return per tahun (4h):

| Tahun | Buy & hold | A | B | C |
|---|---|---|---|---|
| 2019 | −2% | +39% | +80% | +58% |
| 2020 | +237% | +198% | +116% | +106% |
| 2021 | +510% | +556% | +288% | +173% |
| 2022 (bear) | −66% | −50% | −28% | −27% |
| 2023 | +116% | +75% | −8% | −8% |
| 2024 | +104% | +76% | +43% | +31% |
| 2025 | −11% | +14% | +14% | +9% |
| 2026 (s/d Nov) | −38% | −3% | −8% | −8% |

Sensitivitas biaya (Sharpe test): pada 0,10% per sisi A 0,75 / B 0,65 / C 0,73; pada 0,25% per sisi
A 0,71 / B 0,47 / C 0,45. Formula A paling tahan biaya karena jarang trading.

## Formula yang direkomendasikan

**Formula A (utama), timeframe 4h, parameter default (tidak di-tuning):**

- **Masuk / hold** saat candle 4h close dengan **EMA 50 di atas EMA 200** (golden cross).
- **Keluar** saat candle 4h close dengan **EMA 50 di bawah EMA 200** (death cross).
- Watak trend-following: win rate rendah (±34%) tapi profit factor tinggi. Profitnya datang dari
  sedikit tren besar, jadi **jangan skip sinyal** setelah beberapa kali rugi kecil.

**Formula B (konservatif):** syarat A **plus Supertrend(10,3) 4h arah up**. Keluar lebih cepat
saat Supertrend flip down. Return lebih kecil, drawdown lebih kecil (BTC 34% vs 59%), tapi
trading ±3× lebih sering sehingga lebih sensitif terhadap biaya.

Market structure (BOS/CHoCH) dan skor konfluensi tetap berguna sebagai **konteks dan level**
(support/resistance, invalidasi), tapi sebagai aturan entry/exit mekanis tidak lebih baik dari A.

Status kedua formula untuk tiap koin tampil otomatis di `python3 -m cta ...` (baris
*Formula teruji backtest (4h)*, perlu `4h` di daftar `--tf`).

## Batasan, baca sebelum dipakai

- **Survivorship bias:** keenam koin dipilih karena masih besar hari ini. Koin yang mati tidak
  diuji, jadi hasil untuk altcoin acak kemungkinan lebih buruk.
- Drawdown tetap besar (median 60–69%). Ini mengurangi kerugian dibanding buy & hold, bukan
  menghilangkannya. Pakai ukuran posisi yang wajar.
- Walk-forward (memilih ulang formula tiap tahun) hasilnya campuran: unggul di tahun bear,
  tertinggal di tahun bull kuat. Konsisten memakai satu formula sederhana lebih baik daripada
  terus ganti-ganti formula terbaik.
- Tanpa short, tanpa leverage, tanpa funding. Hasil masa lalu tidak menjamin hasil masa depan.
  Bukan nasihat keuangan.
