import json
import sqlite3

# regions_id va warehouse_code ro‘yxatlar
region_codes = {
    "Buxoro": [110, 1211, 109, 108, 107, 3658, 905, 1070]
    # "Andijon": [184, 1205, 183, 182, 181, 3438, 906, 1061],
    # "Surxondaryo": [134, 1210, 133, 132, 131, 3808, 909, 1063],
    # "Sirdaryo": [168, 1202, 167, 166, 165, 3208, 915, 1062],
    # "Qo'qon": [172, 1204, 171, 170, 169, 3338, 903, 1064],
    # "Namangan": [180, 1206, 179, 178, 177, 3358, 904, 1065],
    # "Jizzax": [163, 1208, 162, 161, 160, 3408, 914, 1066],
    # "Xorazm": [44, 1214, 43, 42, 41, 3858, 912, 1060],
    # "Farg‘ona": [176, 1203, 175, 174, 173, 3308, 902, 1069],
    # "Samarqand": [159, 1207, 158, 151, 140, 3458, 907, 1068],
    # "Toshkent shahri": [188, 1201, 187, 186, 185, 3008, 1042, 901],
    # "Qoraqalpog‘iston Res": [48, 1213, 47, 46, 45, 3758, 913, 1071],
    # "Qashqadaryo": [139, 1209, 138, 137, 136, 3558, 908, 1067],
    # "Navoiy": [102, 1212, 101, 50, 49, 3608, 911, 1072]
}

# Kategoriyalar va ID lar
warehouse_categories = {
    "Oddiy": 1,
    "Bronze": 2,
    "Silver": 3,
    "Gold": 4,
    "Platinum": 5,
    "Platinum10": 6,
    "Platinum20": 7,
    "Platinum30": 8
}

# regions_id lar
regions_ids = {
    "Buxoro": 15,
    "Andijon": 7,
    "Surxondaryo": 8,
    "Sirdaryo": 9,
    "Qo'qon": 10,
    "Namangan": 11,
    "Jizzax": 12,
    "Xorazm": 13,
    "Farg‘ona": 14,
    "Samarqand": 16,
    "Toshkent shahri": 17,
    "Qoraqalpog‘iston Res": 18,
    "Qashqadaryo": 19,
    "Navoiy": 20
}

# Umumiy tuzilma
regions = {}
for region, codes in region_codes.items():
    regions[region] = {
        "regions_id": regions_ids.get(region),
        "warehouses": {}
    }
    for idx, (category, cat_id) in enumerate(warehouse_categories.items()):
        if idx < len(codes):
            regions[region]["warehouses"][category] = {
                "category_id": cat_id,
                "code": codes[idx]
            }

# 1) JSON faylga yozish
with open("config/regions.json", "w", encoding="utf-8") as f:
    json.dump(regions, f, ensure_ascii=False, indent=4)

# 2) SQLite bazaga yozish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

for region, data in regions.items():
    for category, info in data["warehouses"].items():
        cur.execute(
    "INSERT OR IGNORE INTO warehouses (regions_id, regions_name, category_id, category, code) VALUES (?, ?, ?, ?, ?)",
    (data["regions_id"], region, info["category_id"], category, info["code"])
)


conn.commit()
conn.close()

print("Tayyor: config/regions.json va warehouses jadvali yaratildi.")






























































# import json
# import sqlite3

# # regions_id va warehouse_code siz bergan ro‘yxatlar
# region_codes = {
#     "Andijon": [184, 1205, 183, 182, 181, 3438, 906, 1061],
#     "Surxondaryo": [134, 1210, 133, 132, 131, 3808, 909, 1063],
#     "Sirdaryo": [168, 1202, 167, 166, 165, 3208, 915, 1062],
#     "Qo'qon": [172, 1204, 171, 170, 169, 3338, 903, 1064],
#     "Namangan": [180, 1206, 179, 178, 177, 3358, 904, 1065],
#     "Jizzax": [163, 1208, 162, 161, 160, 3408, 914, 1066],
#     "Xorazm": [44, 1214, 43, 42, 41, 3858, 912, 1060],
#     "Farg‘ona": [176, 1203, 175, 174, 173, 3308, 902, 1069],
#     "Buxoro": [110, 1211, 109, 108, 107, 3658, 905, 1070],
#     "Samarqand": [159, 1207, 158, 151, 140, 3458, 907, 1068],
#     "Toshkent shahri": [188, 1201, 187, 186, 185, 3008, 1042, 901],
#     "Qoraqalpog‘iston Res": [48, 1213, 47, 46, 45, 3758, 913, 1071],
#     "Qashqadaryo": [139, 1209, 138, 137, 136, 3558, 908, 1067],
#     "Navoiy": [102, 1212, 101, 50, 49, 3608, 911, 1072]
# }

# warehouse_categories = [
#     "Oddiy", "Bronze", "Silver", "Gold", "Platinum",
#     "Platinum 10", "Platinum 20", "Platinum 30"
# ]

# warehouse_categories = {
#     "Oddiy": 1,
#     "Bronze": 2,
#     "Silver": 3,
#     "Gold": 4,
#     "Platinum": 5,
#     "Platinum10": 6,
#     "Platinum20": 7,
#     "Platinum30": 8
# }

# regions_ids = {
#     "Andijon": 7,
#     "Surxondaryo": 8,
#     "Sirdaryo": 9,
#     "Qo'qon": 10,
#     "Namangan": 11,
#     "Jizzax": 12,
#     "Xorazm": 13,
#     "Farg‘ona": 14,
#     "Buxoro": 15,
#     "Samarqand": 16,
#     "Toshkent shahri": 17,
#     "Qoraqalpog‘iston Res": 18,
#     "Qashqadaryo": 19,
#     "Navoiy": 20
# }

# # Umumiy tuzilma yaratish
# regions = {}
# for region, codes in region_codes.items():
#     regions[region] = {
#         "regions_id": regions_ids.get(region),
#         "warehouses": {}
#     }
#     for idx, category in enumerate(warehouse_categories):
#         if idx < len(codes):
#             regions[region]["warehouses"][category] = codes[idx]

# # 1) JSON faylga yozish
# with open("regions.json", "w", encoding="utf-8") as f:
#     json.dump(regions, f, ensure_ascii=False, indent=4)

# # 2) SQLite bazaga yozish


# # config.json o‘qish
# with open("config/config.json", "r", encoding="utf-8") as f:
#     config = json.load(f)

# DB_NAME = config["db_name"]
# conn = sqlite3.connect(DB_NAME)
# cur = conn.cursor()

# cur.execute("""
# CREATE TABLE IF NOT EXISTS warehouses (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     region TEXT,
#     regions_id INTEGER,
#     category TEXT,
#     code INTEGER
# )
# """)

# for region, data in regions.items():
#     for category, code in data["warehouses"].items():
#         cur.execute(
#             "INSERT INTO warehouses (region, regions_id, category, code) VALUES (?, ?, ?, ?)",
#             (region, data["regions_id"], category, code)
#         )

# conn.commit()
# conn.close()

# print("Tayyor: regions.json va warehouses.db yaratildi.")





































