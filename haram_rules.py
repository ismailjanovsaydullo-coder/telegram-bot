"""Taqiqlangan faoliyat sohalari (sifat skrining) uchun qoidalar bazasi.

Uch qatlam:
  1. INDUSTRY_BLACKLIST  - yfinance "industry" maydoni bilan aniq moslik
  2. SECTOR_BLACKLIST    - butun sektor taqiqlangan
  3. SUMMARY_KEYWORDS    - kompaniya tavsifidagi kalit so'zlar
"""

# --- Sektor darajasida taqiqlangan ---
SECTOR_BLACKLIST = {
    "financial services": "An'anaviy moliya sektori (foizga asoslangan)",
}

# --- Soha (industry) darajasida taqiqlangan ---
# Kalit: yfinance industry nomi (kichik harflarda)
INDUSTRY_BLACKLIST = {
    # Bank va kredit
    "banks - diversified": "An'anaviy bank",
    "banks - regional": "An'anaviy bank",
    "banks": "An'anaviy bank",
    "mortgage finance": "Foizli ipoteka krediti",
    "credit services": "Foizli kredit xizmatlari",
    "capital markets": "An'anaviy kapital bozori faoliyati",
    "financial conglomerates": "An'anaviy moliyaviy konglomerat",
    "financial data & stock exchanges": "An'anaviy moliya infratuzilmasi",
    "asset management": "An'anaviy aktivlarni boshqarish",
    "shell companies": "Faoliyati noaniq (blank-check)",
    # Sug'urta
    "insurance - diversified": "An'anaviy sug'urta (g'arar va riba)",
    "insurance - life": "An'anaviy hayot sug'urtasi",
    "insurance - property & casualty": "An'anaviy mol-mulk sug'urtasi",
    "insurance - reinsurance": "An'anaviy qayta sug'urta",
    "insurance - specialty": "An'anaviy sug'urta",
    "insurance brokers": "Sug'urta brokerligi",
    # Ichimlik va tamaki
    "beverages - wineries & distilleries": "Alkogol ishlab chiqarish",
    "beverages - brewers": "Pivo ishlab chiqarish",
    "tobacco": "Tamaki mahsulotlari",
    # Qimor va ko'ngilochar
    "gambling": "Qimor",
    "resorts & casinos": "Kazino va qimor",
    "leisure": "Ko'ngilochar (tekshirish talab etiladi)",
    # Boshqa
    "reit - mortgage": "Foizli ipoteka REIT",
    "reit - hotel & motel": "Mehmonxona REIT (alkogol/ko'ngilochar daromadi)",
}

# --- Ixtiloflі sohalar: to'g'ridan-to'g'ri harom emas, SHUBHALI ---
INDUSTRY_DOUBTFUL = {
    "aerospace & defense": "Mudofaa/qurol sanoati - olimlar ixtilof qilgan",
    "entertainment": "Ko'ngilochar kontent - mazmuni tekshirilsin",
    "broadcasting": "Media kontenti tekshirilsin",
    "electronic gaming & multimedia": "O'yin kontenti tekshirilsin",
    "lodging": "Mehmonxona - alkogol/ko'ngilochar daromadi bo'lishi mumkin",
    "restaurants": "Restoran - cho'chqa/alkogol menyusi tekshirilsin",
    "drug manufacturers - specialty & generic": "Ba'zi mahsulotlar tekshirilsin",
    "airlines": "Bortdagi alkogol xizmati - odatda 5% dan kam",
}

# --- Kompaniya tavsifidagi kalit so'zlar (longBusinessSummary) ---
# (kalit so'z, sabab)
SUMMARY_KEYWORDS_HARAM = [
    ("alcoholic beverage", "Alkogolli ichimlik"),
    ("alcoholic drinks", "Alkogolli ichimlik"),
    ("distilled spirits", "Spirtli ichimlik"),
    ("beer, wine", "Alkogol savdosi"),
    ("wine and spirits", "Alkogol savdosi"),
    ("brewery", "Pivo zavodi"),
    ("breweries", "Pivo zavodi"),
    ("distillery", "Aroq zavodi"),
    ("cigarette", "Sigaret"),
    ("cigar ", "Tamaki"),
    ("tobacco product", "Tamaki mahsuloti"),
    ("vaping", "Nikotin mahsuloti"),
    ("pork", "Cho'chqa go'shti"),
    ("swine", "Cho'chqachilik"),
    ("casino", "Kazino"),
    ("gaming and betting", "Tikish/qimor"),
    ("sports betting", "Sport tikish"),
    ("lottery", "Lotereya"),
    ("adult entertainment", "Kattalar kontenti"),
    ("pornograph", "Kattalar kontenti"),
    ("interest income from loans", "Foizli kredit daromadi"),
    ("consumer lending", "Foizli iste'mol krediti"),
    ("payday loan", "Foizli mikrokredit"),
    ("conventional insurance", "An'anaviy sug'urta"),
]

SUMMARY_KEYWORDS_DOUBTFUL = [
    ("cannabis", "Nasha mahsulotlari"),
    ("marijuana", "Nasha mahsulotlari"),
    ("defense contractor", "Mudofaa pudratchisi"),
    ("weapons systems", "Qurol tizimlari"),
    ("munitions", "O'q-dorilar"),
    ("nightclub", "Tungi klub"),
]


def check_sector(sector: str) -> tuple[str, str] | None:
    """Sektorni tekshiradi. -> (holat, sabab) yoki None"""
    if not sector:
        return None
    s = sector.strip().lower()
    if s in SECTOR_BLACKLIST:
        return ("haram", SECTOR_BLACKLIST[s])
    return None


def check_industry(industry: str) -> tuple[str, str] | None:
    """Sohani tekshiradi. -> (holat, sabab) yoki None"""
    if not industry:
        return None
    i = industry.strip().lower()
    if i in INDUSTRY_BLACKLIST:
        return ("haram", INDUSTRY_BLACKLIST[i])
    if i in INDUSTRY_DOUBTFUL:
        return ("doubtful", INDUSTRY_DOUBTFUL[i])
    return None


def check_summary(summary: str) -> tuple[str, str] | None:
    """Kompaniya tavsifini kalit so'zlar bo'yicha tekshiradi."""
    if not summary:
        return None
    text = summary.lower()
    for kw, reason in SUMMARY_KEYWORDS_HARAM:
        if kw in text:
            return ("haram", f"{reason} (tavsifda: «{kw.strip()}»)")
    for kw, reason in SUMMARY_KEYWORDS_DOUBTFUL:
        if kw in text:
            return ("doubtful", f"{reason} (tavsifda: «{kw.strip()}»)")
    return None
