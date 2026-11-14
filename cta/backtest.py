"""Backtest of rule sets built from EMA, Stoch RSI and market structure.

Execution model (no look-ahead):
* a rule produces a target position from information available at the **close** of bar i;
* the position is entered/exited at the **open** of bar i+1;
* every change of position pays ``cost`` per unit (fee + slippage, default 0.15% per side).

Results are aggregated per calendar year so any window (train, test, walk-forward) can be
evaluated without re-simulating.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional, Sequence

from . import indicators as ind
from .data import INTERVAL_MINUTES, Candle
from .structure import find_breaks, find_swings

DAY_MS = 86_400_000
WEEK_OFFSET_MS = 4 * DAY_MS  # 1970-01-05 was a Monday -> weeks start Monday 00:00 UTC (as Binance)


def year_of(ms: int) -> int:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).year


def resample(candles: Sequence[Candle], minutes: int) -> list[Candle]:
    """Aggregate candles into ``minutes`` buckets (weekly buckets start on Monday)."""
    period = minutes * 60_000
    offset = WEEK_OFFSET_MS if minutes == INTERVAL_MINUTES["1w"] else 0
    out: list[Candle] = []
    cur = None
    for c in candles:
        b = (c.open_time - offset) // period
        if cur is None or b != cur[0]:
            if cur is not None:
                out.append(cur[1])
            start = b * period + offset
            cur = [b, Candle(start, c.open, c.high, c.low, c.close, c.volume, start + period - 1)]
        else:
            p = cur[1]
            cur[1] = Candle(p.open_time, p.open, max(p.high, c.high), min(p.low, c.low), c.close,
                            p.volume + c.volume, p.close_time)
    if cur is not None:
        out.append(cur[1])
    return out


class Features:
    """Lazily computed, cached indicator series for one candle series."""

    def __init__(self, candles: Sequence[Candle]):
        self.candles = list(candles)
        self.o = [c.open for c in candles]
        self.h = [c.high for c in candles]
        self.l = [c.low for c in candles]
        self.c = [c.close for c in candles]
        self.t = [c.open_time for c in candles]
        self.ct = [c.close_time for c in candles]
        self.year = [year_of(x) for x in self.t]
        self._cache: dict = {}

    def _memo(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def ema(self, n: int):
        return self._memo(("ema", n), lambda: ind.ema(self.c, n))

    def stoch(self, rsi_len: int = 14, stoch_len: int = 14, k: int = 3, d: int = 3):
        """``(k, d)`` of Stoch RSI."""
        return self._memo(("stoch", rsi_len, stoch_len, k, d),
                          lambda: ind.stoch_rsi(self.c, rsi_len, stoch_len, k, d)[1:])

    def struct_bias(self, swing: int):
        """+1 / -1 / 0 per bar: direction of the latest BOS/CHoCH known at that bar's close."""
        def build():
            swings = find_swings(self.h, self.l, swing, swing)
            breaks = find_breaks(swings, self.c, swing)
            out = [0] * len(self.c)
            k, cur = 0, 0
            for j in range(len(self.c)):
                while k < len(breaks) and breaks[k].index <= j:
                    cur = 1 if breaks[k].direction == "bull" else -1
                    k += 1
                out[j] = cur
            return out
        return self._memo(("struct", swing), build)

    def score(self, ef: int, es: int, swing: int, stoch: tuple = (14, 14, 3, 3)):
        """Per-bar copy of the live -5..+5 score (see ``analysis.analyze_candles``)."""
        def build():
            f, s, b = self.ema(ef), self.ema(es), self.struct_bias(swing)
            k, d = self.stoch(*stoch)
            out = []
            for i, c in enumerate(self.c):
                v = b[i]
                if k[i] is not None and d[i] is not None:
                    v += (k[i] > d[i]) - (k[i] < d[i])
                if f[i] is not None:
                    v += (c > f[i]) - (c < f[i])
                if s[i] is not None:
                    v += (c > s[i]) - (c < s[i])
                if f[i] is not None and s[i] is not None:
                    v += (f[i] > s[i]) - (f[i] < s[i])
                out.append(v)
            return out
        return self._memo(("score", ef, es, swing, tuple(stoch)), build)


def align_htf(ltf: Features, htf: Features, values: Sequence) -> list:
    """For each LTF bar, the HTF value of the last HTF candle closed at or before that bar's close."""
    out = [None] * len(ltf.c)
    k = -1
    for i, ct in enumerate(ltf.ct):
        while k + 1 < len(htf.ct) and htf.ct[k + 1] <= ct:
            k += 1
        out[i] = values[k] if k >= 0 else None
    return out


# --------------------------------------------------------------------------- rules

@dataclass(frozen=True)
class Rule:
    name: str
    params: tuple  # ((key, value), ...) — hashable, printable
    fn: Callable[["Features", Optional["Features"]], list]

    @property
    def label(self) -> str:
        if not self.params:
            return self.name
        return f"{self.name}(" + ", ".join(f"{k}={v}" for k, v in self.params) + ")"

    @property
    def p(self) -> dict:
        return dict(self.params)


def _gt(a, b) -> bool:
    return a is not None and b is not None and a > b


def _htf_golden(F: Features, H: Features, ef: int, es: int) -> list:
    return F._memo(("htf_golden", id(H), ef, es),
                   lambda: align_htf(F, H, [_gt(a, b) for a, b in zip(H.ema(ef), H.ema(es))]))


def stoch_crosses(F: Features, os_: float, ob: float) -> tuple[list, list]:
    """Per bar: bullish K/D cross starting below ``os_``; bearish K/D cross starting above ``ob``."""
    def build():
        k, d = F.stoch()
        bull, bear = [False] * len(k), [False] * len(k)
        for i in range(1, len(k)):
            if None in (k[i], d[i], k[i - 1], d[i - 1]):
                continue
            bull[i] = k[i - 1] <= d[i - 1] and k[i] > d[i] and k[i - 1] < os_
            bear[i] = k[i - 1] >= d[i - 1] and k[i] < d[i] and k[i - 1] > ob
        return bull, bear
    return F._memo(("stoch_x", os_, ob), build)


def entry_exit(entry: Sequence[bool], exit_: Sequence[bool]) -> list[int]:
    """Stateful position: go long on ``entry``, stay long until ``exit_`` (exit wins ties)."""
    pos, out = 0, []
    for en, ex in zip(entry, exit_):
        if pos and ex:
            pos = 0
        elif not pos and en and not ex:
            pos = 1
        out.append(pos)
    return out


def make_rules(ema_grid=((20, 50), (50, 100), (50, 200)), swing_grid=(3, 5, 10),
               os_grid=(20, 30, 50), ob_grid=(70, 80)) -> list[Rule]:
    """Rule library. Stoch RSI is fixed at 14/14/3/3; only its trigger levels vary."""
    R: list[Rule] = []

    def add(name, params, fn):
        R.append(Rule(name, tuple(params.items()), fn))

    def golden(F, ef, es):
        return [_gt(a, b) for a, b in zip(F.ema(ef), F.ema(es))]

    def kd_up(F):
        k, d = F.stoch()
        return [_gt(a, b) for a, b in zip(k, d)]

    add("BUY_HOLD", {}, lambda F, H: [1] * len(F.c))
    add("STOCH_K>D", {}, lambda F, H: [int(x) for x in kd_up(F)])
    for os_ in (20, 30):
        for ob in ob_grid:
            add("STOCH_SWING", {"os": os_, "ob": ob},
                lambda F, H, os_=os_, ob=ob: entry_exit(*stoch_crosses(F, os_, ob)))
    for ef, es in ema_grid:
        e = f"{ef}/{es}"
        add("EMA_CROSS", {"ema": e}, lambda F, H, ef=ef, es=es: [int(g) for g in golden(F, ef, es)])
        add("EMA_CROSS+STOCH_K>D", {"ema": e},
            lambda F, H, ef=ef, es=es: [int(g and u) for g, u in zip(golden(F, ef, es), kd_up(F))])
        add("EMA_CROSS+HTF_EMA_CROSS", {"ema": e},
            lambda F, H, ef=ef, es=es: [int(g and bool(h)) for g, h in
                                        zip(golden(F, ef, es), _htf_golden(F, H, ef, es))])
        for os_ in os_grid:
            # Wait for a Stoch RSI dip inside the uptrend, hold until the death cross.
            add("EMA_CROSS+STOCH_DIP", {"ema": e, "os": os_},
                lambda F, H, ef=ef, es=es, os_=os_: entry_exit(
                    [g and b for g, b in zip(golden(F, ef, es), stoch_crosses(F, os_, 80)[0])],
                    [not g for g in golden(F, ef, es)]))
            for ob in ob_grid:
                # Same entry, but also take profit on a bearish cross from overbought.
                add("EMA_CROSS+STOCH_SWING", {"ema": e, "os": os_, "ob": ob},
                    lambda F, H, ef=ef, es=es, os_=os_, ob=ob: entry_exit(
                        [g and b for g, b in zip(golden(F, ef, es), stoch_crosses(F, os_, ob)[0])],
                        [(not g) or x for g, x in zip(golden(F, ef, es), stoch_crosses(F, os_, ob)[1])]))
    for n in sorted({e for pair in ema_grid for e in pair}):
        add("CLOSE>EMA", {"ema": n},
            lambda F, H, n=n: [int(_gt(c, e)) for c, e in zip(F.c, F.ema(n))])
    for sw in swing_grid:
        add("STRUCT", {"swing": sw}, lambda F, H, sw=sw: [int(b == 1) for b in F.struct_bias(sw)])
        for _, es in ema_grid:
            add("STRUCT+CLOSE>EMA", {"swing": sw, "ema": es},
                lambda F, H, sw=sw, es=es: [int(b == 1 and _gt(c, e))
                                            for b, c, e in zip(F.struct_bias(sw), F.c, F.ema(es))])
        for os_ in os_grid:
            add("STRUCT+STOCH_DIP", {"swing": sw, "os": os_},
                lambda F, H, sw=sw, os_=os_: entry_exit(
                    [b == 1 and x for b, x in zip(F.struct_bias(sw), stoch_crosses(F, os_, 80)[0])],
                    [b == -1 for b in F.struct_bias(sw)]))
        for k in (3, 4, 5):
            add("SCORE>=", {"k": k, "ema": "50/200", "swing": sw},
                lambda F, H, sw=sw, k=k: [int(s >= k) for s in F.score(50, 200, sw)])
    return R


# --------------------------------------------------------------------------- simulation

@dataclass
class Stats:
    """Mergeable per-window aggregates."""
    n: int = 0
    sum_r: float = 0.0
    sum_r2: float = 0.0
    log_growth: float = 0.0
    in_pos: int = 0
    trades: list = field(default_factory=list)  # closed trade returns (fraction)
    max_dd: float = 0.0  # only meaningful for windows simulated as one block

    def merge(self, other: "Stats") -> "Stats":
        return Stats(self.n + other.n, self.sum_r + other.sum_r, self.sum_r2 + other.sum_r2,
                     self.log_growth + other.log_growth, self.in_pos + other.in_pos,
                     self.trades + other.trades, max(self.max_dd, other.max_dd))


def simulate(F: Features, target: Sequence, start: int, cost: float,
             windows: dict[str, tuple[int, int]]) -> tuple[dict[int, Stats], dict[str, Stats]]:
    """Run ``target`` from bar ``start`` (flat before). Returns per-year and per-window stats.

    ``windows`` maps a name to ``(start_ms, end_ms)``; their max drawdown is computed on the
    equity path inside that window.
    """
    years: dict[int, Stats] = {}
    wins = {k: Stats() for k in windows}
    peaks = {k: 1.0 for k in windows}
    weq = {k: 1.0 for k in windows}
    import bisect
    o, c, t, yr = F.o, F.c, F.t, F.year
    ranges = {k: (bisect.bisect_left(t, a), bisect.bisect_left(t, b)) for k, (a, b) in windows.items()}
    pos = 0
    trade_eq = 1.0
    for i in range(start, len(c)):
        new = target[i - 1] or 0
        gap = o[i] / c[i - 1] - 1.0
        intra = c[i] / o[i] - 1.0
        g = (1.0 + pos * gap)
        if new != pos:
            g *= 1.0 - abs(new - pos) * cost
        g *= 1.0 + new * intra
        # trade bookkeeping
        if pos != 0:
            trade_eq *= (1.0 + pos * gap)
        if new != pos:
            if pos != 0:
                trade_eq *= 1.0 - abs(pos) * cost
                closed = trade_eq - 1.0
            else:
                closed = None
            trade_eq = 1.0
            if new != 0:
                trade_eq *= 1.0 - abs(new) * cost
        else:
            closed = None
        if new != 0:
            trade_eq *= 1.0 + new * intra
        pos = new

        r = g - 1.0
        y = yr[i]
        st = years.get(y)
        if st is None:
            st = years[y] = Stats()
        st.n += 1
        st.sum_r += r
        st.sum_r2 += r * r
        st.log_growth += math.log(g) if g > 0 else -50.0
        st.in_pos += pos != 0
        if closed is not None:
            st.trades.append(closed)
        for k, (a, b) in ranges.items():
            if a <= i < b:
                w = wins[k]
                w.n += 1
                w.sum_r += r
                w.sum_r2 += r * r
                w.log_growth += math.log(g) if g > 0 else -50.0
                w.in_pos += pos != 0
                if closed is not None:
                    w.trades.append(closed)
                weq[k] *= g
                peaks[k] = max(peaks[k], weq[k])
                w.max_dd = max(w.max_dd, 1.0 - weq[k] / peaks[k])
    return years, wins


def metrics(s: Stats, bars_per_year: float) -> dict:
    if s.n == 0:
        return {}
    growth = math.exp(s.log_growth)
    mean = s.sum_r / s.n
    var = max(s.sum_r2 / s.n - mean * mean, 0.0)
    sharpe = mean / math.sqrt(var) * math.sqrt(bars_per_year) if var > 0 else 0.0
    yrs = s.n / bars_per_year
    cagr = growth ** (1 / yrs) - 1 if yrs > 0 and growth > 0 else -1.0
    wins = [x for x in s.trades if x > 0]
    losses = [-x for x in s.trades if x <= 0]
    return {
        "return": growth - 1,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_dd": s.max_dd,
        "calmar": cagr / s.max_dd if s.max_dd > 0 else 0.0,
        "exposure": s.in_pos / s.n,
        "trades": len(s.trades),
        "trades_per_year": len(s.trades) / yrs if yrs else 0.0,
        "win_rate": len(wins) / len(s.trades) if s.trades else 0.0,
        "profit_factor": (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else float("inf") if wins else 0.0,
    }
