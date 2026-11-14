"""Command line: ``python3 -m cta BTC ETH SOL --tf 15m 1h 4h 1d 1w``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analysis import DEFAULT_TIMEFRAMES, Config, analyze_symbol
from .data import INTERVAL_MINUTES, normalize_symbol
from .report import render_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python3 -m cta",
        description="Analisa crypto multi-timeframe: EMA 50/200, Supertrend, market structure "
                    "(data Binance spot, tanpa API key).")
    p.add_argument("symbols", nargs="*", default=["BTCUSDT"],
                   help="Pair Binance, mis. BTCUSDT ETHBTC; 'sol' otomatis jadi SOLUSDT (default: BTCUSDT)")
    p.add_argument("--tf", nargs="+", default=list(DEFAULT_TIMEFRAMES), metavar="TF",
                   help=f"Timeframe (default: {' '.join(DEFAULT_TIMEFRAMES)}). "
                        f"Pilihan: {' '.join(INTERVAL_MINUTES)}")
    p.add_argument("--format", choices=("md", "json"), default="md", help="Format output (default: md)")
    p.add_argument("--out", type=Path, help="Tulis ke file, bukan stdout")
    p.add_argument("--json-out", type=Path, help="Sekaligus tulis hasil JSON ke file ini")
    g = p.add_argument_group("parameter indikator")
    g.add_argument("--ema-fast", type=int, default=50)
    g.add_argument("--ema-slow", type=int, default=200)
    g.add_argument("--st-period", type=int, default=10, help="ATR period Supertrend (default 10)")
    g.add_argument("--st-mult", type=float, default=3.0, help="Multiplier Supertrend (default 3)")
    g.add_argument("--swing", type=int, default=5,
                   help="Bar kiri/kanan untuk swing high/low market structure (default 5)")
    g.add_argument("--limit", type=int, default=1000, help="Jumlah candle per timeframe (maks 1000)")
    g.add_argument("--include-open", action="store_true",
                   help="Ikutkan candle yang belum close (default: hanya candle tertutup)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bad = [t for t in args.tf if t not in INTERVAL_MINUTES]
    if bad:
        print(f"timeframe tidak dikenal: {' '.join(bad)}", file=sys.stderr)
        return 2
    if args.ema_fast >= args.ema_slow:
        print("--ema-fast harus lebih kecil dari --ema-slow", file=sys.stderr)
        return 2
    cfg = Config(ema_fast=args.ema_fast, ema_slow=args.ema_slow, st_period=args.st_period,
                 st_mult=args.st_mult, swing_left=args.swing, swing_right=args.swing,
                 limit=args.limit, include_open=args.include_open)
    tfs = list(dict.fromkeys(args.tf))  # dedupe, keep order
    symbols = list(dict.fromkeys(normalize_symbol(s) for s in args.symbols))

    results = [analyze_symbol(s, tfs, cfg) for s in symbols]

    text = json.dumps(results, indent=2) if args.format == "json" else render_report(results)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"ditulis ke {args.out}", file=sys.stderr)
    else:
        print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"JSON ditulis ke {args.json_out}", file=sys.stderr)

    errors = [v["error"] for r in results
              for tf, v in r["timeframes"].items() if "error" in v]
    for e in errors:
        print(f"peringatan: {e}", file=sys.stderr)
    total = sum(len(r["timeframes"]) for r in results)
    return 1 if errors and len(errors) == total else 0
