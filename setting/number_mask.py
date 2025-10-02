import sqlite3
import json

# Configdan DB nomini olish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

# JSON ma'lumot
# data = [
#     {"id": 1, "sim_esim" : "e_sim", "mask": "*ABABA*", "category": "Oddiy", "category_id": 1},
#     {"id": 2, "sim_esim" : "e_sim", "mask": "*ABA*AB", "category": "Oddiy", "category_id": 1},
#     {"id": 3, "sim_esim" : "e_sim", "mask": "*0B00*B", "category": "Bronze", "category_id": 2},
#     {"id": 4, "sim_esim" : "e_sim", "mask": "0*B0B0*", "category": "Bronze", "category_id": 2},
#     {"id": 5, "sim_esim" : "e_sim", "mask": "B*BBB*B", "category": "Bronze", "category_id": 2},
#     {"id": 6, "sim_esim" : "e_sim", "mask": "*0B0B0*", "category": "Bronze", "category_id": 2},
#     {"id": 7, "sim_esim" : "e_sim", "mask": "*0B0*0B", "category": "Bronze", "category_id": 2},
#     {"id": 8, "sim_esim" : "e_sim", "mask": "0*B0B0*", "category": "Bronze", "category_id": 2},
#     {"id": 9, "sim_esim" : "e_sim", "mask": "AB0A0B0", "category": "Bronze", "category_id": 2},
#     {"id": 10, "sim_esim" : "e_sim", "mask": "AB0B0A0", "category": "Bronze", "category_id": 2},
#     {"id": 10, "sim_esim" : "e_sim", "mask": "***ABAB", "category": "Silver", "category_id": 3},
#     {"id": 32, "sim_esim" : "e_sim", "mask": "*BABBBA", "category": "Silver", "category_id": 3},
#     {"id": 33, "sim_esim" : "e_sim", "mask": "BB**BBB", "category": "Silver", "category_id": 3},
#     {"id": 34, "sim_esim" : "e_sim", "mask": "*ABABBB", "category": "Silver", "category_id": 3},
#     {"id": 9, "sim_esim" : "e_sim", "mask": "***ABAB", "category": "Gold", "category_id": 4},
#     {"id": 12, "sim_esim" : "e_sim", "mask": "*ABABBA", "category": "Gold", "category_id": 4},
#     {"id": 13, "sim_esim" : "e_sim", "mask": "*ABBAAB", "category": "Gold", "category_id": 4},
#     {"id": 14, "sim_esim" : "e_sim", "mask": "00*0BBB", "category": "Gold", "category_id": 4},
#     {"id": 15, "sim_esim" : "e_sim", "mask": "*00B00B", "category": "Gold", "category_id": 4},
#     {"id": 16, "sim_esim" : "e_sim", "mask": "0*0B00B", "category": "Gold", "category_id": 4},
#     {"id": 17, "sim_esim" : "e_sim", "mask": "B00B00B", "category": "Gold", "category_id": 4},
#     {"id": 18, "sim_esim" : "e_sim", "mask": "B000BB0", "category": "Gold", "category_id": 4},
#     {"id": 19, "sim_esim" : "e_sim", "mask": "*BB00BB", "category": "Gold", "category_id": 4},
#     {"id": 20, "sim_esim" : "e_sim", "mask": "*BBCCDD", "category": "Gold", "category_id": 4},
#     {"id": 21, "sim_esim" : "e_sim", "mask": "A00ABBA", "category": "Gold", "category_id": 4},
#     {"id": 22, "sim_esim" : "e_sim", "mask": "A00BAAB", "category": "Gold", "category_id": 4},
#     {"id": 25, "sim_esim" : "sim", "mask": "BB*BBB*", "category": "Platinum", "category_id": 5},
#     {"id": 26, "sim_esim" : "sim", "mask": "*BBBBB*", "category": "Platinum", "category_id": 5},
#     {"id": 27, "sim_esim" : "sim", "mask": "*B0B000", "category": "Platinum", "category_id": 5},
#     {"id": 28, "sim_esim" : "sim", "mask": "*B00B00", "category": "Platinum", "category_id": 5},
#     {"id": 29, "sim_esim" : "sim", "mask": "*B000B0", "category": "Platinum", "category_id": 5},
#     {"id": 30, "sim_esim" : "sim", "mask": "BBBBB**", "category": "Platinum", "category_id": 5},
#     {"id": 31, "sim_esim" : "sim", "mask": "*0*000B", "category": "Platinum", "category_id": 5},
#     {"id": 36, "sim_esim" : "sim", "mask": "Platinum10", "category": "Platinum", "category_id": 6},
#     {"id": 37, "sim_esim" : "sim", "mask": "Platinum20", "category": "Platinum", "category_id": 7},
#     {"id": 38, "sim_esim" : "sim", "mask": "Platinum30", "category": "Platinum", "category_id": 8}
# ]
data = [
    {"sim_esim": "e_sim", "mask": "*ABABA*", "category": "Oddiy", "category_id": 1},
    {"sim_esim": "e_sim", "mask": "*ABA*AB", "category": "Oddiy", "category_id": 1},

    {"sim_esim": "e_sim", "mask": "*0B00*B", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "0*B0B0*", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "B*BBB*B", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "*0B0B0*", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "*0B0*0B", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "0*B0B0*", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "AB0A0B0", "category": "Bronze", "category_id": 2},
    {"sim_esim": "e_sim", "mask": "AB0B0A0", "category": "Bronze", "category_id": 2},

    {"sim_esim": "e_sim", "mask": "***ABAB", "category": "Silver", "category_id": 3},
    {"sim_esim": "e_sim", "mask": "*BABBBA", "category": "Silver", "category_id": 3},
    {"sim_esim": "e_sim", "mask": "BB**BBB", "category": "Silver", "category_id": 3},
    {"sim_esim": "e_sim", "mask": "*ABABBB", "category": "Silver", "category_id": 3},

    {"sim_esim": "e_sim", "mask": "***ABAB", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "*ABABBA", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "*ABBAAB", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "00*0BBB", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "*00B00B", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "0*0B00B", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "B00B00B", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "B000BB0", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "*BB00BB", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "*BBCCDD", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "A00ABBA", "category": "Gold", "category_id": 4},
    {"sim_esim": "e_sim", "mask": "A00BAAB", "category": "Gold", "category_id": 4},

    {"sim_esim": "sim", "mask": "BB*BBB*", "category": "Platinum", "category_id": 5},
    {"sim_esim": "sim", "mask": "*BBBBB*", "category": "Platinum", "category_id": 5},
    {"sim_esim": "sim", "mask": "*B0B000", "category": "Platinum", "category_id": 5},
    {"sim_esim": "sim", "mask": "*B00B00", "category": "Platinum", "category_id": 5},
    {"sim_esim": "sim", "mask": "*B000B0", "category": "Platinum", "category_id": 5},
    {"sim_esim": "sim", "mask": "BBBBB**", "category": "Platinum", "category_id": 5},
    {"sim_esim": "sim", "mask": "*0*000B", "category": "Platinum", "category_id": 5},

    {"sim_esim": "sim", "mask": "Platinum10", "category": "Platinum", "category_id": 6},
    {"sim_esim": "sim", "mask": "Platinum20", "category": "Platinum", "category_id": 7},
    {"sim_esim": "sim", "mask": "Platinum30", "category": "Platinum", "category_id": 8}
]

# SQLite ulanish
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()


# Ma'lumotlarni yozish
# for row in data:
#     cursor.execute("""
#         INSERT INTO number_mask (id, sim_esim, mask, category, category_id)
#         VALUES (?, ?, ?, ?, ?)
#         ON CONFLICT(id) DO UPDATE SET 
#             sim_esim=excluded.sim_esim,
#             mask=excluded.mask,
#             category=excluded.category,
#             category_id=excluded.category_id
#     """, (row["id"], row["sim_esim"], row["mask"], row["category"], row["category_id"]))
for row in data:
    cursor.execute("""
        INSERT INTO number_mask (sim_esim, mask, category, category_id)
        VALUES (?, ?, ?, ?)
    """, (row["sim_esim"], row["mask"], row["category"], row["category_id"]))

conn.commit()
cursor.close()
conn.close()
print("Ma'lumotlar muvaffaqiyatli yozildi.")    
