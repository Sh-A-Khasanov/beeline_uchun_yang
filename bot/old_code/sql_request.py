import sqlite3
import logging
import json

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# config.json o‘qish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

def get_kategoriya():
    try:
        # Bazaga ulanish
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Kategoriya jadvalidan barcha ma'lumotlarni olish
        cursor.execute("SELECT * FROM Kategoriya ORDER BY Tarif")
        rows = cursor.fetchall()  # Barcha satrlarni olish

        # Natijani massivga ajratish (ro'yxat sifatida)
        data = [list(row) for row in rows]


        return data  # Massivni qaytarish

    except sqlite3.Error as e:
        print("Xatolik yuz berdi:", e)

    finally:
        # Bog'lanishni yopish
        conn.close()