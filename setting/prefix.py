import pandas as pd
import sqlite3
import json

# ---------- config.json o‘qish ----------
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

# ---------- Excelni o‘qish ----------
df = pd.read_excel("prefix.xlsx")

# ---------- Dict yasash (interval ochib) ----------
prefix_dict = {}
for _, row in df.iterrows():
    regions_id = int(row["regions_id"])
    regions_name = row["regions_name"]
    n_Code = str(row["n_Code"])
    ate_val = str(row["ATE"]).strip()

    if regions_name not in prefix_dict:
        prefix_dict[regions_name] = {}

    if n_Code not in prefix_dict[regions_name]:
        # har bir n_Code uchun { "regions_id": ..., "ates": [...] }
        prefix_dict[regions_name][n_Code] = {"regions_id": regions_id, "ates": []}

    # Interval bo‘lsa
    if "-" in ate_val:
        parts = ate_val.split("-")
        numbers = [int(x) for x in parts if x.isdigit()]
        if len(numbers) >= 2:
            start, end = numbers[0], numbers[-1]
            for i in range(start, end + 1):
                full_ate = f"{n_Code}{i:03d}"
                prefix_dict[regions_name][n_Code]["ates"].append(full_ate)
        else:
            full_ate = f"{n_Code}{ate_val}"
            prefix_dict[regions_name][n_Code]["ates"].append(full_ate)
    else:
        try:
            full_ate = f"{n_Code}{int(ate_val):03d}"
        except ValueError:
            full_ate = f"{n_Code}{ate_val}"
        prefix_dict[regions_name][n_Code]["ates"].append(full_ate)

print("Dict ko‘rinishi:")
print(prefix_dict)

# ---------- Bazaga ulanish ----------
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Jadvalni yaratish (agar bo‘lmasa)
# Jadvalni yaratish (agar bo‘lmasa)
cursor.execute("""
CREATE TABLE IF NOT EXISTS prefix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regions_id INTEGER,
    regions_name TEXT,
    n_Code INTEGER,
    ate INTEGER
)
""")

# Eski yozuvlarni tozalash
cursor.execute("DELETE FROM prefix")

# Dictni bazaga yozish
# Bazaga yozish
for regions_name, n_Codes in prefix_dict.items():
    for n_Code, data in n_Codes.items():
        regions_id = data["regions_id"]
        for ate in data["ates"]:
            cursor.execute(
                "INSERT INTO prefix (regions_id, regions_name, n_Code, ate) VALUES (?, ?, ?, ?)",
                (regions_id, regions_name, n_Code, ate)
            )


conn.commit()
cursor.close()
conn.close()

print("✅ prefix.xlsx dan ma’lumotlar dict qilindi va interval ochilib prefix jadvaliga yozildi.")
