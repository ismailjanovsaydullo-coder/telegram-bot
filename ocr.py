"""Rasmdan tiker belgilarini ajratib olish.

Asosiy g'oya: Tesseract ko'p axlat matn chiqaradi. Shu sababli natijani
haqiqiy tikerlar ro'yxati (NASDAQ + NYSE) bilan kesishtiramiz. Ro'yxat
yuklanmagan bo'lsa, stop-so'zlar filtri + yfinance tekshiruvi ishlaydi.
"""
from __future__ import annotations

import io
import re

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

from config import TESSERACT_CMD, TICKERS_FILE

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

TICKER_RE = re.compile(r"\b[A-Z]{1,5}\b")

# Birja terminallarida uchraydigan, tiker bo'lmagan so'zlar
STOPWORDS = {
    "OPEN", "HIGH", "LOW", "CLOSE", "VOL", "AVG", "BUY", "SELL", "BID", "ASK",
    "USD", "EUR", "GBP", "PM", "AM", "ET", "EST", "PST", "UTC", "MAX", "MIN",
    "DAY", "WEEK", "YEAR", "YTD", "EPS", "PE", "MKT", "CAP", "CHG", "PCT",
    "NEW", "OLD", "TOP", "ALL", "ADD", "EDIT", "MORE", "LESS", "NEXT", "BACK",
    "HOME", "MENU", "LIST", "VIEW", "CHART", "TRADE", "ORDER", "LIMIT", "STOP",
    "SHARE", "PRICE", "TOTAL", "VALUE", "GAIN", "LOSS", "LONG", "SHORT",
    "NYSE", "NASDAQ", "AMEX", "ETF", "IPO", "SEC", "CEO", "CFO", "INC", "CORP",
    "LTD", "PLC", "CO", "AND", "THE", "FOR", "YOU", "YOUR", "MY", "IS", "ON",
    "OFF", "IN", "OUT", "UP", "DOWN", "TO", "OF", "AT", "BY", "NA", "N",
    "MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN",
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT",
    "NOV", "DEC", "TIME", "DATE", "NAME", "TYPE", "QTY", "FEE", "TAX", "NET",
    "PORT", "CASH", "FUND", "RISK", "NEWS", "DATA", "LIVE", "REAL", "DEMO",
}

_universe: set[str] | None = None


def load_universe() -> set[str]:
    """Haqiqiy tikerlar ro'yxatini yuklaydi (bir marta)."""
    global _universe
    if _universe is not None:
        return _universe

    if TICKERS_FILE.exists():
        _universe = {
            line.strip().upper()
            for line in TICKERS_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    else:
        _universe = set()
    return _universe


def download_universe() -> int:
    """NASDAQ Trader saytidan barcha tikerlarni yuklab, faylga saqlaydi.
    setup_tickers.py orqali bir marta ishga tushiriladi."""
    import urllib.request

    urls = [
        "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt",
    ]
    symbols: set[str] = set()
    for url in urls:
        with urllib.request.urlopen(url, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
        for line in text.splitlines()[1:]:
            parts = line.split("|")
            if len(parts) < 2:
                continue
            sym = parts[1].strip().upper()
            if sym and sym.isalpha() and len(sym) <= 5:
                symbols.add(sym)

    if symbols:
        TICKERS_FILE.write_text("\n".join(sorted(symbols)), encoding="utf-8")
    return len(symbols)


def preprocess(img: Image.Image) -> Image.Image:
    """OCR aniqligini oshirish uchun rasmni tayyorlash."""
    img = img.convert("L")                       # kulrang
    w, h = img.size
    if w < 1600:                                 # kichik rasmlarni kattalashtirish
        scale = 1600 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    return img


def extract_tickers(image_bytes: bytes, max_items: int = 10) -> list[str]:
    """Rasm baytlaridan tiker ro'yxatini qaytaradi (tartib saqlanadi)."""
    img = Image.open(io.BytesIO(image_bytes))

    texts: list[str] = []
    for invert in (False, True):                 # qorong'i mavzuli skrinshotlar uchun
        proc = preprocess(img)
        if invert:
            proc = ImageOps.invert(proc)
        for psm in ("6", "11"):
            try:
                texts.append(
                    pytesseract.image_to_string(
                        proc,
                        config=f"--psm {psm} -c "
                               "tessedit_char_whitelist="
                               "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:%$+-/ ",
                    )
                )
            except Exception:
                continue

    universe = load_universe()
    seen: list[str] = []
    for text in texts:
        for cand in TICKER_RE.findall(text.upper()):
            if cand in seen or cand in STOPWORDS or len(cand) < 2:
                continue
            if universe:
                if cand in universe:
                    seen.append(cand)
            else:
                seen.append(cand)                # ro'yxat yo'q -> keyin tekshiriladi
            if len(seen) >= max_items:
                return seen
    return seen
