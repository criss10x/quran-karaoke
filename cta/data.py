"""Candle data from Binance's public spot market-data API (no API key needed).

Primary host is ``data-api.binance.vision`` (Binance's public market-data mirror,
which also answers from regions where ``api.binance.com`` is geo-blocked).
Override the host list with ``CTA_BINANCE_HOSTS=https://a,https://b``.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

DEFAULT_HOSTS = ("https://data-api.binance.vision", "https://api.binance.com")

# Binance spot kline intervals -> minutes (1M approximated as 30 days).
INTERVAL_MINUTES = {
    "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
    "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720,
    "1d": 1440, "3d": 4320, "1w": 10080, "1M": 43200,
}

QUOTE_ASSETS = ("USDT", "USDC", "FDUSD", "TUSD", "BUSD", "DAI", "BTC", "ETH", "BNB",
                "EUR", "TRY", "BRL", "JPY", "IDR")

MAX_LIMIT = 1000


class DataError(RuntimeError):
    """Raised when candles cannot be fetched."""


@dataclass(frozen=True)
class Candle:
    open_time: int   # ms since epoch, UTC
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int  # ms since epoch, UTC


def normalize_symbol(symbol: str, default_quote: str = "USDT") -> str:
    """``btc`` -> ``BTCUSDT``; ``eth/usdt`` -> ``ETHUSDT``; ``ETHBTC`` stays."""
    s = symbol.strip().upper().replace("/", "").replace("-", "").replace("_", "")
    if not s:
        raise ValueError("empty symbol")
    for q in QUOTE_ASSETS:
        if s.endswith(q) and len(s) > len(q):
            return s
    return s + default_quote


def _hosts() -> tuple[str, ...]:
    env = os.environ.get("CTA_BINANCE_HOSTS", "").strip()
    if env:
        return tuple(h.strip().rstrip("/") for h in env.split(",") if h.strip())
    return DEFAULT_HOSTS


def _get_json(url: str, timeout: float):
    req = urllib.request.Request(url, headers={"User-Agent": "cta-mtf/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_klines(symbol: str, interval: str, limit: int = MAX_LIMIT,
                 include_open: bool = False, timeout: float = 15.0,
                 retries: int = 3, start_time: int | None = None) -> list[Candle]:
    """Return up to ``limit`` candles, oldest first (the latest ones unless ``start_time``).

    The still-forming last candle is dropped unless ``include_open`` is set, so
    every signal is computed on closed candles only.
    """
    if interval not in INTERVAL_MINUTES:
        raise ValueError(f"unsupported interval {interval!r}; use one of "
                         f"{', '.join(INTERVAL_MINUTES)}")
    limit = max(1, min(int(limit), MAX_LIMIT))
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time is not None:
        params["startTime"] = int(start_time)
    query = urllib.parse.urlencode(params)

    errors: list[str] = []
    for host in _hosts():
        url = f"{host}/api/v3/klines?{query}"
        for attempt in range(retries):
            try:
                raw = _get_json(url, timeout)
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:200]
                if e.code == 400:  # bad symbol/params: no point trying other hosts
                    raise DataError(f"{symbol} {interval}: Binance rejected request: {body}") from e
                if e.code in (403, 451):  # geo-blocked / forbidden -> next host
                    errors.append(f"{host}: HTTP {e.code}")
                    raw = None
                    break
                errors.append(f"{host}: HTTP {e.code} {body}")
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                errors.append(f"{host}: {getattr(e, 'reason', e)}")
            raw = None
            if attempt < retries - 1:
                time.sleep(min(2 ** attempt, 8))
        if raw is not None:
            break
    else:
        raise DataError(f"{symbol} {interval}: all hosts failed: " + "; ".join(errors[-4:]))

    candles = [Candle(int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]),
                      float(k[5]), int(k[6])) for k in raw]
    if not include_open and candles and candles[-1].close_time > time.time() * 1000:
        candles = candles[:-1]
    return candles


def fetch_last_price(symbol: str, timeout: float = 10.0) -> float | None:
    """Latest traded price, or ``None`` if unavailable."""
    q = urllib.parse.urlencode({"symbol": symbol})
    for host in _hosts():
        try:
            return float(_get_json(f"{host}/api/v3/ticker/price?{q}", timeout)["price"])
        except Exception:  # noqa: BLE001 - best effort, falls back to last close
            continue
    return None


def fetch_history(symbol: str, interval: str, start_time: int,
                  cache_dir: str | os.PathLike | None = None, pause: float = 0.1) -> list[Candle]:
    """All closed candles from ``start_time`` (ms) until now, paginated 1000 at a time.

    With ``cache_dir`` the candles are kept in ``<cache_dir>/<SYMBOL>_<interval>.csv`` and
    later calls only download what is newer than the cache.
    """
    import csv
    from pathlib import Path

    candles: list[Candle] = []
    path = meta = None
    if cache_dir is not None:
        path = Path(cache_dir) / f"{symbol}_{interval}.csv"
        meta = path.with_suffix(".start")  # the start_time the cache was built from
        cached_from = int(meta.read_text()) if meta.exists() else None
        if path.exists() and cached_from is not None and cached_from <= start_time:
            with path.open(newline="") as f:
                candles = [Candle(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]),
                                  float(r[5]), int(r[6])) for r in csv.reader(f)]
        else:
            cached_from = start_time

    cursor = candles[-1].open_time + 1 if candles else start_time
    while True:
        batch = fetch_klines(symbol, interval, MAX_LIMIT, include_open=False, start_time=cursor)
        batch = [c for c in batch if c.open_time >= cursor]
        if not batch:
            break
        candles.extend(batch)
        cursor = batch[-1].open_time + 1
        if len(batch) < MAX_LIMIT - 1:
            break
        time.sleep(pause)

    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            for c in candles:
                w.writerow([c.open_time, c.open, c.high, c.low, c.close, c.volume, c.close_time])
        meta.write_text(str(cached_from))
    return [c for c in candles if c.open_time >= start_time]
