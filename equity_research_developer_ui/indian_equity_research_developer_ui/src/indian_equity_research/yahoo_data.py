"""Minimal Yahoo Finance daily data helper.

This module provides a small, self-contained wrapper around the
`query1.finance.yahoo.com` endpoints to fetch recent daily OHLC data and
basic derived metrics. It deliberately avoids any additional
third‑party dependencies beyond ``requests``.

The goal is to give the app and any downstream agents a way to obtain
explicit, timestamped daily data for basic analysis, without changing
the existing myGenAssist research flow.

Security / safety:
- No secrets or tokens are used.
- Only public Yahoo Finance endpoints are called.
- Callers must handle connectivity errors gracefully.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


@dataclass(frozen=True)
class YahooCandle:
    """Single daily OHLCV candle from Yahoo Finance.

    All monetary values are floats as returned by Yahoo. ``timestamp`` is
    normalised to UTC seconds since epoch.
    """

    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int

    @property
    def iso_time(self) -> str:
        """Return the candle timestamp as an ISO 8601 string in UTC."""

        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class YahooDailySummary:
    """Summary of recent daily data with simple derived metrics.

    This keeps the abstraction intentionally small so it can be consumed by
    either the Flask app or future agent prompts.
    """

    symbol: str
    candles: List[YahooCandle]
    latest_close: Optional[float]
    latest_time_utc: Optional[str]
    daily_change: Optional[float]
    daily_change_pct: Optional[float]
    sma_5: Optional[float]


class YahooFinanceError(RuntimeError):
    """Raised when Yahoo Finance data cannot be retrieved or parsed."""


def _call_yahoo_chart(symbol: str, interval: str = "1d", range_: str = "1mo") -> Dict[str, Any]:
    """Call the Yahoo Finance chart endpoint for a given symbol.

    Parameters
    ----------
    symbol:
        Yahoo Finance ticker (e.g., "RELIANCE.NS").
    interval:
        Candle interval, defaults to daily ("1d").
    range_:
        History range, e.g., "5d", "1mo", "3mo".

    Returns
    -------
    dict
        Parsed JSON payload from Yahoo.

    Raises
    ------
    YahooFinanceError
        If the response is not OK or cannot be interpreted.
    """

    url = "https://query1.finance.yahoo.com/v8/finance/chart/{}".format(symbol)
    params = {"interval": interval, "range": range_}
    try:
        response = requests.get(url, params=params, timeout=10)
    except Exception as exc:  # pragma: no cover - network
        raise YahooFinanceError(f"Yahoo Finance request failed: {exc}") from exc

    if not response.ok:
        raise YahooFinanceError(
            f"Yahoo Finance returned HTTP {response.status_code} for symbol {symbol}."
        )

    try:
        payload = response.json()
    except ValueError as exc:  # pragma: no cover - defensive
        raise YahooFinanceError("Yahoo Finance returned non‑JSON response.") from exc

    return payload


def _parse_candles(payload: Dict[str, Any]) -> List[YahooCandle]:
    """Extract daily candles from the chart payload.

    Yahoo returns data under ``chart.result[0].indicators.quote[0]`` with a
    parallel ``timestamp`` array. We stitch these together and filter out
    incomplete entries.
    """

    result = payload.get("chart", {}).get("result") or []
    if not result:
        return []

    series = result[0]
    timestamps = series.get("timestamp") or []
    indicators = series.get("indicators", {})
    quotes = indicators.get("quote") or []
    if not timestamps or not quotes:
        return []

    quote = quotes[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    candles: List[YahooCandle] = []
    for idx, ts in enumerate(timestamps):
        try:
            o = float(opens[idx])
            h = float(highs[idx])
            l = float(lows[idx])
            c = float(closes[idx])
            v_raw = volumes[idx]
            v = int(v_raw) if v_raw is not None else 0
        except (IndexError, TypeError, ValueError):
            continue
        candles.append(YahooCandle(timestamp=int(ts), open=o, high=h, low=l, close=c, volume=v))

    return candles


def _simple_moving_average(values: List[float], window: int) -> Optional[float]:
    if len(values) < window:
        return None
    return sum(values[-window:]) / float(window)


def get_daily_summary(symbol: str, range_: str = "1mo") -> YahooDailySummary:
    """Fetch recent daily data and compute basic derived metrics.

    This helper focuses on a compact slice of functionality:
    - fetches up to ``range_`` worth of daily OHLCV data;
    - identifies the latest close and its timestamp;
    - computes the absolute and percentage daily change vs the previous close;
    - computes a simple 5‑day moving average (SMA5) when enough data exists.

    Parameters
    ----------
    symbol:
        Yahoo Finance ticker, e.g., "RELIANCE.NS".
    range_:
        History range string accepted by Yahoo (default: "1mo").

    Raises
    ------
    YahooFinanceError
        If the upstream call fails or no usable candles are available.
    """

    payload = _call_yahoo_chart(symbol, interval="1d", range_=range_)
    candles = _parse_candles(payload)
    if not candles:
        raise YahooFinanceError(f"No daily data available for symbol {symbol}.")

    latest = candles[-1]
    prev = candles[-2] if len(candles) >= 2 else None

    latest_close = latest.close
    latest_time_utc = latest.iso_time

    if prev is not None:
        daily_change = latest.close - prev.close
        daily_change_pct = (daily_change / prev.close) * 100 if prev.close else None
    else:
        daily_change = None
        daily_change_pct = None

    closes = [c.close for c in candles]
    sma5 = _simple_moving_average(closes, window=5)

    return YahooDailySummary(
        symbol=symbol,
        candles=candles,
        latest_close=latest_close,
        latest_time_utc=latest_time_utc,
        daily_change=daily_change,
        daily_change_pct=daily_change_pct,
        sma_5=sma5,
    )


def summary_to_dict(summary: YahooDailySummary) -> Dict[str, Any]:
    """Serialise a ``YahooDailySummary`` into a JSON‑serialisable dict.

    This is intended for use in Flask responses or for logging.
    """

    return {
        "symbol": summary.symbol,
        "latest_close": summary.latest_close,
        "latest_time_utc": summary.latest_time_utc,
        "daily_change": summary.daily_change,
        "daily_change_pct": summary.daily_change_pct,
        "sma_5": summary.sma_5,
        "candles": [
            {
                "timestamp": c.timestamp,
                "iso_time": c.iso_time,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
            for c in summary.candles
        ],
    }
