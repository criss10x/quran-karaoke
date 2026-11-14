"""Markdown rendering of ``analyze_symbol`` results."""

from __future__ import annotations

from typing import Optional

from .data import INTERVAL_MINUTES

ARROW = {"up": "▲ up", "down": "▼ down", "n/a": "n/a"}
STRUCT_ID = {"bullish": "Bullish", "bearish": "Bearish", "range": "Range", "unknown": "?"}

DISCLAIMER = ("_Bukan nasihat keuangan. Indikator bersifat lagging; selalu pakai manajemen "
              "risiko (stop loss, ukuran posisi)._")


def fmt_price(p: Optional[float]) -> str:
    if p is None:
        return "–"
    a = abs(p)
    if a >= 1000:
        return f"{p:,.2f}"
    if a >= 1:
        return f"{p:,.4f}"
    return f"{p:.6g}"


def fmt_pct(p: Optional[float], signed: bool = True) -> str:
    if p is None:
        return "–"
    return f"{p:+.2f}%" if signed else f"{p:.2f}%"


def _ago(n: Optional[int]) -> str:
    return "–" if n is None else f"{n} bar lalu"


def _break_cell(b: Optional[dict]) -> str:
    if not b:
        return "–"
    arrow = "↑" if b["direction"] == "bull" else "↓"
    return f"{b['kind']} {arrow} @ {fmt_price(b['level'])} ({b['bars_ago']}b)"


def render_symbol(res: dict) -> str:
    tfs = sorted(res["timeframes"], key=lambda t: INTERVAL_MINUTES[t])
    conf = res["confluence"]
    cfg = res["config"]
    ef, es = cfg["ema_fast"], cfg["ema_slow"]
    lines = [f"## {res['symbol']}", ""]
    price = res["last_price"]
    if price is None:
        price = next((res["timeframes"][t]["close"] for t in tfs if "close" in res["timeframes"][t]), None)
    conf_pct = "–" if conf["score_pct"] is None else f"{conf['score_pct']:+.0f}%"
    lines.append(f"**Harga terakhir:** {fmt_price(price)} · **Confluence MTF:** "
                 f"{conf['bias']} ({conf_pct}) · dibuat {res['generated_at']}")
    lines.append("")
    lines.append(f"> {conf['summary']}")
    lines.append("")
    sig_tf = res["timeframes"].get("4h", {})
    if "signals" in sig_tf:
        def sig(k):
            v = sig_tf["signals"][k]
            ago = "" if v["since_bars"] is None else f" sejak {v['since_bars']} bar"
            return f"**{v['state']}**{ago}"
        lines.append(f"**Formula teruji backtest (4h):** A · EMA{ef}/{es} cross → {sig('A')} · "
                     f"B · EMA{ef}/{es} + Supertrend → {sig('B')} "
                     f"<sub>(lihat docs/backtest.md)</sub>")
        lines.append("")

    head = (f"| TF | Close | EMA{ef} | EMA{es} | Cross | Supertrend | Struktur (bias / swing) "
            f"| BOS/CHoCH terakhir | Support | Resistance | Skor | Bias |")
    lines += [head, "|" + "---|" * 12]
    for tf in tfs:
        r = res["timeframes"][tf]
        if "error" in r:
            lines.append(f"| {tf} | ⚠️ {r['error']} |" + " |" * 10)
            continue
        e, st, s = r["ema"], r["supertrend"], r["structure"]
        cross = e["cross"] if e["cross"] == "n/a" else \
            f"{'Golden' if e['cross'] == 'golden' else 'Death'}" + \
            (f" ({e['cross_bars_ago']}b)" if e["cross_bars_ago"] is not None else "")
        flip = "" if st["flip_bars_ago"] is None else f" ({st['flip_bars_ago']}b)"
        lines.append(
            f"| {tf} | {fmt_price(r['close'])} "
            f"| {fmt_price(e['fast'])} ({fmt_pct(e['dist_fast_pct'])}) "
            f"| {fmt_price(e['slow'])} ({fmt_pct(e['dist_slow_pct'])}) "
            f"| {cross} "
            f"| {ARROW[st['direction']]} @ {fmt_price(st['line'])}{flip} "
            f"| {STRUCT_ID[s['bias']]} / {STRUCT_ID[s['swing_trend']]} "
            f"| {_break_cell(s['last_break'])} "
            f"| {fmt_price(s['support'])} | {fmt_price(s['resistance'])} "
            f"| {r['score']:+d} | {r['bias']} |")
    lines.append("")

    lines.append("<details><summary>Detail per timeframe</summary>")
    lines.append("")
    for tf in tfs:
        r = res["timeframes"][tf]
        if "error" in r:
            continue
        e, st, s = r["ema"], r["supertrend"], r["structure"]
        swings = " → ".join(f"{sw['label'] or sw['kind'][0].upper()} {fmt_price(sw['price'])}"
                            for sw in s["recent_swings"]) or "–"
        lines += [
            f"**{tf}** (candle {r['candle_time']}, {r['bars']} bar)",
            f"- EMA{ef} slope 5 bar: {fmt_pct(e['fast_slope_pct'])}; "
            f"cross EMA{ef}/{es}: {e['cross']} sejak {_ago(e['cross_bars_ago'])}",
            f"- Supertrend({st['period']}, {st['mult']}): {st['direction']}, jarak {fmt_pct(st['dist_pct'])}, "
            f"flip {_ago(st['flip_bars_ago'])}",
            f"- Swing terakhir: {swings}",
            f"- BOS terakhir: {_break_cell(s['last_bos'])}; CHoCH terakhir: {_break_cell(s['last_choch'])}",
            f"- Komponen skor: " + ", ".join(f"{k} {v:+d}" for k, v in r["components"].items()),
            "",
        ]
    lines.append("</details>")
    lines.append("")
    return "\n".join(lines)


def render_report(results: list[dict]) -> str:
    parts = ["# Analisa Crypto Multi-Timeframe", "",
             "EMA 50/200 · Supertrend · Market Structure (BOS/CHoCH) — data: Binance spot, candle tertutup.",
             ""]
    parts += [render_symbol(r) for r in results]
    parts += [
        "### Cara membaca",
        "- **Skor TF** (−5..+5): close vs EMA fast, close vs EMA slow, EMA fast vs slow, arah Supertrend, "
        "bias struktur (arah BOS/CHoCH terakhir). Masing-masing ±1.",
        "- **Confluence** (−100%..+100%): rata-rata tertimbang skor; timeframe besar berbobot lebih.",
        "- **BOS** = break searah bias struktur (lanjutan tren); **CHoCH** = break pertama melawan bias "
        "(tanda awal pembalikan). `(Nb)` = N bar lalu.",
        "",
        DISCLAIMER,
        "",
    ]
    return "\n".join(parts)
