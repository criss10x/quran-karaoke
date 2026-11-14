"""Per-timeframe analysis and multi-timeframe confluence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence

from . import indicators as ind
from .data import INTERVAL_MINUTES, Candle, DataError, fetch_klines, fetch_last_price
from .structure import analyze_structure

DEFAULT_TIMEFRAMES = ("15m", "1h", "4h", "1d", "1w")

# Higher timeframes carry more weight in the confluence score.
TF_WEIGHT = {
    "1m": 0.5, "3m": 0.5, "5m": 0.75, "15m": 1.0, "30m": 1.25,
    "1h": 1.5, "2h": 1.75, "4h": 2.0, "6h": 2.0, "8h": 2.25, "12h": 2.25,
    "1d": 2.5, "3d": 2.75, "1w": 3.0, "1M": 3.0,
}

MAX_SCORE = 5  # number of +/-1 components in a timeframe score


@dataclass
class Config:
    ema_fast: int = 50
    ema_slow: int = 200
    st_period: int = 10
    st_mult: float = 3.0
    swing_left: int = 5
    swing_right: int = 5
    limit: int = 1000
    include_open: bool = False


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def _pct(a: float, b: Optional[float]) -> Optional[float]:
    return None if b in (None, 0) else (a - b) / b * 100.0


def bias_label(score: float, max_score: float) -> str:
    r = score / max_score if max_score else 0.0
    if r >= 0.7:
        return "Strong Bullish"
    if r >= 0.3:
        return "Bullish"
    if r > -0.3:
        return "Neutral"
    if r > -0.7:
        return "Bearish"
    return "Strong Bearish"


def analyze_candles(candles: Sequence[Candle], cfg: Config = Config()) -> dict:
    """Indicators, structure and a -5..+5 score for one timeframe."""
    if len(candles) < max(cfg.st_period, cfg.swing_left + cfg.swing_right + 1) + 2:
        raise DataError(f"only {len(candles)} candles — not enough history")
    o_t = [c.open_time for c in candles]
    h = [c.high for c in candles]
    lo = [c.low for c in candles]
    cl = [c.close for c in candles]
    close = cl[-1]

    ef, es = ind.ema(cl, cfg.ema_fast), ind.ema(cl, cfg.ema_slow)
    fast, slow = ef[-1], es[-1]
    cross_state = [None if a is None or b is None else (a > b) for a, b in zip(ef, es)]
    slope_n = 5
    fast_slope = _pct(fast, ef[-1 - slope_n]) if fast is not None and len(ef) > slope_n else None

    st_line, st_dir = ind.supertrend(h, lo, cl, cfg.st_period, cfg.st_mult)
    struct = analyze_structure(h, lo, cl, cfg.swing_left, cfg.swing_right)

    components = {
        "close_vs_ema_fast": _sign(close - fast) if fast is not None else 0,
        "close_vs_ema_slow": _sign(close - slow) if slow is not None else 0,
        "ema_fast_vs_slow": _sign(fast - slow) if fast is not None and slow is not None else 0,
        "supertrend": st_dir[-1] or 0,
        "structure": {"bullish": 1, "bearish": -1}.get(struct["bias"], 0),
    }
    score = sum(components.values())

    if fast is None or slow is None:
        ema_cross = "n/a"
    else:
        ema_cross = "golden" if fast > slow else "death"

    return {
        "candle_time": datetime.fromtimestamp(o_t[-1] / 1000, timezone.utc).isoformat(),
        "bars": len(candles),
        "close": close,
        "ema": {
            "fast_len": cfg.ema_fast, "slow_len": cfg.ema_slow,
            "fast": fast, "slow": slow,
            "dist_fast_pct": _pct(close, fast), "dist_slow_pct": _pct(close, slow),
            "cross": ema_cross,  # golden = EMA fast above EMA slow
            "cross_bars_ago": ind.bars_since_change(cross_state),
            "fast_slope_pct": fast_slope,  # % change of EMA fast over the last 5 bars
        },
        "supertrend": {
            "period": cfg.st_period, "mult": cfg.st_mult,
            "direction": {1: "up", -1: "down"}.get(st_dir[-1], "n/a"),
            "line": st_line[-1],
            "dist_pct": _pct(close, st_line[-1]),
            "flip_bars_ago": ind.bars_since_change(st_dir),
        },
        "structure": struct,
        "components": components,
        "score": score,
        "bias": bias_label(score, MAX_SCORE),
    }


def _side(score: Optional[float]) -> int:
    """+1 / -1 / 0 using the same neutral band as ``bias_label``."""
    if score is None:
        return 0
    r = score / MAX_SCORE
    return 1 if r >= 0.3 else -1 if r <= -0.3 else 0


def confluence(per_tf: dict[str, dict]) -> dict:
    """Weighted multi-timeframe score (-100..+100) plus a plain-language read."""
    ok = {tf: r for tf, r in per_tf.items() if "score" in r}
    if not ok:
        return {"score_pct": None, "bias": "n/a", "summary": "Tidak ada data yang bisa dianalisis."}
    tfs = sorted(ok, key=lambda t: INTERVAL_MINUTES[t])
    wsum = sum(TF_WEIGHT[t] for t in tfs)
    pct = sum(TF_WEIGHT[t] * ok[t]["score"] for t in tfs) / (wsum * MAX_SCORE) * 100.0

    k = 2 if len(tfs) >= 4 else 1
    ltf, htf = tfs[:k], tfs[-k:]
    htf_side = _side(sum(ok[t]["score"] for t in htf) / len(htf))
    ltf_side = _side(sum(ok[t]["score"] for t in ltf) / len(ltf))

    if htf_side == 1 and ltf_side == 1:
        read = ("Tren naik selaras di semua lapisan. Cari entry buy saat pullback ke EMA "
                "fast / garis Supertrend / HL terakhir, bukan mengejar harga.")
    elif htf_side == 1 and ltf_side == -1:
        read = ("Koreksi (pullback) di dalam tren naik timeframe besar. Tunggu CHoCH bullish "
                "atau Supertrend flip up di timeframe kecil sebelum buy.")
    elif htf_side == 1:
        read = "Timeframe besar bullish, timeframe kecil netral/konsolidasi — bias buy, tunggu pemicu."
    elif htf_side == -1 and ltf_side == -1:
        read = ("Tren turun selaras di semua lapisan. Rally ke EMA / Supertrend / LH terakhir "
                "berpotensi jadi area sell; hindari menangkap pisau jatuh.")
    elif htf_side == -1 and ltf_side == 1:
        read = ("Relief rally di dalam tren turun timeframe besar. Waspada penolakan di "
                "resistance; tunggu CHoCH bearish di timeframe kecil untuk lanjutan turun.")
    elif htf_side == -1:
        read = "Timeframe besar bearish, timeframe kecil netral — bias sell, tunggu pemicu."
    elif ltf_side != 0:
        arah = "naik" if ltf_side == 1 else "turun"
        read = (f"Timeframe besar belum punya arah jelas; momentum jangka pendek {arah}. "
                "Perlakukan sebagai trading range sampai ada BOS di timeframe besar.")
    else:
        read = "Sideways / sinyal campuran di semua timeframe. Tunggu break struktur yang jelas."

    return {
        "score_pct": round(pct, 1),
        "bias": bias_label(pct, 100.0),
        "htf": htf, "ltf": ltf,
        "aligned_bull": [t for t in tfs if _side(ok[t]["score"]) == 1],
        "aligned_bear": [t for t in tfs if _side(ok[t]["score"]) == -1],
        "summary": read,
    }


def analyze_symbol(symbol: str, timeframes: Sequence[str] = DEFAULT_TIMEFRAMES,
                   cfg: Config = Config()) -> dict:
    def one(tf: str) -> dict:
        try:
            return analyze_candles(fetch_klines(symbol, tf, cfg.limit, cfg.include_open), cfg)
        except (DataError, ValueError) as e:
            return {"error": str(e)}

    with ThreadPoolExecutor(max_workers=6) as pool:
        price_job = pool.submit(fetch_last_price, symbol)
        per_tf = dict(zip(timeframes, pool.map(one, timeframes)))
        last_price = price_job.result()
    return {
        "symbol": symbol,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_price": last_price,
        "config": cfg.__dict__.copy(),
        "timeframes": per_tf,
        "confluence": confluence(per_tf),
    }
