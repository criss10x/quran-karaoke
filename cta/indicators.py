"""EMA, ATR and Supertrend — pure Python, matching TradingView's Pine definitions.

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


def true_range(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> list[float]:
    tr = []
    for i in range(len(close)):
        if i == 0:
            tr.append(high[0] - low[0])
        else:
            pc = close[i - 1]
            tr.append(max(high[i] - low[i], abs(high[i] - pc), abs(low[i] - pc)))
    return tr


def atr(high: Sequence[float], low: Sequence[float], close: Sequence[float], length: int = 14) -> Series:
    return rma(true_range(high, low, close), length)


def supertrend(high: Sequence[float], low: Sequence[float], close: Sequence[float],
               period: int = 10, multiplier: float = 3.0) -> tuple[Series, list[Optional[int]]]:
    """``ta.supertrend(multiplier, period)`` on hl2.

    Returns ``(line, direction)`` where direction is ``+1`` (uptrend, line below
    price) or ``-1`` (downtrend, line above price). Note Pine itself uses the
    opposite sign convention; here +1 simply means bullish.
    """
    n = len(close)
    a = atr(high, low, close, period)
    line: Series = [None] * n
    direction: list[Optional[int]] = [None] * n
    upper = lower = None
    for i in range(n):
        if a[i] is None:
            continue
        hl2 = (high[i] + low[i]) / 2.0
        basic_upper = hl2 + multiplier * a[i]
        basic_lower = hl2 - multiplier * a[i]
        if upper is None:  # first bar with ATR
            upper, lower = basic_upper, basic_lower
            d = 1 if close[i] >= hl2 else -1
        else:
            prev_upper, prev_lower, prev_close = upper, lower, close[i - 1]
            lower = basic_lower if (basic_lower > prev_lower or prev_close < prev_lower) else prev_lower
            upper = basic_upper if (basic_upper < prev_upper or prev_close > prev_upper) else prev_upper
            if direction[i - 1] == -1:
                d = 1 if close[i] > prev_upper else -1
            else:
                d = -1 if close[i] < prev_lower else 1
        direction[i] = d
        line[i] = lower if d == 1 else upper
    return line, direction


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
