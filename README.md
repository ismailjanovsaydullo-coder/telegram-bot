# 🕌 Halol Aksiya Skrineri — Telegram Bot

Amerika aksiyalarini **AAOIFI Shari'ah Standard No. 21** mezonlari bo'yicha
tekshiruvchi Telegram bot. Tiker yozib yoki broker skrinshotini tashlab
tekshirish mumkin.

---

## 1. O'rnatish

### 1.1 Python paketlari

```bash
cd halal_bot
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 1.2 Tesseract OCR (rasm o'qish uchun)

**Windows:** https://github.com/UB-Mannheim/tesseract/wiki dan o'rnating.
So'ng `.env` faylida yo'lini ko'rsating:
```
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 1.3 Bot tokeni

Telegramda [@BotFather](https://t.me/BotFather) ga `/newbot` yozib token oling.

```bash
cp .env.example .env
```
`.env` faylini oching va tokenni qo'ying:
```
BOT_TOKEN=8123456789:AAH...
```

### 1.4 Tikerlar ro'yxatini yuklash (MUHIM)

```bash
python setup_tickers.py
```

Bu ~10 000 ta haqiqiy tikerni `tickers.txt` ga saqlaydi. **OCR aniqligi shu
faylga bog'liq** — usiz bot rasmdan "OPEN", "VOL" kabi so'zlarni tiker deb
o'ylashi mumkin.

### 1.5 Ishga tushirish

```bash
python bot.py
```

---

## 2. Ishlatish

| Kiritish | Natija |
|---|---|
| `AAPL` | Bitta aksiya hisoboti |
| `AAPL MSFT JPM` | Uchtasi ketma-ket |
| 📷 Skrinshot | Rasmdan tikerlar o'qib tekshiriladi |
| `/help` | Cheklovlar va tushuntirish |

---

## 3. Skrining mantiqi

### 1-bosqich — Faoliyat sohasi (sifat)

Kompaniyaning asosiy biznesi taqiqlangan bo'lsa → darhol **HAROM**,
nisbatlar hisoblanmaydi.

Tekshiriladi: sektor → soha (industry) → kompaniya tavsifi (kalit so'zlar).

Taqiqlangan: bank, sug'urta, kredit, alkogol, tamaki, cho'chqa, qimor,
kazino, kattalar kontenti, ipoteka REIT.

Ixtilofli (→ **SHUBHALI**): mudofaa, ko'ngilochar, mehmonxona, restoran,
o'yin sanoati.

### 2-bosqich — Moliyaviy nisbatlar (miqdoriy)

| Nisbat | Chegara |
|---|---|
| Foizli qarz / **Bozor kapitalizatsiyasi** | < 30% |
| Naqd + foizli investitsiyalar / **Bozor kapitalizatsiyasi** | < 30% |
| Foizli (taqiqlangan) daromad / Umumiy daromad | < 5% |

> AAOIFI maxrajda **bozor kapitalizatsiyasini** ishlatadi (S&P/Dow Jones
> esa umumiy aktivlarni). Shuning uchun natija narx o'zgarishi bilan
> o'zgaradi.

### Natija turlari

- ✅ **HALOL** — barcha mezonlardan o'tdi
- ⛔️ **HAROM** — faoliyat yoki nisbat mezoni buzilgan
- ⚠️ **SHUBHALI** — ma'lumot yetarli emas yoki soha ixtilofli

### Tozalash (tathir)

Dividend to'lovchi kompaniyalar uchun:
`sadaqa = dividend × (foizli daromad ulushi)`

---

## 4. Cheklovlar — buni bilib qo'ying

1. **"Real vaqt" qisman.** Narx va bozor kapitalizatsiyasi har so'rovda
   yangilanadi. Lekin qarz va naqd choraklik hisobotdan olinadi — 3 oyda
   bir marta yangilanadi. Ya'ni nisbat real vaqtda **qayta hisoblanadi**,
   ammo balans ma'lumoti eski.

2. **"Taqiqlangan daromad < 5%" — taxminiy.** Kompaniyaning aniq segment
   daromadi bepul manbalarda yo'q. Uning o'rniga hisobotdagi
   `Interest Income` qatori proksi sifatida ishlatiladi. Bu AAOIFI
   talabining to'liq bajarilishi emas — yaqinlashtirilgan baho.

3. **Ma'lumot yo'q = HALOL emas.** Ma'lumot yetishmasa bot **SHUBHALI**
   deydi. Bu ataylab shunday — noaniqlikni halol deb ko'rsatish xato bo'lardi.

4. **yfinance norasmiy.** Yahoo API'sini o'zgartirsa buzilishi mumkin.
   Shunda `pip install -U yfinance` qiling.

5. **Bu fatvo emas.** Bot faqat ochiq raqamlarni AAOIFI formulasiga soladi.

---

## 5. Sozlash

`config.py` faylida:

```python
DEBT_RATIO_MAX    = 0.30   # qarz chegarasi
CASH_RATIO_MAX    = 0.30   # naqd chegarasi
HARAM_INCOME_MAX  = 0.05   # daromad chegarasi
DEFENSE_IS_HARAM  = False  # mudofaa sohasi harommi?
CACHE_TTL_HOURS   = 24     # kesh muddati
```

`haram_rules.py` faylida sohalar va kalit so'zlar ro'yxatini kengaytirish
mumkin — bu bot "miyasi", vaqt o'tgani sari to'ldirib borasiz.

---

## 6. Fayllar

```
halal_bot/
├── bot.py            # Telegram handlerlar va hisobot formati
├── screener.py       # AAOIFI skrining mantiqi
├── data_source.py    # yfinance + SQLite kesh
├── haram_rules.py    # taqiqlangan sohalar bazasi
├── ocr.py            # rasmdan tiker o'qish
├── config.py         # sozlamalar
├── setup_tickers.py  # tikerlar ro'yxatini yuklash
├── requirements.txt
└── .env.example
```
