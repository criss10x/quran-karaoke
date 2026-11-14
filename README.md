# Crypto MTF Analysis — EMA 50/200 · Stoch RSI · Market Structure

Analisa teknikal crypto **multi-timeframe** dari data candle live **Binance spot** (API publik,
tanpa API key). Pure Python standard library — tidak perlu `pip install`.

Per timeframe dihitung:

| Komponen | Detail |
|---|---|
| **EMA 50 / 200** | posisi harga vs EMA, golden/death cross + berapa bar lalu, slope EMA 50 |
| **Stoch RSI (14)** | RSI 14, %K/%D (14, 3, 3), zona overbought ≥ 80 / oversold ≤ 20, cross %K/%D terakhir dan zonanya |
| **Market structure** | swing high/low → label HH/HL/LH/LL, **BOS** dan **CHoCH**, support/resistance terdekat |
| **Skor & bias** | skor −5..+5 per TF, lalu **confluence** tertimbang lintas TF + ringkasan bahasa Indonesia |

Default timeframe: `15m 1h 4h 1d 1w`.

## Pakai

```bash
python3 -m cta                                   # BTCUSDT, 15m 1h 4h 1d 1w
python3 -m cta btc eth sol                       # ticker otomatis jadi ...USDT
python3 -m cta ETHBTC --tf 1h 4h 1d              # pair apa pun di Binance spot
python3 -m cta BTC --format json                 # JSON untuk diproses lanjut
python3 -m cta BTC ETH --out report/a.md --json-out report/a.json
python3 -m cta BTC --ema-fast 21 --ema-slow 55 --rsi-len 14 --stoch-len 14 --swing 3
```

Contoh potongan output (BTCUSDT, 14 Nov 2026):

```
## BTCUSDT
**Harga terakhir:** 67,027.20 · **Confluence MTF:** Strong Bearish (-77%)
**Formula teruji backtest (4h):** A · EMA50/200 cross → FLAT sejak 123 bar · B · struktur bullish + close > EMA200 → FLAT sejak 53 bar

| TF | Close | EMA50 | EMA200 | Cross | Stoch RSI K/D | Struktur | BOS/CHoCH terakhir | ... | Skor | Bias |
| 4h | 66,755.66 | 73,406.41 (-9.06%) | 77,700.37 (-14.09%) | Death (123b) | 18.2/22.7 ▼ oversold · cross ↓ 0b | Bearish / Bearish | BOS ↓ @ 72,727.27 (9b) | ... | -5 | Strong Bearish |
| 1d | 68,314.00 | 78,208.69 (-12.65%) | 76,320.79 (-10.49%) | Golden (62b) | 1.9/4.3 ▼ oversold · cross ↓ 6b | Bearish / Bearish | BOS ↓ @ 79,800.00 (15b) | ... | -3 | Bearish |
```

## Hasil backtest BTC: formula yang direkomendasikan

Backtest BTCUSDT 2018 → Nov 2026 (1h/4h/1d, 200 formula, train 2019–2023, test out-of-sample
2024 → sekarang, biaya 0,15% per sisi). Ringkasan: [`docs/formula.md`](docs/formula.md),
laporan lengkap: [`docs/backtest.md`](docs/backtest.md).

| BTC 4h, 2019 → Nov 2026 | Sharpe | CAGR | Max DD | Sharpe test 2024+ | DD test |
|---|---|---|---|---|---|
| Buy & hold | 0,92 | +44% | 77% | 0,58 | 53% |
| **A · EMA 50 > EMA 200** (beli saat golden cross, jual saat death cross) | 1,34 | **+61%** | 59% | 0,91 | 31% |
| **B · Struktur bullish + close > EMA 200** (drawdown lebih kecil) | **1,35** | +53% | **39%** | **1,02** | **26%** |

- **4h** adalah timeframe terbaik untuk BTC. **1h** dan **1d** tidak meyakinkan.
- **Stoch RSI** tidak menambah keunggulan sebagai aturan beli/jual (semua formula berbasis
  Stoch RSI kalah dari buy & hold di test). Di laporan ia dipakai sebagai konteks overbought/oversold.
- Laporan live menampilkan status **LONG/FLAT** formula A dan B di 4h.
- Batasan (satu aset, drawdown masih besar) ada di `docs/formula.md`.

Jalankan ulang riset (download pertama ±3 menit, lalu cache di `data/`):

```bash
python3 -m cta.research --symbols BTC --tf 1h 4h 1d --out docs/backtest.md --json data/backtest.json
```

## Tiga cara menjalankan

1. **CLI** — perintah di atas.
2. **Skill Claude Code** — `.claude/skills/crypto-mtf-analysis/SKILL.md`. Buka repo ini di Claude
   Code lalu tanya biasa ("analisa SOL buat swing") atau ketik `/crypto-mtf-analysis BTC ETH`.
   Claude menjalankan CLI, membaca JSON-nya, lalu menyusun verdict, level kunci, dan skenario.
3. **GitHub Actions** — `.github/workflows/crypto-mtf-analysis.yml`. Jalan otomatis tiap 4 jam
   (atau manual lewat *Actions → Crypto MTF analysis → Run workflow* dengan input simbol/TF).
   Laporan tampil di *job summary* dan disimpan sebagai artifact (`analysis.md` + `analysis.json`).

## Metodologi

**EMA** — definisi TradingView `ta.ema` (α = 2/(n+1), di-seed SMA n bar pertama). Butuh ≥ 200
candle tertutup untuk EMA 200; jika kurang (koin baru di TF besar) nilainya `null` dan komponen skornya 0.

**Stoch RSI** — sama dengan indikator "Stoch RSI" TradingView: RSI 14 (Wilder), stochastic 14
atas nilai RSI, %K = SMA 3, %D = SMA 3. ≥ 80 overbought, ≤ 20 oversold. Komponen skornya +1 bila
%K > %D (momentum naik), −1 bila %K < %D.

**Market structure**
- *Swing high* di bar *i*: high lebih tinggi dari `swing` bar sebelumnya dan tidak dilampaui
  `swing` bar sesudahnya (swing low kebalikannya). Swing baru diketahui di bar *i + swing*, dan
  break tidak pernah dites sebelum itu → **tanpa look-ahead**.
- Label tiap swing dibanding swing sejenis sebelumnya: **HH/LH/EQH**, **HL/LL/EQL**.
  `swing_trend` = bullish bila label terakhir HH + HL, bearish bila LH + LL, selain itu range.
- **Break**: candle *close* melewati swing terakhir yang sudah terkonfirmasi dan belum ditembus.
  Searah bias sebelumnya = **BOS** (lanjutan); berlawanan = **CHoCH** (awal pembalikan).
  `bias` struktur = arah break terakhir.
- Support / resistance = swing low tertinggi di bawah harga / swing high terendah di atas harga
  dalam 300 bar terakhir.

**Skor timeframe** (−5..+5), masing-masing ±1: close vs EMA 50, close vs EMA 200, EMA 50 vs
EMA 200, momentum Stoch RSI (%K vs %D), bias struktur. Label: ≥ +4 Strong Bullish, ≥ +2 Bullish, −1..+1 Neutral,
≤ −2 Bearish, ≤ −4 Strong Bearish.

**Confluence** (−100%..+100%) = rata-rata skor tertimbang (15m 1 · 1h 1.5 · 4h 2 · 1d 2.5 · 1w 3).
Ringkasan membandingkan 2 TF terbesar (HTF) dengan 2 TF terkecil (LTF): selaras naik/turun,
pullback dalam tren naik, relief rally dalam tren turun, atau range.

Semua sinyal memakai **candle yang sudah close** (`--include-open` untuk ikut candle berjalan),
jadi kolom *Close* 1w adalah close minggu lalu; *Harga terakhir* adalah harga live.

## Data & jaringan

Host default `https://data-api.binance.vision` (mirror market-data publik Binance, juga bisa
diakses dari wilayah yang memblokir `api.binance.com`), fallback `https://api.binance.com`.
Ganti dengan `CTA_BINANCE_HOSTS=https://host1,https://host2`. Maks 1000 candle per TF (`--limit`).

## Test

```bash
python3 tests/test_cta.py      # offline, data sintetis, tanpa pytest (indikator, struktur, engine backtest)
```

> Bukan nasihat keuangan. Indikator bersifat lagging; selalu gunakan manajemen risiko.
