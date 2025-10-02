import sqlite3
import json

# config.json o‘qish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
DB_NAME = config["db_name"]


# Jadval yaratish


# Maskani "9989..." formatga aylantirish
def generate_phonenumber(Mask):
    phonenumber = "9989*"
    result = []
    if Mask in ("Gold", "Platinum", "Platinum10", "Platinum20", "Platinum30"):
        phonenumber = "9989********"
    else:
        for char in Mask:
            if char == 'A':
                result.append("{A}")
            elif char == 'B':
                result.append("{B}")
            elif char == 'C':
                result.append("{B+1}")
            elif char == 'D':
                result.append("{B+2}")
            elif char == '*':
                result.append("*")
            elif char.isdigit():
                result.append(char)
        phonenumber += "".join(result)
    return phonenumber


# Bazadan warehouse_categories jadvalidan ma’lumotlarni olish
def get_kategoriya():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                id, warehouse_id, regions_id, regions_name, category_id, 
                warehouse_category, code, category_table_id, mask, sim_esim, category_name
            FROM warehouse_categories
        """)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


# Kombinatsiyalarni yaratish va bazaga yozish
def Update_data():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM full_combinations")
    Maskalar = get_kategoriya()

    for row in Maskalar:
        (mask_id, warehouse_id, regions_id, regions_name, category_id,
         warehouse_category, code, category_table_id, mask_name, sim_esim, category_name) = row

        phonenumber = generate_phonenumber(mask_name)
        
        if '{A}' in phonenumber:
            for B in range(0, 10):
                for A in range(0, 10):
                    if A != B:
                        phonenumber1 = (
                            phonenumber
                            .replace("{A}", str(A))
                            .replace("{B}", str(B))
                            .replace("{B+1}", str((B+1) % 10))
                            .replace("{B+2}", str((B+2) % 10))
                        )
                        
                        cur.execute("""
                            INSERT INTO full_combinations (
                                mask_id, warehouse_id, regions_id, regions_name, category_id, 
                                warehouse_category, code, category_table_id, mask, sim_esim, category_name, phonenumber
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (mask_id, warehouse_id, regions_id, regions_name, category_id,
                              warehouse_category, code, category_table_id, mask_name, sim_esim, category_name, phonenumber1))

        elif '{B}' in phonenumber:
            for B in range(0, 10):
                phonenumber1 = (
                    phonenumber
                    .replace("{B}", str(B))
                    .replace("{B+1}", str((B+1) % 10))
                    .replace("{B+2}", str((B+2) % 10))
                )
                
                cur.execute("""
                    INSERT INTO full_combinations (
                        mask_id, warehouse_id, regions_id, regions_name, category_id, 
                        warehouse_category, code, category_table_id, mask, sim_esim, category_name, phonenumber
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (mask_id, warehouse_id, regions_id, regions_name, category_id,
                      warehouse_category, code, category_table_id, mask_name, sim_esim, category_name, phonenumber1))

        else:
            cur.execute("""
                INSERT INTO full_combinations (
                    mask_id, warehouse_id, regions_id, regions_name, category_id, 
                    warehouse_category, code, category_table_id, mask, sim_esim, category_name, phonenumber
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (mask_id, warehouse_id, regions_id, regions_name, category_id,
                  warehouse_category, code, category_table_id, mask_name, sim_esim, category_name, phonenumber))

    conn.commit()
    conn.close()
    print("Barcha kombinatsiyalar bazaga yozildi.")


# Asosiy ishga tushirish
if __name__ == "__main__":
    Update_data()
    print("Kombinatsiyalar DBga yozildi.")





































# import sqlite3
# import json

# # config.json o‘qish
# with open("config/config.json", "r", encoding="utf-8") as f:
#     config = json.load(f)
# DB_NAME = config["db_name"]


# # Maskani "9989..." formatga aylantirish
# def generate_phonenumber(Mask):
#     phonenumber = "9989*"
#     result = []
#     if Mask in ("Platinum10", "Platinum20", "Platinum30"):
#         phonenumber = "9989********"
#     else:
#         for char in Mask:
#             if char == 'A':
#                 result.append("{A}")
#             elif char == 'B':
#                 result.append("{B}")
#             elif char == 'C':
#                 result.append("{B+1}")
#             elif char == 'D':
#                 result.append("{B+2}")
#             elif char == '*':
#                 result.append("*")
#             elif char.isdigit():
#                 result.append(char)

#         phonenumber += "".join(result)
#     return phonenumber


# # Bazadan maskalarni olish
# def get_kategoriya():
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     try:
#         cur.execute("SELECT id, mask, tarif FROM kategoriya")
#         rows = cur.fetchall()
#         return rows
#     finally:
#         conn.close()


# # Combination jadvaliga yozish
# def insert_combination(mask_id, mask, tarif, phonenumber):
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             INSERT INTO combination (Mask_id, Mask, Tarif, phonenumber)
#             VALUES (?, ?, ?, ?)
#         """, (mask_id, mask, tarif, phonenumber))
#         conn.commit()
#     finally:
#         conn.close()


# # Kombinatsiyalarni yaratish va DBga yozish
# def Update_data():
#     Maskalar = get_kategoriya()

#     for row in Maskalar:
#         mask_id = row[0]
#         mask_name = row[1]   # masalan "A00BAAB"
#         tarif = row[2]
#         phonenumber = generate_phonenumber(mask_name)

#         if '{A}' in phonenumber:
#             for B in range(0, 10):
#                 for A in range(0, 10):
#                     if A != B:
#                         phonenumber1 = (
#                             phonenumber
#                             .replace("{A}", str(A))
#                             .replace("{B}", str(B))
#                             .replace("{B+1}", str((B+1) % 10))
#                             .replace("{B+2}", str((B+2) % 10))
#                         )
#                         insert_combination(mask_id, mask_name, tarif, phonenumber1)
#                         print(f"{mask_name} -> {phonenumber1}")

#         elif '{B}' in phonenumber:
#             for B in range(0, 10):
#                 phonenumber1 = (
#                     phonenumber
#                     .replace("{B}", str(B))
#                     .replace("{B+1}", str((B+1) % 10))
#                     .replace("{B+2}", str((B+2) % 10))
#                 )
#                 insert_combination(mask_id, mask_name, tarif, phonenumber1)
#                 print(f"{mask_name} -> {phonenumber1}")

#         else:
#             insert_combination(mask_id, mask_name, tarif, phonenumber)
#             print(f"{tarif} | {mask_name} -> {phonenumber}")


# # Asosiy ishga tushirish
# if __name__ == "__main__":
#     Update_data()
#     print("Kombinatsiyalar DBga yozildi.")





















# import sqlite3
# import json

# # config.json o‘qish
# with open("config/config.json", "r", encoding="utf-8") as f:
#     config = json.load(f)
# DB_NAME = config["db_name"]


# # Maskani "9989..." formatga aylantirish
# def generate_phonenumber(Mask):
#     phonenumber = "9989*"
#     result = []
#     if Mask in ("Platinum10", "Platinum20", "Platinum30"):
#         phonenumber = "9989********"
#     else:
#         for char in Mask:
#             if char == 'A':
#                 result.append("{A}")
#             elif char == 'B':
#                 result.append("{B}")
#             elif char == 'C':
#                 result.append("{B+1}")
#             elif char == 'D':
#                 result.append("{B+2}")
#             elif char == '*':
#                 result.append("*")
#             elif char.isdigit():
#                 result.append(char)

#         phonenumber += "".join(result)
#     return phonenumber


# # Bazadan maskalarni olish
# def get_kategoriya():
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     try:
#         cur.execute("SELECT id, mask, tarif FROM kategoriya")
#         rows = cur.fetchall()
#         return rows
#     finally:
#         conn.close()


# # Kombinatsiyalarni yaratish va chiqarish
# def Update_data():
#     phone_numbers = []
#     Maskalar = get_kategoriya()

#     for row in Maskalar:
#         mask_name = row[1]   # masalan "A00BAAB"
#         tarif = row[2]
#         phonenumber = generate_phonenumber(mask_name)

#         if '{A}' in phonenumber:
#             for B in range(0, 10):
#                 for A in range(0, 10):
#                     if A != B:
#                         phonenumber1 = (
#                             phonenumber
#                             .replace("{A}", str(A))
#                             .replace("{B}", str(B))
#                             .replace("{B+1}", str((B+1) % 10))
#                             .replace("{B+2}", str((B+2) % 10))
#                         )
#                         phone_numbers.append(phonenumber1)
#                         print(f"{mask_name} = {phonenumber1.replace('9989*', '')}")

#         elif '{B}' in phonenumber:
#             for B in range(0, 10):
#                 phonenumber1 = (
#                     phonenumber
#                     .replace("{B}", str(B))
#                     .replace("{B+1}", str((B+1) % 10))
#                     .replace("{B+2}", str((B+2) % 10))
#                 )
#                 phone_numbers.append(phonenumber1)
#                 print(f"{mask_name} = {phonenumber1.replace('9989*', '')}")

#         else:
#             phone_numbers.append(phonenumber)
#             print(f"{tarif} = {mask_name} = {phonenumber.replace('9989*', '')}")

#     return phone_numbers


# # Asosiy ishga tushirish
# if __name__ == "__main__":
#     Update_data()
#     print("Kombinatsiyalar yaratildi va konsolga chiqarildi.")