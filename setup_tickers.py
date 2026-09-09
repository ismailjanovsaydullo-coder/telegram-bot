"""Haqiqiy tikerlar ro'yxatini yuklab olish (bir marta ishga tushiriladi).
    python setup_tickers.py
"""
import ocr

if __name__ == "__main__":
    print("NASDAQ Trader'dan tikerlar yuklanmoqda...")
    n = ocr.download_universe()
    print(f"Tayyor: {n} ta tiker saqlandi -> tickers.txt")
