"""EMA, RSI and Stoch RSI — pure Python, matching TradingView's Pine definitions.

Every function returns a list the same length as its input, with ``None`` during
the warm-up period.
"""

from __future__ import annotations

from typing import Optional, Sequence

Series = list[Optional[float]]


def _seeded_ma(values: Sequence[float], length: int, alpha: float) -> Series:
    """Exponential MA seeded with the SMA of the first ``length`` values (Pine style)."""
    if length < 1:
        raise ValueError("length must be >= 1")
    n = len(values)
    out: Series = [None] * n
    if n < length:
        return out
    prev = sum(values[:length]) / length
    out[length - 1] = prev
    for i in range(length, n):
        prev = alpha * values[i] + (1.0 - alpha) * prev
        out[i] = prev
    return out


def ema(values: Sequence[float], length: int) -> Series:
    """``ta.ema``: alpha = 2 / (length + 1)."""
    return _seeded_ma(values, length, 2.0 / (length + 1))


def rma(values: Sequence[float], length: int) -> Series:
    """``ta.rma`` (Wilder's smoothing): alpha = 1 / length."""
    return _seeded_ma(values, length, 1.0 / length)


def sma(values: Sequence[Optional[float]], length: int) -> Series:
    """``ta.sma``; ``None`` while any value in the window is ``None``."""
    n = len(values)
    out: Series = [None] * n
    for i in range(length - 1, n):
        window = values[i - length + 1:i + 1]
        if all(v is not None for v in window):
            out[i] = sum(window) / length
    return out


def rsi(close: Sequence[float], length: int = 14) -> Series:
    """``ta.rsi``: Wilder-smoothed average gain / loss."""
    n = len(close)
    out: Series = [None] * n
    if n <= length:
        return out
    gains = [max(close[i] - close[i - 1], 0.0) for i in range(1, n)]
    losses = [max(close[i - 1] - close[i], 0.0) for i in range(1, n)]
    for j, (g, l) in enumerate(zip(rma(gains, length), rma(losses, length))):
        if g is None:
            continue
        out[j + 1] = 100.0 if l == 0 else 0.0 if g == 0 else 100.0 - 100.0 / (1.0 + g / l)
    return out


def stoch_rsi(close: Sequence[float], rsi_len: int = 14, stoch_len: int = 14,
              k_smooth: int = 3, d_smooth: int = 3) -> tuple[Series, Series, Series]:
    """TradingView "Stoch RSI": returns ``(rsi, k, d)``, K and D in 0..100.

    stoch = 100 * (rsi - lowest(rsi, stoch_len)) / (highest - lowest); K = SMA(stoch, k_smooth);
    D = SMA(K, d_smooth). A flat RSI window (highest == lowest) gives ``None``, as ``na`` in Pine.
    """
    r = rsi(close, rsi_len)
    n = len(r)
    raw: Series = [None] * n
    for i in range(stoch_len - 1, n):
        window = r[i - stoch_len + 1:i + 1]
        if any(v is None for v in window):
            continue
        hi, lo = max(window), min(window)
        raw[i] = None if hi == lo else 100.0 * (r[i] - lo) / (hi - lo)
    k = sma(raw, k_smooth)
    return r, k, sma(k, d_smooth)


def last_cross(a: Sequence[Optional[float]], b: Sequence[Optional[float]]) -> Optional[dict]:
    """Most recent bar where ``a`` crossed ``b``: direction, bars ago and ``a`` at the cross."""
    n = len(a)
    for i in range(n - 1, 0, -1):
        if None in (a[i], b[i], a[i - 1], b[i - 1]):
            return None
        if a[i - 1] <= b[i - 1] and a[i] > b[i]:
            return {"direction": "bull", "bars_ago": n - 1 - i, "value": a[i]}
        if a[i - 1] >= b[i - 1] and a[i] < b[i]:
            return {"direction": "bear", "bars_ago": n - 1 - i, "value": a[i]}
    return None


def bars_since_change(values: Sequence[Optional[object]]) -> Optional[int]:
    """How many bars ago the current state began (0 = it flipped on the last bar).

    ``None`` if the state has not changed within the available (warmed-up) history.
    """
    if not values or values[-1] is None:
        return None
    last = values[-1]
    for k in range(len(values) - 2, -1, -1):
        if values[k] is None:
            return None
        if values[k] != last:
            return len(values) - 2 - k
    return None
