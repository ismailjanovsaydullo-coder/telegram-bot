"""Bot sozlamalari va AAOIFI chegaralari."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
CACHE_DB = BASE_DIR / "cache.db"
TICKERS_FILE = BASE_DIR / "tickers.txt"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# --- AAOIFI Shari'ah Standard No. 21 chegaralari ---
# Maxraj = BOZOR KAPITALIZATSIYASI (AAOIFI shunday talab qiladi).
DEBT_RATIO_MAX = 0.30          # Foizli qarz / Bozor kap.
CASH_RATIO_MAX = 0.30          # Naqd + foizli investitsiya / Bozor kap.
HARAM_INCOME_MAX = 0.05        # Taqiqlangan daromad / Umumiy daromad

# Fundamental ma'lumot keshi (soat). Narx har safar yangi olinadi.
CACHE_TTL_HOURS = 24

# Qurol/mudofaa sohasi bo'yicha olimlar ixtilof qilgan.
# True  -> harom deb belgilanadi
# False -> shubhali deb belgilanadi
DEFENSE_IS_HARAM = False

# Bir xabarda maksimal nechta tiker tekshirilsin
MAX_TICKERS_PER_MESSAGE = 10

# Tesseract yo'li (Windows uchun kerak bo'lishi mumkin)
# Masalan: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
