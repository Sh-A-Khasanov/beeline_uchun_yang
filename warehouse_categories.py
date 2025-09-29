import sqlite3
import json
# Bazaga ulanish
# 2) SQLite bazaga yozish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Avval jadvalni tozalash (takror yozilmasligi uchun)
cursor.execute("DELETE FROM warehouse_categories")

# JOIN qilib yozish
# JOIN qilib yozish
query = """
INSERT INTO warehouse_categories (
    warehouse_id, regions_id, region_name, category_id, warehouse_category, code,
    category_table_id, mask, category_name
)
SELECT 
    w.id AS warehouse_id,
    w.regions_id,
    w.region_name,
    w.category_id,
    w.category AS warehouse_category,
    w.code,
    k.id AS category_table_id,
    k.mask,
    k.category AS category_name
FROM warehouses w
JOIN number_mask_new k ON w.category_id = k.category_id
ORDER BY w.id
"""


cursor.execute(query)

conn.commit()
conn.close()

print("✅ warehouse_categories jadvaliga ma'lumotlar yozildi.")
