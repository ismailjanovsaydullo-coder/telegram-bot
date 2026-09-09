"""Moliyaviy ma'lumot qatlami.

Strategiya:
  - Fundamental ma'lumot (qarz, naqd, daromad, soha) -> 24 soat keshlanadi.
  - Narx va bozor kapitalizatsiyasi -> HAR SAFAR yangi olinadi (real vaqt).
Shu sababli nisbatlar narx o'zgarishi bilan qayta hisoblanadi.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, asdict

import pandas as pd
import yfinance as yf

from config import CACHE_DB, CACHE_TTL_HOURS


# ---------------------------------------------------------------- ma'lumot idishi
@dataclass
class Fundamentals:
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    summary: str = ""
    country: str = ""
    currency: str = "USD"
    shares_outstanding: float | None = None
    total_debt: float | None = None
    total_cash: float | None = None          # naqd + qisqa muddatli investitsiya
    total_revenue: float | None = None
    interest_income: float | None = None     # taqiqlangan daromad proksisi
    dividend_rate: float | None = None       # yillik dividend ($/aksiya)
    fetched_at: float = 0.0


@dataclass
class Quote:
    price: float | None = None
    market_cap: float | None = None


class DataError(Exception):
    pass


# ---------------------------------------------------------------- kesh
def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(CACHE_DB)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS fundamentals (
               ticker TEXT PRIMARY KEY,
               payload TEXT NOT NULL,
               fetched_at REAL NOT NULL
           )"""
    )
    conn.commit()
    return conn


def _cache_get(ticker: str) -> Fundamentals | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT payload, fetched_at FROM fundamentals WHERE ticker = ?", (ticker,)
        ).fetchone()
    if not row:
        return None
    payload, fetched_at = row
    if time.time() - fetched_at > CACHE_TTL_HOURS * 3600:
        return None
    return Fundamentals(**json.loads(payload))


def _cache_put(f: Fundamentals) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO fundamentals VALUES (?, ?, ?)",
            (f.ticker, json.dumps(asdict(f)), f.fetched_at),
        )
        conn.commit()


# ---------------------------------------------------------------- yordamchilar
def _row_value(df: pd.DataFrame | None, *candidates: str) -> float | None:
    """Moliyaviy hisobot jadvalidan qator qiymatini oladi (eng so'nggi ustun)."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    index_map = {str(i).strip().lower(): i for i in df.index}
    for cand in candidates:
        key = cand.strip().lower()
        if key in index_map:
            series = df.loc[index_map[key]]
            for val in series:          # eng so'nggi chorak/yildan boshlab
                if pd.notna(val):
                    return float(val)
    return None


def _num(value) -> float | None:
    try:
        if value is None:
            return None
        v = float(value)
        return v if v == v else None    # NaN tekshiruvi
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- asosiy API
def fetch_fundamentals(ticker: str, force: bool = False) -> Fundamentals:
    """Fundamental ma'lumotni oladi (keshdan yoki yfinance'dan)."""
    ticker = ticker.upper().strip()
    if not force:
        cached = _cache_get(ticker)
        if cached:
            return cached

    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception as exc:
        raise DataError(f"yfinance xatosi: {exc}") from exc

    if not info.get("longName") and not info.get("shortName"):
        raise DataError("Bunday tiker topilmadi")

    # Balans va daromad hisobotlari (qarz/naqd info'da bo'lmasa zaxira sifatida)
    try:
        bs = t.quarterly_balance_sheet
        if bs is None or bs.empty:
            bs = t.balance_sheet
    except Exception:
        bs = None
    try:
        inc = t.income_stmt
    except Exception:
        inc = None

    total_debt = _num(info.get("totalDebt"))
    if total_debt is None:
        total_debt = _row_value(bs, "Total Debt")
    if total_debt is None:
        ltd = _row_value(bs, "Long Term Debt") or 0.0
        std = _row_value(bs, "Current Debt", "Short Long Term Debt") or 0.0
        total_debt = (ltd + std) or None

    total_cash = _num(info.get("totalCash"))
    if total_cash is None:
        total_cash = _row_value(
            bs,
            "Cash Cash Equivalents And Short Term Investments",
            "Cash And Cash Equivalents",
        )

    f = Fundamentals(
        ticker=ticker,
        name=info.get("longName") or info.get("shortName") or ticker,
        sector=info.get("sector") or "",
        industry=info.get("industry") or "",
        summary=info.get("longBusinessSummary") or "",
        country=info.get("country") or "",
        currency=info.get("currency") or "USD",
        shares_outstanding=_num(info.get("sharesOutstanding")),
        total_debt=total_debt,
        total_cash=total_cash,
        total_revenue=_num(info.get("totalRevenue")) or _row_value(inc, "Total Revenue"),
        interest_income=_row_value(inc, "Interest Income", "Net Interest Income"),
        dividend_rate=_num(info.get("dividendRate")),
        fetched_at=time.time(),
    )
    _cache_put(f)
    return f


def fetch_quote(ticker: str) -> Quote:
    """Real vaqtdagi narx va bozor kapitalizatsiyasi."""
    t = yf.Ticker(ticker.upper().strip())
    price = market_cap = None
    try:
        fi = t.fast_info
        price = _num(fi.get("last_price") if hasattr(fi, "get") else fi.last_price)
        market_cap = _num(fi.get("market_cap") if hasattr(fi, "get") else fi.market_cap)
    except Exception:
        pass
    if price is None:
        try:
            hist = t.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        except Exception:
            pass
    return Quote(price=price, market_cap=market_cap)


def ticker_exists(ticker: str) -> bool:
    """Tiker haqiqiyligini tez tekshiradi (OCR natijasini filtrlash uchun)."""
    try:
        fi = yf.Ticker(ticker).fast_info
        mc = fi.get("market_cap") if hasattr(fi, "get") else fi.market_cap
        return mc is not None
    except Exception:
        return False
