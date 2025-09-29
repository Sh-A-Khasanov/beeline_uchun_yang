import sqlite3
import json

# Configdan DB nomini olish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

# JSON ma'lumot
data = [
    {"id": 1, "mask": "*0B00*B", "category": "Bronze", "category_id": 2},
    {"id": 2, "mask": "0*B0B0*", "category": "Bronze", "category_id": 2},
    {"id": 3, "mask": "B*BBB*B", "category": "Bronze", "category_id": 2},
    {"id": 4, "mask": "*0B0B0*", "category": "Bronze", "category_id": 2},
    {"id": 5, "mask": "*0B0*0B", "category": "Bronze", "category_id": 2},
    {"id": 6, "mask": "0*B0B0*", "category": "Bronze", "category_id": 2},
    {"id": 7, "mask": "AB0A0B0", "category": "Bronze", "category_id": 2},
    {"id": 8, "mask": "AB0B0A0", "category": "Bronze", "category_id": 2},
    {"id": 9, "mask": "***ABAB", "category": "Gold", "category_id": 4},
    {"id": 10, "mask": "***ABAB", "category": "Silver", "category_id": 3},
    {"id": 12, "mask": "*ABABBA", "category": "Gold", "category_id": 4},
    {"id": 13, "mask": "*ABBAAB", "category": "Gold", "category_id": 4},
    {"id": 14, "mask": "00*0BBB", "category": "Gold", "category_id": 4},
    {"id": 15, "mask": "*00B00B", "category": "Gold", "category_id": 4},
    {"id": 16, "mask": "0*0B00B", "category": "Gold", "category_id": 4},
    {"id": 17, "mask": "B00B00B", "category": "Gold", "category_id": 4},
    {"id": 18, "mask": "B000BB0", "category": "Gold", "category_id": 4},
    {"id": 19, "mask": "*BB00BB", "category": "Gold", "category_id": 4},
    {"id": 20, "mask": "*BBCCDD", "category": "Gold", "category_id": 4},
    {"id": 21, "mask": "A00ABBA", "category": "Gold", "category_id": 4},
    {"id": 22, "mask": "A00BAAB", "category": "Gold", "category_id": 4},
    {"id": 23, "mask": "*ABABA*", "category": "Oddiy", "category_id": 1},
    {"id": 24, "mask": "*ABA*AB", "category": "Oddiy", "category_id": 1},
    {"id": 25, "mask": "BB*BBB*", "category": "Platinum", "category_id": 5},
    {"id": 26, "mask": "*BBBBB*", "category": "Platinum", "category_id": 5},
    {"id": 27, "mask": "*B0B000", "category": "Platinum", "category_id": 5},
    {"id": 28, "mask": "*B00B00", "category": "Platinum", "category_id": 5},
    {"id": 29, "mask": "*B000B0", "category": "Platinum", "category_id": 5},
    {"id": 30, "mask": "BBBBB**", "category": "Platinum", "category_id": 5},
    {"id": 31, "mask": "*0*000B", "category": "Platinum", "category_id": 5},
    {"id": 32, "mask": "*BABBBA", "category": "Silver", "category_id": 3},
    {"id": 33, "mask": "BB**BBB", "category": "Silver", "category_id": 3},
    {"id": 34, "mask": "*ABABBB", "category": "Silver", "category_id": 3},
    {"id": 36, "mask": "Platinum10", "category": "Platinum", "category_id": 10},
    {"id": 37, "mask": "Platinum20", "category": "Platinum", "category_id": 20},
    {"id": 38, "mask": "Platinum30", "category": "Platinum", "category_id": 30}
]

# SQLite ulanish
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()


# Ma'lumotlarni yozish
for row in data:
    cursor.execute("""
        INSERT INTO number_mask (id, mask, category, category_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET 
            mask=excluded.mask,
            category=excluded.category,
            category_id=excluded.category_id
    """, (row["id"], row["mask"], row["category"], row["category_id"]))

conn.commit()
cursor.close()
conn.close()
print("Ma'lumotlar muvaffaqiyatli yozildi.")    
