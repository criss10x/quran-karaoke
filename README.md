# Crypto MTF Analysis — EMA 50/200 · Supertrend · Market Structure

Analisa teknikal crypto **multi-timeframe** dari data candle live **Binance spot** (API publik,
tanpa API key). Pure Python standard library — tidak perlu `pip install`.

Per timeframe dihitung:

| Komponen | Detail |
|---|---|
| **EMA 50 / 200** | posisi harga vs EMA, golden/death cross + berapa bar lalu, slope EMA 50 |
| **Supertrend (10, 3)** | arah, level garis (trailing stop), jarak %, kapan terakhir flip |
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
python3 -m cta BTC --ema-fast 21 --ema-slow 55 --st-period 10 --st-mult 2 --swing 3
```

Contoh potongan output:

```
## BTCUSDT
**Harga terakhir:** 66,943.72 · **Confluence MTF:** Bearish (-42%)
> Timeframe besar belum punya arah jelas; momentum jangka pendek turun. ...

| TF | Close | EMA50 | EMA200 | Cross | Supertrend | Struktur | BOS/CHoCH terakhir | ... | Skor | Bias |
| 4h | 68,314.00 | 73,677.87 (-7.28%) | 77,810.39 (-12.20%) | Death (122b) | ▼ down @ 72,034.05 (50b) | Bearish / Bearish | BOS ↓ @ 72,727.27 (8b) | ... | -5 | Strong Bearish |
| 1w | 74,851.44 | 78,432.03 (-4.57%) | 69,562.63 (+7.60%) | Golden | ▲ up @ 66,811.57 (9b) | Bullish / Range | CHoCH ↑ @ 82,850.00 (6b) | ... | +3 | Bullish |
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

**Supertrend** — sama dengan `ta.supertrend(3, 10)`: ATR Wilder (RMA), band dari hl2, band
hanya boleh menyempit selama tren berlaku. Di sini `up` = bullish (garis di bawah harga).

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
EMA 200, arah Supertrend, bias struktur. Label: ≥ +4 Strong Bullish, ≥ +2 Bullish, −1..+1 Neutral,
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
python3 tests/test_cta.py      # offline, data sintetis, tanpa pytest
```

> Bukan nasihat keuangan. Indikator bersifat lagging; selalu gunakan manajemen risiko.
