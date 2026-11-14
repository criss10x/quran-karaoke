"""Market structure: swing pivots, HH/HL/LH/LL labels, BOS and CHoCH.

* A swing high at bar ``i`` is a high strictly above the ``left`` bars before it
  and not exceeded by the ``right`` bars after it (lows mirrored). It is only
  *known* at bar ``i + right`` — breaks are never tested before that, so there is
  no look-ahead.
* Each swing is labelled against the previous swing of the same kind:
  highs HH / LH / EQH, lows HL / LL / EQL.
* A close beyond the most recent confirmed, still-unbroken swing is a break of
  structure. If it goes against the prevailing structural bias it is a CHoCH
  (change of character); otherwise a BOS (break of structure).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional, Sequence


@dataclass
class Swing:
    index: int
    price: float
    kind: str                     # "high" | "low"
    label: Optional[str] = None   # HH/LH/EQH or HL/LL/EQL; None for the first of its kind


@dataclass
class Break:
    index: int        # bar whose close broke the level
    direction: str    # "bull" | "bear"
    kind: str         # "BOS" | "CHoCH"
    level: float
    swing_index: int  # bar of the swing that was broken


def find_swings(high: Sequence[float], low: Sequence[float], left: int = 5, right: int = 5) -> list[Swing]:
    n = len(high)
    swings: list[Swing] = []
    for i in range(left, n - right):
        h = high[i]
        if h > max(high[i - left:i]) and h >= max(high[i + 1:i + right + 1]):
            swings.append(Swing(i, h, "high"))
        lo = low[i]
        if lo < min(low[i - left:i]) and lo <= min(low[i + 1:i + right + 1]):
            swings.append(Swing(i, lo, "low"))
    _label(swings)
    return swings


def _label(swings: list[Swing]) -> None:
    prev: dict[str, Optional[Swing]] = {"high": None, "low": None}
    for s in swings:
        p = prev[s.kind]
        if p is not None:
            if s.kind == "high":
                s.label = "HH" if s.price > p.price else "LH" if s.price < p.price else "EQH"
            else:
                s.label = "HL" if s.price > p.price else "LL" if s.price < p.price else "EQL"
        prev[s.kind] = s


def swing_trend(swings: Sequence[Swing]) -> str:
    """``bullish`` (HH + HL), ``bearish`` (LH + LL) or ``range`` from the latest labels."""
    last_high = next((s.label for s in reversed(swings) if s.kind == "high" and s.label), None)
    last_low = next((s.label for s in reversed(swings) if s.kind == "low" and s.label), None)
    if last_high == "HH" and last_low == "HL":
        return "bullish"
    if last_high == "LH" and last_low == "LL":
        return "bearish"
    return "range"


def find_breaks(swings: Sequence[Swing], close: Sequence[float], right: int) -> list[Break]:
    ordered = sorted(swings, key=lambda s: (s.index, s.kind))
    breaks: list[Break] = []
    bias = 0  # +1 bullish, -1 bearish, 0 unknown
    active: dict[str, Optional[Swing]] = {"high": None, "low": None}
    p = 0
    for j in range(len(close)):
        # Swings confirmed at the close of bar index+right can be broken from the next bar on.
        while p < len(ordered) and ordered[p].index + right < j:
            active[ordered[p].kind] = ordered[p]
            p += 1
        c = close[j]
        hi = active["high"]
        if hi is not None and c > hi.price:
            breaks.append(Break(j, "bull", "CHoCH" if bias == -1 else "BOS", hi.price, hi.index))
            bias, active["high"] = 1, None
        lo = active["low"]
        if lo is not None and c < lo.price:
            breaks.append(Break(j, "bear", "CHoCH" if bias == 1 else "BOS", lo.price, lo.index))
            bias, active["low"] = -1, None
    return breaks


def analyze_structure(high: Sequence[float], low: Sequence[float], close: Sequence[float],
                      left: int = 5, right: int = 5, level_lookback: int = 300) -> dict:
    """Summary dict of the market structure on one timeframe."""
    n = len(close)
    swings = find_swings(high, low, left, right)
    breaks = find_breaks(swings, close, right)
    last_close = close[-1] if n else None

    bias = "bullish" if breaks and breaks[-1].direction == "bull" else \
           "bearish" if breaks else "unknown"

    recent = [s for s in swings if s.index >= n - level_lookback]
    resistance = min((s.price for s in recent if s.kind == "high" and s.price > last_close), default=None)
    support = max((s.price for s in recent if s.kind == "low" and s.price < last_close), default=None)

    def pack_break(b: Optional[Break]) -> Optional[dict]:
        if b is None:
            return None
        d = asdict(b)
        d["bars_ago"] = n - 1 - b.index
        return d

    last_bos = next((b for b in reversed(breaks) if b.kind == "BOS"), None)
    last_choch = next((b for b in reversed(breaks) if b.kind == "CHoCH"), None)

    return {
        "bias": bias,                       # from the latest BOS/CHoCH direction
        "swing_trend": swing_trend(swings),  # from the latest HH/HL/LH/LL labels
        "last_break": pack_break(breaks[-1] if breaks else None),
        "last_bos": pack_break(last_bos),
        "last_choch": pack_break(last_choch),
        "recent_swings": [dict(asdict(s), bars_ago=n - 1 - s.index) for s in swings[-6:]],
        "support": support,
        "resistance": resistance,
    }
