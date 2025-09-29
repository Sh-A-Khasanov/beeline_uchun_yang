import requests
import sqlite3
import json

# Config faylini o'qish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

db_path = config["db_name"]
url_info_link = config["url_info"][0]["link"]

# SQLite bazaga ulanish
conn = sqlite3.connect(db_path)
cursor = conn.cursor()


# Regions jadvalidan barcha idlarni olish
cursor.execute("SELECT id FROM regions")
region_ids = [row[0] for row in cursor.fetchall()]

# Har bir region_id uchun APIga so'rov yuborish va ma’lumotlarni yozish
for region_id in region_ids:
    url = f"{url_info_link}msapi/web/rms/phone-numbers/warehouses?region_id={region_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        warehouses = response.json()
        for wh in warehouses:
            # regions arrayni alohida ustunlarga ajratish
            regions_ids = ",".join(str(r.get("id")) for r in wh.get("regions", []))
            regions_names = ",".join(r.get("name") for r in wh.get("regions", []))
            
            cursor.execute("""
            INSERT OR REPLACE INTO warehouses (
                id, nameRu, nameUz, code, price,
                partialPaymentService, partialPaymentServiceId,
                region, regionId, service, serviceId,
                regions_id, regions_name,
                conditionOfUse, conditionOfUseId, createdAt, updatedAt,
                createdBy, createdById, modifiedBy, modifiedById,
                active, partialPayment, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wh.get("id"),
                wh.get("nameRu"),
                wh.get("nameUz"),
                wh.get("code"),
                wh.get("price"),
                wh.get("partialPaymentService"),
                wh.get("partialPaymentServiceId"),
                wh.get("region"),
                wh.get("regionId"),
                wh.get("service"),
                wh.get("serviceId"),
                regions_ids,
                regions_names,
                wh.get("conditionOfUse"),
                wh.get("conditionOfUseId"),
                wh.get("createdAt"),
                wh.get("updatedAt"),
                wh.get("createdBy"),
                wh.get("createdById"),
                wh.get("modifiedBy"),
                wh.get("modifiedById"),
                wh.get("active"),
                wh.get("partialPayment"),
                wh.get("description")
            ))
    else:
        print(f"Region {region_id} uchun xatolik: {response.status_code}")

conn.commit()
conn.close()
print("Warehouses bazaga to‘liq yozildi, regions alohida ustunlarda!")
