"""Halol aksiya skrineri — Telegram bot (aiogram 3)."""
from __future__ import annotations

import asyncio
import io
import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
import ocr
from config import BOT_TOKEN, MAX_TICKERS_PER_MESSAGE
from data_source import ticker_exists
from screener import DOUBTFUL, HALAL, HARAM, Result, screen

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("halalbot")

dp = Dispatcher()

BADGE = {
    HALAL: "✅ <b>HALOL</b>",
    HARAM: "⛔️ <b>HAROM</b>",
    DOUBTFUL: "⚠️ <b>SHUBHALI</b>",
}

DISCLAIMER = (
    "<i>Bu avtomatik skrining natijasi, fatvo emas. "
    "Ochiq moliyaviy hisobotlarga asoslangan. "
    "Yakuniy qarorda olimga murojaat qiling.</i>"
)

TICKER_INPUT_RE = re.compile(r"\b[A-Za-z]{1,5}\b")


# ---------------------------------------------------------------- formatlash
def fmt_money(v: float | None) -> str:
    if v is None:
        return "—"
    for unit, div in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= div:
            return f"${v / div:,.2f}{unit}"
    return f"${v:,.0f}"


def render(r: Result) -> str:
    if r.error:
        return f"❓ <b>{r.ticker}</b> — {r.error}"

    lines = [
        f"{BADGE.get(r.verdict, '')}",
        f"<b>{r.ticker}</b> — {r.name}",
        "",
        f"🏭 Soha: {r.industry or '—'} ({r.sector or '—'})",
        f"💵 Narx: {('$' + format(r.price, ',.2f')) if r.price else '—'}   "
        f"📊 Bozor kap.: {fmt_money(r.market_cap)}",
        "",
        "<b>1) Faoliyat skrining</b>",
        f"   {r.activity_note}",
    ]

    if r.verdict == HARAM and not r.ratios:
        lines += ["", "Faoliyat sohasi taqiqlangan — moliyaviy nisbatlar ko'rilmadi.",
                  "", DISCLAIMER]
        return "\n".join(lines)

    lines += ["", "<b>2) Moliyaviy nisbatlar (AAOIFI №21)</b>"]
    for ratio in r.ratios:
        if ratio.passed is None:
            mark, val = "❔", "ma'lumot yo'q"
        else:
            mark = "✅" if ratio.passed else "❌"
            val = f"{ratio.value * 100:.1f}%"
        lines.append(f"   {mark} {ratio.label}: <b>{val}</b> "
                     f"(chegara {ratio.limit * 100:.0f}%)")

    if r.warnings:
        lines += ["", "<b>⚠️ Diqqat</b>"]
        lines += [f"   • {w}" for w in dict.fromkeys(r.warnings)]

    if r.purification_pct and r.dividend_rate:
        per_share = r.dividend_rate * r.purification_pct
        lines += [
            "",
            f"🧹 <b>Tozalash (tathir):</b> har 1 aksiya dividendidan "
            f"~${per_share:.4f} sadaqa qilinadi "
            f"({r.purification_pct * 100:.2f}%)",
        ]

    lines += ["", DISCLAIMER]
    return "\n".join(lines)


# ---------------------------------------------------------------- handlerlar
@dp.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "🕌 <b>Halol Aksiya Skrineri</b>\n\n"
        "Amerika aksiyalarini AAOIFI (Shari'ah Standard №21) mezonlari "
        "bo'yicha tekshiraman.\n\n"
        "<b>Qanday ishlataman?</b>\n"
        "• Tiker yozing: <code>AAPL</code>\n"
        "• Bir nechta: <code>AAPL MSFT JPM KO</code>\n"
        "• Yoki broker/TradingView <b>skrinshotini</b> tashlang\n\n"
        "<b>Tekshiriladigan mezonlar:</b>\n"
        "1️⃣ Faoliyat sohasi taqiqlanganmi?\n"
        "2️⃣ Foizli qarz / bozor kap. &lt; 30%\n"
        "3️⃣ Naqd + foizli invest. / bozor kap. &lt; 30%\n"
        "4️⃣ Foizli daromad / umumiy daromad &lt; 5%\n\n"
        "/help — batafsil ma'lumot"
    )


@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(
        "<b>Natija turlari</b>\n"
        "✅ HALOL — barcha mezonlardan o'tdi\n"
        "⛔️ HAROM — faoliyat yoki nisbat mezoni buzilgan\n"
        "⚠️ SHUBHALI — ma'lumot yetarli emas yoki soha ixtilofli\n\n"
        "<b>Cheklovlar (rostini bilib qo'ying)</b>\n"
        "• Qarz va naqd ma'lumoti oxirgi <b>choraklik hisobotdan</b> olinadi "
        "(3 oyda bir yangilanadi). Narx esa real vaqtda — shuning uchun "
        "nisbatlar kun davomida o'zgaradi.\n"
        "• «Taqiqlangan daromad» aniq segment hisoboti bepul manbalarda yo'q. "
        "Uning o'rniga <b>foizli daromad</b> qatori proksi sifatida ishlatiladi. "
        "Bu taxminiy raqam.\n"
        "• Bot fatvo bermaydi, faqat ochiq ma'lumotlarni AAOIFI formulasiga "
        "solib beradi.\n\n"
        "<b>Manba:</b> Yahoo Finance (yfinance)"
    )


async def process_and_reply(msg: Message, tickers: list[str]):
    if not tickers:
        await msg.answer("Tiker topilmadi. Masalan: <code>AAPL</code>")
        return

    tickers = tickers[:MAX_TICKERS_PER_MESSAGE]
    status = await msg.answer(f"⏳ Tekshirilmoqda: {', '.join(tickers)}")

    for tk in tickers:
        try:
            result = await asyncio.to_thread(screen, tk)
            await msg.answer(render(result))
        except Exception as exc:
            log.exception("screen failed for %s", tk)
            await msg.answer(f"❓ <b>{tk}</b> — xatolik: {exc}")
        await asyncio.sleep(0.4)          # yfinance'ni bo'g'ib qo'ymaslik uchun

    try:
        await status.delete()
    except Exception:
        pass


@dp.message(F.photo | (F.document & F.document.mime_type.startswith("image/")))
async def handle_image(msg: Message, bot: Bot):
    wait = await msg.answer("🔍 Rasmdan tikerlar o'qilmoqda...")

    file_id = msg.photo[-1].file_id if msg.photo else msg.document.file_id
    buf = io.BytesIO()
    await bot.download(file_id, destination=buf)

    try:
        found = await asyncio.to_thread(
            ocr.extract_tickers, buf.getvalue(), MAX_TICKERS_PER_MESSAGE
        )
    except Exception as exc:
        await wait.edit_text(
            f"OCR ishlamadi: {exc}\n\nTesseract o'rnatilganini tekshiring."
        )
        return

    # Tiker ro'yxati yuklanmagan bo'lsa — har birini yfinance orqali tekshiramiz
    if not ocr.load_universe() and found:
        checked = []
        for tk in found:
            if await asyncio.to_thread(ticker_exists, tk):
                checked.append(tk)
        found = checked

    await wait.delete()

    if not found:
        await msg.answer(
            "Rasmdan tiker topa olmadim 😕\n"
            "Tikerni qo'lda yozib yuboring, masalan: <code>AAPL</code>"
        )
        return

    await msg.answer(f"📷 Topildi: <b>{', '.join(found)}</b>")
    await process_and_reply(msg, found)


@dp.message(F.text)
async def handle_text(msg: Message):
    raw = msg.text.upper().replace(",", " ").replace("$", " ")
    tickers = [t for t in TICKER_INPUT_RE.findall(raw) if len(t) >= 1]
    tickers = list(dict.fromkeys(tickers))
    await process_and_reply(msg, tickers)


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini to'ldiring.")
    bot = Bot(token=BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    log.info("Bot ishga tushdi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
