"""Offline unit tests (synthetic data, no network). Run: python3 tests/test_cta.py"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cta import indicators as ind  # noqa: E402
from cta.analysis import Config, analyze_candles, confluence  # noqa: E402
from cta.data import Candle, normalize_symbol  # noqa: E402
from cta.report import render_report  # noqa: E402
from cta.structure import find_breaks, find_swings, swing_trend  # noqa: E402
from cta.backtest import (Features, align_htf, entry_exit, make_rules, metrics,  # noqa: E402
                          resample, simulate)


def candles_from_closes(closes, wick=0.5):
    out, prev = [], closes[0]
    for i, c in enumerate(closes):
        o = prev
        out.append(Candle(i * 60_000, o, max(o, c) + wick, min(o, c) - wick, c, 1.0, i * 60_000 + 59_999))
        prev = c
    return out


def zigzag(points, steps=10):
    """Linear interpolation through turning points."""
    out = []
    for a, b in zip(points, points[1:]):
        out += [a + (b - a) * k / steps for k in range(steps)]
    return out + [points[-1]]


def test_ema_matches_hand_calc():
    v = [1, 2, 3, 4, 5, 6]
    e = ind.ema(v, 3)
    assert e[:2] == [None, None]
    assert e[2] == 2.0                          # SMA seed
    assert math.isclose(e[3], 0.5 * 4 + 0.5 * 2.0)  # alpha = 2/(3+1)
    assert math.isclose(e[5], 0.5 * 6 + 0.5 * e[4])


def test_ema_constant_and_short():
    assert ind.ema([7.0] * 20, 5)[-1] == 7.0
    assert ind.ema([1, 2], 5) == [None, None]


def test_rma():
    r = ind.rma([2, 4, 6, 8], 2)
    assert r[1] == 3 and r[2] == 4.5 and r[3] == 6.25


def test_rsi_matches_wilder_reference():
    # StockCharts' RSI(14) worked example (Wilder smoothing, same as TradingView ta.rsi).
    closes = [44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433,
              46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028, 46.0328, 46.4116,
              46.2222, 45.6439, 46.2122, 46.2521, 45.7137, 46.4515, 45.7835, 45.3548, 44.0288,
              44.1783, 44.2181, 44.5672, 43.4205, 42.6628, 43.1314]
    expected = [70.53, 66.32, 66.55, 69.41, 66.36, 57.97, 62.93, 63.26, 56.06, 62.38, 54.71,
                50.42, 39.99, 41.46, 41.87, 45.46, 37.30, 33.08, 37.77]
    r = ind.rsi(closes, 14)
    assert r[13] is None
    assert all(abs(a - b) < 0.005 for a, b in zip(r[14:], expected))


def test_rsi_extremes():
    assert ind.rsi(list(range(1, 30)), 14)[-1] == 100.0
    assert ind.rsi(list(range(30, 1, -1)), 14)[-1] == 0.0


def test_stoch_rsi_bounds_and_smoothing():
    closes = [100 + 10 * math.sin(i / 7) + 3 * math.sin(i / 2.3) for i in range(300)]
    r, k, d = ind.stoch_rsi(closes, 14, 14, 3, 3)
    first_k = next(i for i, v in enumerate(k) if v is not None)
    assert first_k == 14 + 13 + 2          # rsi warm-up + stoch window + K smoothing
    vals = [v for v in k + d if v is not None]
    assert min(vals) >= 0 and max(vals) <= 100
    assert min(vals) < 20 and max(vals) > 80  # an oscillating series visits both zones
    i = 200
    assert abs(d[i] - (k[i] + k[i - 1] + k[i - 2]) / 3) < 1e-9


def test_last_cross():
    assert ind.last_cross([1, 2, 3], [2, 2, 2]) == {"direction": "bull", "bars_ago": 0, "value": 3}
    assert ind.last_cross([1, 3, 3], [2, 2, 2])["bars_ago"] == 1
    assert ind.last_cross([3, 1, 1, 1], [2, 2, 2, 2])["direction"] == "bear"
    assert ind.last_cross([1, 1], [2, 2]) is None


def test_bars_since_change():
    assert ind.bars_since_change([1, 1, -1, -1, -1]) == 2
    assert ind.bars_since_change([1, -1]) == 0
    assert ind.bars_since_change([None, 1, 1]) is None
    assert ind.bars_since_change([]) is None


def test_structure_bullish_then_choch():
    # Higher highs / higher lows, then a sharp drop through the last higher low.
    closes = zigzag([100, 120, 110, 130, 120, 140, 130, 150, 100], steps=10)
    c = candles_from_closes(closes, wick=0)
    h, lo, cl = [x.high for x in c], [x.low for x in c], [x.close for x in c]
    swings = find_swings(h, lo, 3, 3)
    labels = [s.label for s in swings if s.label]
    assert "HH" in labels and "HL" in labels and "LH" not in labels
    breaks = find_breaks(swings, cl, 3)
    assert breaks[0].direction == "bull" and breaks[0].kind == "BOS"
    assert any(b.kind == "BOS" and b.direction == "bull" for b in breaks[1:])
    last = breaks[-1]
    assert last.direction == "bear" and last.kind == "CHoCH"
    assert last.level == 130  # the most recent higher low


def test_swing_trend():
    closes = zigzag([150, 130, 140, 120, 130, 110, 120], steps=10)
    c = candles_from_closes(closes, wick=0)
    sw = find_swings([x.high for x in c], [x.low for x in c], 3, 3)
    assert swing_trend(sw) == "bearish"


def test_no_lookahead():
    # A break can never be reported on or before the bar that confirms the swing.
    closes = zigzag([100, 120, 110, 130, 90, 140], steps=8)
    c = candles_from_closes(closes, wick=0)
    sw = find_swings([x.high for x in c], [x.low for x in c], 3, 3)
    for b in find_breaks(sw, [x.close for x in c], 3):
        assert b.index > b.swing_index + 3


def test_analyze_candles_end_to_end():
    closes = [100 * (1.002 ** i) + 3 * math.sin(i / 4) for i in range(400)]
    r = analyze_candles(candles_from_closes(closes), Config())
    assert r["ema"]["cross"] == "golden"
    assert r["stoch_rsi"]["k"] is not None and r["stoch_rsi"]["zone"] in ("overbought", "oversold", "neutral")
    assert r["score"] >= 3 and "Bullish" in r["bias"]
    conf = confluence({"1h": r, "4h": r, "1d": r})
    assert conf["score_pct"] > 50 and "naik" in conf["summary"]
    res = {"symbol": "TESTUSDT", "generated_at": "now", "last_price": None,
           "config": Config().__dict__, "timeframes": {"1h": r, "4h": {"error": "boom"}},
           "confluence": conf}
    md = render_report([res])
    assert "TESTUSDT" in md and "boom" in md and "Golden" in md


def test_formula_signals():
    wavy_up = [100 * (1.002 ** i) + 2 * math.sin(i / 3) for i in range(400)]
    up = analyze_candles(candles_from_closes(wavy_up), Config())
    assert up["signals"]["A"]["state"] == "LONG" and up["signals"]["B"]["state"] == "LONG"
    wavy_down = [100 * (0.998 ** i) + 2 * math.sin(i / 3) for i in range(400)]
    down = analyze_candles(candles_from_closes(wavy_down), Config())
    assert down["signals"]["A"]["state"] == "FLAT" and down["signals"]["B"]["state"] == "FLAT"
    short = analyze_candles(candles_from_closes([100 + i + math.sin(i) for i in range(120)]), Config())
    assert short["signals"]["A"]["state"] == "n/a"   # EMA 200 not warmed up


def test_entry_exit_state_machine():
    assert entry_exit([0, 1, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0]) == [0, 1, 1, 0, 1, 1]
    assert entry_exit([1, 1], [1, 0]) == [0, 1]     # exit wins on the same bar


def test_formula_b_matches_backtest_rule():
    closes = [100 + 15 * math.sin(i / 25) + i * 0.03 + 2 * math.sin(i / 3) for i in range(800)]
    c = candles_from_closes(closes)
    rule = next(r for r in make_rules() if r.label == "STRUCT+CLOSE>EMA(swing=5, ema=200)")
    target = rule.fn(Features(c), None)
    for n in (400, 550, 700, 800):
        state = analyze_candles(c[:n], Config())["signals"]["B"]["state"]
        assert state == ("LONG" if target[n - 1] else "FLAT")


def test_live_score_matches_backtest_features():
    closes = [100 + 10 * math.sin(i / 15) + i * 0.05 for i in range(600)]
    c = candles_from_closes(closes)
    cfg = Config()
    F = Features(c)
    sc = F.score(cfg.ema_fast, cfg.ema_slow, cfg.swing_left)
    for n in (300, 450, 600):
        assert analyze_candles(c[:n], cfg)["score"] == sc[n - 1]


def test_warmup_without_ema_slow():
    r = analyze_candles(candles_from_closes([100 + i for i in range(120)]), Config())
    assert r["ema"]["slow"] is None and r["ema"]["cross"] == "n/a"
    assert r["components"]["close_vs_ema_slow"] == 0


def test_normalize_symbol():
    assert normalize_symbol("btc") == "BTCUSDT"
    assert normalize_symbol("eth/usdt") == "ETHUSDT"
    assert normalize_symbol("ETHBTC") == "ETHBTC"
    assert normalize_symbol("bnb") == "BNBUSDT"
    assert normalize_symbol("sol-usdc") == "SOLUSDC"


def _bt_candles(opens_closes, start_ms=1_704_067_200_000, step=86_400_000):
    """Candles from (open, close) pairs, daily, starting 2024-01-01."""
    return [Candle(start_ms + i * step, o, max(o, c), min(o, c), c, 1.0, start_ms + (i + 1) * step - 1)
            for i, (o, c) in enumerate(opens_closes)]


def test_simulate_next_open_execution_and_costs():
    # Prices double between bar 1 open and bar 2 close; signal fires at the close of bar 0.
    F = Features(_bt_candles([(10, 10), (10, 15), (15, 20), (20, 20)]))
    target = [1, 1, 0, 0]          # long decided at close of bar 0 -> filled at open of bar 1
    win = {"all": (0, 2**62)}
    _, w = simulate(F, target, 1, 0.0, win)
    m = metrics(w["all"], 365)
    assert abs(m["return"] - 1.0) < 1e-12          # 10 -> 20 exactly, no look-ahead fill
    assert m["trades"] == 1 and m["win_rate"] == 1.0
    _, w = simulate(F, target, 1, 0.01, win)        # 1% per side
    assert abs(metrics(w["all"], 365)["return"] - (2.0 * 0.99 * 0.99 - 1)) < 1e-12


def test_simulate_signal_on_last_bar_not_traded():
    F = Features(_bt_candles([(10, 10), (10, 30)]))
    _, w = simulate(F, [0, 1], 1, 0.0, {"all": (0, 2**62)})
    assert metrics(w["all"], 365)["return"] == 0.0  # signal at the final close is never filled


def test_max_drawdown():
    F = Features(_bt_candles([(100, 100), (100, 120), (120, 60), (60, 90)]))
    _, w = simulate(F, [1, 1, 1, 1], 1, 0.0, {"all": (0, 2**62)})
    m = metrics(w["all"], 365)
    assert abs(m["max_dd"] - 0.5) < 1e-12 and abs(m["return"] - (-0.1)) < 1e-12


def test_resample_weekly_and_htf_alignment():
    day = 86_400_000
    monday = 1_704_067_200_000  # 2024-01-01 was a Monday
    daily = [Candle(monday + i * day, i, i + 0.5, i - 0.5, i + 0.25, 1.0, monday + (i + 1) * day - 1)
             for i in range(15)]
    weeks = resample(daily, 7 * 24 * 60)
    assert len(weeks) == 3 and weeks[0].open_time == monday
    assert weeks[0].open == 0 and weeks[0].close == 6.25 and weeks[0].high == 6.5 and weeks[0].volume == 7
    L, H = Features(daily), Features(weeks)
    a = align_htf(L, H, [10, 20, 30])
    assert a[:6] == [None] * 6      # first week not closed until Sunday's close
    assert a[6] == 10 and a[12] == 10 and a[13] == 20
    assert a[14] == 20              # the partial 3rd week is never visible


def test_rules_have_no_lookahead():
    # Changing only the future must never change a rule's past targets.
    closes = [100 + 10 * math.sin(i / 9) + i * 0.1 + 3 * math.sin(i / 2.1) for i in range(700)]
    full = candles_from_closes(closes)
    cut = 500
    altered = full[:cut] + candles_from_closes([c * 1.5 for c in closes])[cut:]
    F1, F2 = Features(full), Features(altered)
    H1, H2 = Features(resample(full, 240)), Features(resample(altered, 240))
    for rule in make_rules():
        a, b = rule.fn(F1, H1), rule.fn(F2, H2)
        assert a[:cut - 10] == b[:cut - 10], rule.label


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print(f"ok  {name}")
    print(f"{len(tests)} tests passed")
