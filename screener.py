"""AAOIFI Shari'ah Standard No. 21 bo'yicha skrining dvigateli."""
from __future__ import annotations

from dataclasses import dataclass, field

import haram_rules
from config import (
    CASH_RATIO_MAX,
    DEBT_RATIO_MAX,
    DEFENSE_IS_HARAM,
    HARAM_INCOME_MAX,
)
from data_source import DataError, Fundamentals, Quote, fetch_fundamentals, fetch_quote

HALAL = "halal"
HARAM = "haram"
DOUBTFUL = "doubtful"


@dataclass
class Ratio:
    label: str
    value: float | None
    limit: float
    passed: bool | None      # None = ma'lumot yo'q
    detail: str = ""


@dataclass
class Result:
    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    price: float | None = None
    market_cap: float | None = None
    verdict: str = DOUBTFUL
    activity_note: str = ""
    ratios: list[Ratio] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    purification_pct: float | None = None
    dividend_rate: float | None = None
    error: str = ""


def _ratio(label: str, numerator: float | None, denominator: float | None,
           limit: float) -> Ratio:
    if numerator is None or not denominator:
        return Ratio(label, None, limit, None, "ma'lumot yetarli emas")
    value = numerator / denominator
    return Ratio(label, value, limit, value < limit)


def screen(ticker: str) -> Result:
    ticker = ticker.upper().strip()
    res = Result(ticker=ticker)

    try:
        f: Fundamentals = fetch_fundamentals(ticker)
    except DataError as exc:
        res.error = str(exc)
        return res
    except Exception as exc:                       # tarmoq/yfinance nosozligi
        res.error = f"Ma'lumot olishda xato: {exc}"
        return res

    q: Quote = fetch_quote(ticker)
    res.name, res.sector, res.industry = f.name, f.sector, f.industry
    res.price = q.price
    res.dividend_rate = f.dividend_rate

    # Bozor kapitalizatsiyasi: real vaqtdagi narx x aksiyalar soni
    market_cap = q.market_cap
    if market_cap is None and q.price and f.shares_outstanding:
        market_cap = q.price * f.shares_outstanding
    res.market_cap = market_cap

    # ---------- 1-BOSQICH: faoliyat sohasi ----------
    activity = (
        haram_rules.check_sector(f.sector)
        or haram_rules.check_industry(f.industry)
        or haram_rules.check_summary(f.summary)
    )

    if activity:
        status, reason = activity
        # Mudofaa sohasi uchun sozlama
        if not DEFENSE_IS_HARAM and "Mudofaa" in reason:
            status = DOUBTFUL
        res.activity_note = reason
        if status == HARAM:
            res.verdict = HARAM
            return res                              # nisbatlarga hojat yo'q
        res.warnings.append(reason)
    else:
        res.activity_note = "Asosiy faoliyatda taqiqlangan yo'nalish topilmadi"

    # ---------- 2-BOSQICH: moliyaviy nisbatlar ----------
    res.ratios = [
        _ratio("Foizli qarz / Bozor kap.", f.total_debt, market_cap, DEBT_RATIO_MAX),
        _ratio("Naqd + foizli invest. / Bozor kap.", f.total_cash, market_cap,
               CASH_RATIO_MAX),
        _ratio("Foizli daromad / Umumiy daromad", f.interest_income, f.total_revenue,
               HARAM_INCOME_MAX),
    ]

    if market_cap is None:
        res.warnings.append("Bozor kapitalizatsiyasi aniqlanmadi")

    failed = [r for r in res.ratios if r.passed is False]
    unknown = [r for r in res.ratios if r.passed is None]

    if failed:
        res.verdict = HARAM
    elif unknown or res.warnings:
        res.verdict = DOUBTFUL
        for r in unknown:
            res.warnings.append(f"{r.label} — hisoblab bo'lmadi")
    else:
        res.verdict = HALAL

    # ---------- Tozalash (tathir) ----------
    inc_ratio = res.ratios[2].value
    if inc_ratio is not None and f.dividend_rate:
        res.purification_pct = inc_ratio

    return res
