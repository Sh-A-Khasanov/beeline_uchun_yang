import requests
import sqlite3
import json

# Config faylini o'qish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
url_info_link = config["url_info"][0]["link"]  # https://nomer.beeline.uz/

db_path = config["db_name"]  # "database/beeline.db"

# SQLite bazaga ulanish
conn = sqlite3.connect(db_path)
cursor = conn.cursor()



# APIga so'rov yuborish
url = f"{url_info_link}msapi/web/rms/phone-numbers/regions"
response = requests.get(url)
data = response.json()

# Malumotlarni bazaga yozish
for region in data:
    cursor.execute("""
    INSERT OR REPLACE INTO regions (id, nameRu, nameUz, createdAt, updatedAt, createdBy, modifiedBy)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        region["id"],
        region["nameRu"],
        region["nameUz"],
        region["createdAt"],
        region["updatedAt"],
        region["createdBy"],
        region["modifiedBy"]
    ))

conn.commit()
conn.close()

print("Regions bazaga yozildi!")
