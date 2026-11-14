"""Search for a robust rule set: grid backtest, train/test split and walk-forward.

    python3 -m cta.research --symbols BTC ETH BNB SOL XRP ADA --tf 1h 4h 1d \\
        --out docs/backtest.md --json data/backtest.json

Selection is done on the **train** window only, ranked by the median Sharpe across all
symbols (a rule must work on most coins, not just one). The **test** window is never used
for selection. The walk-forward table repeats the selection every year using the previous
three years, which is the honest estimate of "pick the best formula, then trade it".
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .backtest import Features, Stats, make_rules, metrics, resample, simulate
from .data import INTERVAL_MINUTES, fetch_history, normalize_symbol

DATA_START = "2018-01-01"
EVAL_START = "2019-01-01"   # one year of warm-up for EMA 200 on 1d
TRAIN_END = "2024-01-01"    # train 2019-2023, test 2024 -> today
HTF_OF = {"15m": "1h", "30m": "2h", "1h": "4h", "2h": "8h", "4h": "1d", "6h": "1d",
          "8h": "1d", "12h": "1w", "1d": "1w"}
WARMUP_BARS = 300


def ms(date: str) -> int:
    return int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def bpy(tf: str) -> float:
    return 365 * 1440 / INTERVAL_MINUTES[tf]


def run_grid(symbols, tfs, cache_dir, cost, log=print):
    rules = make_rules()
    rows = []
    for tf in tfs:
        for sym in symbols:
            t0 = time.time()
            candles = fetch_history(sym, tf, ms(DATA_START), cache_dir)
            if len(candles) < WARMUP_BARS + 100:
                log(f"skip {sym} {tf}: only {len(candles)} candles")
                continue
            F = Features(candles)
            H = Features(resample(candles, INTERVAL_MINUTES[HTF_OF[tf]]))
            start = max(WARMUP_BARS, next(i for i, t in enumerate(F.t) if t >= ms(EVAL_START))
                        if F.t[-1] >= ms(EVAL_START) else len(F.t))
            windows = {"train": (ms(EVAL_START), ms(TRAIN_END)), "test": (ms(TRAIN_END), 2**62),
                       "full": (ms(EVAL_START), 2**62)}
            for rule in rules:
                years, wins = simulate(F, rule.fn(F, H), start, cost, windows)
                rows.append({"symbol": sym, "tf": tf, "rule": rule.label, "name": rule.name,
                             "years": years, **{k: metrics(v, bpy(tf)) for k, v in wins.items()}})
            log(f"{sym} {tf}: {len(candles)} bars, {len(rules)} rules, {time.time() - t0:.0f}s")
    return rows


def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def summarize(rows, tf, window):
    by_rule: dict[str, list] = {}
    for r in rows:
        if r["tf"] == tf and r.get(window):
            by_rule.setdefault(r["rule"], []).append(r)
    out = []
    for rule, rs in by_rule.items():
        m = [r[window] for r in rs]
        out.append({
            "rule": rule, "name": rs[0]["name"], "n": len(rs),
            "sharpe": _med([x["sharpe"] for x in m]),
            "cagr": _med([x["cagr"] for x in m]),
            "max_dd": _med([x["max_dd"] for x in m]),
            "calmar": _med([x["calmar"] for x in m]),
            "exposure": _med([x["exposure"] for x in m]),
            "tpy": _med([x["trades_per_year"] for x in m]),
            "win": _med([x["win_rate"] for x in m]),
            "per_symbol": {r["symbol"]: r[window] for r in rs},
        })
    return {o["rule"]: o for o in out}


def walk_forward(rows, tf, first_year, last_year, lookback=3, min_tpy=1.0):
    """Each year pick the rule with the best median Sharpe over the previous ``lookback`` years."""
    per = {}
    for r in rows:
        if r["tf"] == tf:
            per.setdefault(r["rule"], {})[r["symbol"]] = r["years"]
    symbols = sorted({s for d in per.values() for s in d})
    steps = []
    chain = {s: 1.0 for s in symbols}
    chain_bh = {s: 1.0 for s in symbols}
    for y in range(first_year, last_year + 1):
        best, best_val = None, None
        for rule, d in per.items():
            sh = []
            for s, yrs in d.items():
                st = Stats()
                for yy in range(y - lookback, y):
                    if yy in yrs:
                        st = st.merge(yrs[yy])
                if st.n:
                    m = metrics(st, bpy(tf))
                    if m["trades_per_year"] >= min_tpy or rule == "BUY_HOLD":
                        sh.append(m["sharpe"])
            v = _med(sh)
            if v is not None and (best_val is None or v > best_val):
                best, best_val = rule, v
        rets, bh = {}, {}
        for s in symbols:
            ys = per[best].get(s, {})
            yb = per["BUY_HOLD"].get(s, {})
            if y in ys and y in yb:
                rets[s] = metrics(ys[y], bpy(tf))["return"]
                bh[s] = metrics(yb[y], bpy(tf))["return"]
                chain[s] *= 1 + rets[s]
                chain_bh[s] *= 1 + bh[s]
        steps.append({"year": y, "rule": best, "train_sharpe": best_val,
                      "median_ret": _med(list(rets.values())), "median_bh": _med(list(bh.values())),
                      "rets": rets, "bh": bh})
    return {"steps": steps, "total": {s: chain[s] - 1 for s in symbols},
            "total_bh": {s: chain_bh[s] - 1 for s in symbols}}


# --------------------------------------------------------------------------- report

def pct(x, d=0):
    return "–" if x is None else f"{x * 100:+.{d}f}%"


def num(x, d=2):
    return "–" if x is None else f"{x:.{d}f}"


def render(rows, symbols, tfs, cost, top=12):
    L = ["# Backtest — EMA · Supertrend · Market Structure", ""]
    L.append(f"Dibuat {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · data Binance spot · koin: "
             f"{', '.join(symbols)} · biaya {cost * 100:.2f}% per sisi (fee + slippage) · "
             f"long/flat (spot, tanpa leverage).")
    L.append("")
    L.append(f"- **Train** (untuk memilih formula): {EVAL_START} s/d {TRAIN_END} (eksklusif).")
    L.append(f"- **Test / out-of-sample** (tidak pernah dipakai memilih): {TRAIN_END} s/d data terakhir.")
    L.append("- Sinyal dihitung saat candle close, eksekusi di open candle berikutnya.")
    L.append("- Ranking = **median** Sharpe antar koin di periode train (formula harus bagus di "
             "mayoritas koin, bukan satu koin saja). Angka di tabel adalah median antar koin.")
    L.append("")
    for tf in tfs:
        tr, te = summarize(rows, tf, "train"), summarize(rows, tf, "test")
        if not tr:
            continue
        bh_tr, bh_te = tr.get("BUY_HOLD"), te.get("BUY_HOLD")
        L.append(f"## Timeframe {tf}")
        L.append("")
        L.append(f"Buy & hold — train: Sharpe {num(bh_tr['sharpe'])}, CAGR {pct(bh_tr['cagr'])}, "
                 f"MaxDD {pct(bh_tr['max_dd'])} · test: Sharpe {num(bh_te['sharpe'])}, CAGR "
                 f"{pct(bh_te['cagr'])}, MaxDD {pct(bh_te['max_dd'])}")
        L.append("")
        L.append("**Per keluarga formula** (median semua kombinasi parameter × semua koin; "
                 "*% kombinasi > B&H* = porsi kombinasi parameter yang Sharpe test-nya mengalahkan "
                 "buy & hold di koin yang sama):")
        L.append("")
        L.append("| Keluarga | Kombinasi | Train Sharpe | Test Sharpe | Test CAGR | Test MaxDD | % kombinasi > B&H (test) |")
        L.append("|---|---|---|---|---|---|---|")
        fams = {}
        for r in rows:
            if r["tf"] == tf and r.get("test") and r.get("train"):
                fams.setdefault(r["name"], []).append(r)
        bh_by_sym = {r["symbol"]: r["test"]["sharpe"] for r in rows
                     if r["tf"] == tf and r["name"] == "BUY_HOLD" and r.get("test")}
        fam_rows = []
        for name, rs in fams.items():
            beat = [r["test"]["sharpe"] > bh_by_sym.get(r["symbol"], 0) for r in rs]
            fam_rows.append((name, len({r["rule"] for r in rs}), _med([r["train"]["sharpe"] for r in rs]),
                             _med([r["test"]["sharpe"] for r in rs]), _med([r["test"]["cagr"] for r in rs]),
                             _med([r["test"]["max_dd"] for r in rs]), sum(beat) / len(beat)))
        for f in sorted(fam_rows, key=lambda f: f[3], reverse=True):
            L.append(f"| `{f[0]}` | {f[1]} | {num(f[2])} | {num(f[3])} | {pct(f[4])} | {pct(f[5])} | "
                     f"{'–' if f[0] == 'BUY_HOLD' else pct(f[6]).lstrip('+')} |")
        L.append("")
        L.append(f"**Top {top} formula berdasarkan train** (lalu lihat apakah bertahan di test):")
        L.append("")
        ranked = sorted((r for r in tr.values() if r["name"] != "BUY_HOLD" and (r["tpy"] or 0) >= 1),
                        key=lambda r: r["sharpe"], reverse=True)[:top]
        L.append("| # | Formula | Train Sharpe | Train CAGR | Train MaxDD | **Test Sharpe** | "
                 "**Test CAGR** | **Test MaxDD** | Exposure | Trade/thn | Win% |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for i, r in enumerate(ranked, 1):
            t = te.get(r["rule"], {})
            L.append(f"| {i} | `{r['rule']}` | {num(r['sharpe'])} | {pct(r['cagr'])} | {pct(r['max_dd'])} "
                     f"| **{num(t.get('sharpe'))}** | **{pct(t.get('cagr'))}** | **{pct(t.get('max_dd'))}** "
                     f"| {pct(t.get('exposure'))} | {num(t.get('tpy'), 1)} | {pct(t.get('win'))} |")
        L.append("")
        defaults = ["EMA_CROSS(ema=50/200)", "CLOSE>EMA(ema=200)", "ST(st=10/3)", "STRUCT(swing=5)",
                    "ST+CLOSE>EMA(st=10/3, ema=200)", "ST+EMA_CROSS(st=10/3, ema=50/200)",
                    "ST+STRUCT(st=10/3, swing=5)", "SCORE>=(k=3, st=10/3, ema=50/200, swing=5)",
                    "SCORE>=(k=4, st=10/3, ema=50/200, swing=5)", "ST+HTF_ST(st=10/3, htf_st=10/3)"]
        L.append("<details><summary>Parameter default (EMA 50/200, Supertrend 10/3, swing 5)</summary>")
        L.append("")
        L.append("| Formula | Train Sharpe | Train CAGR | Train MaxDD | Test Sharpe | Test CAGR | Test MaxDD | Trade/thn |")
        L.append("|---|---|---|---|---|---|---|---|")
        for d in ["BUY_HOLD"] + defaults:
            if d in tr:
                r, t = tr[d], te.get(d, {})
                L.append(f"| `{d}` | {num(r['sharpe'])} | {pct(r['cagr'])} | {pct(r['max_dd'])} "
                         f"| {num(t.get('sharpe'))} | {pct(t.get('cagr'))} | {pct(t.get('max_dd'))} "
                         f"| {num(t.get('tpy'), 1)} |")
        L.append("")
        L.append("</details>")
        L.append("")
        last_year = max(y for r in rows if r["tf"] == tf for y in r["years"])
        wf = walk_forward(rows, tf, int(EVAL_START[:4]) + 3, last_year)
        L.append(f"**Walk-forward {tf}** (tiap tahun pilih formula terbaik dari 3 tahun sebelumnya, "
                 f"lalu dipakai tahun itu):")
        L.append("")
        L.append("| Tahun | Formula terpilih | Median return | Median buy & hold |")
        L.append("|---|---|---|---|")
        for s in wf["steps"]:
            L.append(f"| {s['year']} | `{s['rule']}` | {pct(s['median_ret'])} | {pct(s['median_bh'])} |")
        tot = ", ".join(f"{s.replace('USDT', '')} {pct(v)} (B&H {pct(wf['total_bh'][s])})"
                        for s, v in wf["total"].items())
        L.append("")
        L.append(f"Total walk-forward per koin: {tot}")
        L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m cta.research", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", nargs="+", default=["BTC", "ETH", "BNB", "SOL", "XRP", "ADA"])
    ap.add_argument("--tf", nargs="+", default=["1h", "4h", "1d"])
    ap.add_argument("--cost", type=float, default=0.0015, help="biaya per sisi (default 0.0015 = 0.15%%)")
    ap.add_argument("--cache", default="data", help="folder cache candle (default: data)")
    ap.add_argument("--out", type=Path, help="tulis laporan Markdown")
    ap.add_argument("--json", type=Path, help="tulis ringkasan JSON (train/test per koin per formula)")
    args = ap.parse_args(argv)
    symbols = [normalize_symbol(s) for s in args.symbols]
    rows = run_grid(symbols, args.tf, args.cache, args.cost, log=lambda m: print(m, file=sys.stderr))
    md = render(rows, symbols, args.tf, args.cost)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md + "\n", encoding="utf-8")
    else:
        print(md)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        slim = [{k: v for k, v in r.items() if k != "years"} for r in rows]
        args.json.write_text(json.dumps(slim, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
