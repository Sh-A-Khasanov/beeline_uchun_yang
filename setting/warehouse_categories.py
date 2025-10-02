import sqlite3
import json

# Config
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Avval jadvalni tozalash
cursor.execute("DELETE FROM warehouse_categories")

# JOIN qilib yozish (sim_esim qo‘shildi)
query = """
INSERT INTO warehouse_categories (
    warehouse_id, regions_id, regions_name, category_id, warehouse_category, code,
    category_table_id, mask, category_name, sim_esim
)
SELECT 
    w.id AS warehouse_id,
    w.regions_id,
    w.regions_name,
    w.category_id,
    w.category AS warehouse_category,
    w.code,
    k.id AS category_table_id,
    k.mask,
    k.category AS category_name,
    k.sim_esim
FROM warehouses w
JOIN number_mask k ON w.category_id = k.category_id
ORDER BY w.id
"""

cursor.execute(query)
conn.commit()
conn.close()

print("✅ warehouse_categories jadvaliga ma'lumotlar yozildi.")
