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

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --- Jadval yaratish va ustunlarni tekshirish ---
    def create_or_update_table(table_name, create_sql, required_columns):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(create_sql)
            logger.info(f"{table_name} jadvali yaratildi.")
        else:
            logger.info(f"{table_name} jadvali allaqachon mavjud.")

            # mavjud ustunlarni olish
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = [r[1] for r in cursor.fetchall()]

            # kerakli ustunlarni tekshirish
            for col_name, col_type in required_columns.items():
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                    logger.info(f"{table_name} jadvaliga {col_name} ustuni qo‘shildi.")

    # Numbers jadvali
    create_or_update_table(
        "numbers",
        """
        CREATE TABLE numbers (
            id INTEGER PRIMARY KEY,
            phoneNumber TEXT,
            warehouse_row_id INTEGER,
            regions_id INTEGER,
            ctnStatus TEXT,
            phoneNumberStatus TEXT,
            phoneNumberStatusId INTEGER,
            warehouseCode INTEGER,
            price INTEGER,
            marketCodes TEXT,
            warehouse TEXT,
            warehouseId INTEGER,
            createdAt TEXT,
            updatedAt TEXT,
            createdBy TEXT,
            createdById INTEGER,
            modifiedBy TEXT,
            modifiedById INTEGER
        )
        """,
        {
            "id": "INTEGER",
            "phoneNumber": "TEXT",
            "warehouse_row_id": "INTEGER",
            "regions_id": "INTEGER",
            "ctnStatus": "TEXT",
            "phoneNumberStatus": "TEXT",
            "phoneNumberStatusId": "INTEGER",
            "warehouseCode": "INTEGER",
            "price": "INTEGER",
            "marketCodes": "TEXT",
            "warehouse": "TEXT",
            "warehouseId": "INTEGER",
            "createdAt": "TEXT",
            "updatedAt": "TEXT",
            "createdBy": "TEXT",
            "createdById": "INTEGER",
            "modifiedBy": "TEXT",
            "modifiedById": "INTEGER"
        }
    )

    # number_mask jadvali
    create_or_update_table(
        "number_mask",
        """
        CREATE TABLE number_mask (
            id INTEGER PRIMARY KEY,
            sim_esim TEXT,
            mask TEXT,
            category TEXT,
            category_id TEXT
        )
        """,
        {
            "id": "INTEGER",
            "sim_esim": "TEXT",
            "mask": "TEXT",     
            "category": "TEXT",
            "category_id": "TEXT"
        }
    )
    # Warehouses jadvali
    # create_or_update_table(
    #     "warehouses",
    #     """
    #     CREATE TABLE warehouses (
    #         id INTEGER PRIMARY KEY,
    #         regions_id INTEGER,
    #         regions_name TEXT,
    #         nameRu TEXT,
    #         nameUz TEXT,
    #         code INTEGER,
    #         price REAL,
    #         partialPaymentService TEXT,
    #         partialPaymentServiceId INTEGER,
    #         region TEXT,
    #         regionId INTEGER,
    #         service TEXT,
    #         serviceId INTEGER,
    #         conditionOfUse TEXT,
    #         conditionOfUseId INTEGER,
    #         createdAt TEXT,
    #         updatedAt TEXT,
    #         createdBy TEXT,
    #         createdById INTEGER,
    #         modifiedBy TEXT,
    #         modifiedById INTEGER,
    #         active BOOLEAN,
    #         partialPayment BOOLEAN,
    #         description TEXT
    #     )
    #     """,
    #     {
    #         "id": "INTEGER",
    #         "regions_id": "INTEGER",
    #         "regions_name": "TEXT",
    #         "nameRu": "TEXT",
    #         "nameUz": "TEXT",
    #         "code": "INTEGER",
    #         "price": "REAL",
    #         "partialPaymentService": "TEXT",
    #         "partialPaymentServiceId": "INTEGER",
    #         "region": "TEXT",
    #         "regionId": "INTEGER",
    #         "service": "TEXT",
    #         "serviceId": "INTEGER",
    #         "conditionOfUse": "TEXT",
    #         "conditionOfUseId": "INTEGER",
    #         "createdAt": "TEXT",
    #         "updatedAt": "TEXT",
    #         "createdBy": "TEXT",
    #         "createdById": "INTEGER",
    #         "modifiedBy": "TEXT",
    #         "modifiedById": "INTEGER",
    #         "active": "BOOLEAN",
    #         "partialPayment": "BOOLEAN",
    #         "description": "TEXT"
    #     }
    # )
     # Warehouses jadvali
    create_or_update_table(
        "warehouses",
        """
        CREATE TABLE warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regions_id INTEGER,
            regions_name TEXT,
            category_id INTEGER,
            category TEXT,
            code INTEGER,
            UNIQUE(regions_id, category_id, code)
        )
        """,
        {
            "id": "INTEGER",
            "regions_id": "INTEGER",
            "regions_name": "TEXT",
            "category_id": "INTEGER",
            "category": "TEXT",         
            "code": "INTEGER"
        }
    )
    create_or_update_table(
        "numbers_esim",
        """
        CREATE TABLE numbers_esim  (
            id INTEGER PRIMARY KEY,
            regions_id INTEGER,
            regions_name TEXT,
            mask_id INTEGER,
            mask TEXT,
            category_id INTEGER,
            warehouse_category TEXT,
            phoneNumber INTEGER,
            name TEXT,
            price REAL,
            cancelDate TEXT,
            code INTEGER,
            n1 INTEGER,
            n2 INTEGER,
            n3 INTEGER,
            n4 INTEGER,
            n5 INTEGER,
            n6 INTEGER,
            n7 INTEGER
        )
        """,
        {
            "id": "INTEGER",
            "regions_id": "INTEGER",
            "regions_name": "TEXT",
            "mask_id": "INTEGER",
            "mask": "TEXT",
            "category_id": "INTEGER",
            "warehouse_category": "TEXT",
            "phoneNumber": "INTEGER",
            "name": "TEXT",
            "price": "REAL",
            "cancelDate": "TEXT",
            "code": "INTEGER",
            "n1": "INTEGER",
            "n2": "INTEGER",
            "n3": "INTEGER",
            "n4": "INTEGER",
            "n5": "INTEGER",
            "n6": "INTEGER",
            "n7": "INTEGER"
        }
    )
    create_or_update_table(
        "prefix",
        """
        CREATE TABLE prefix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regions_id INTEGER,
            regions_name TEXT,
            n_Code INTEGER,
            ate INTEGER
        )
        """,
        {
            "id": "INTEGER",
            "regions_id": "INTEGER",
            "regions_name": "TEXT",
            "n_Code": "INTEGER",
            "ate": "INTEGER"
        }
    )
    create_or_update_table(
        "full_combinations",
        """
        CREATE TABLE full_combinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mask_id INTEGER,
            mask TEXT,
            warehouse_id INTEGER,
            warehouse_category TEXT,
            regions_id INTEGER,
            regions_name TEXT,
            category_id INTEGER,
            category_name TEXT,
            code TEXT,
            category_table_id INTEGER,
            sim_esim TEXT,
            phonenumber TEXT
        )
        """,
        {
            "id": "INTEGER",
            "mask_id": "INTEGER",
            "mask": "TEXT",
            "warehouse_id": "INTEGER",
            "warehouse_category": "TEXT",
            "regions_id": "INTEGER",
            "regions_name": "TEXT",
            "category_id": "INTEGER",
            "category_name": "TEXT",
            "code": "TEXT",
            "category_table_id": "INTEGER",
            "sim_esim": "TEXT",
            "phonenumber": "TEXT"
        }
    )
    
    create_or_update_table(
        "warehouse_categories",
        """
        CREATE TABLE warehouse_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regions_id INTEGER,
            regions_name TEXT,
            warehouse_id INTEGER,
            category_id INTEGER,
            warehouse_category TEXT,
            code TEXT,
            category_table_id INTEGER,
            mask TEXT,
            sim_esim TEXT,
            category_name TEXT
        )
        """,
        {
            "id": "INTEGER",
            "regions_id": "INTEGER",
            "regions_name": "TEXT",
            "warehouse_id": "INTEGER",
            "category_id": "INTEGER",
            "warehouse_category": "TEXT",   
            "code": "TEXT",
            "category_table_id": "INTEGER",
            "mask": "TEXT",
            "sim_esim": "TEXT",
            "category_name": "TEXT"
        }
    )
    conn.commit()
    # phoneNumber uchun 
    cursor.execute("PRAGMA index_list('numbers')")
    indexes = [r[1] for r in cursor.fetchall()]
    if "idx_numbers_phoneNumber_unique" not in indexes:
        cursor.execute(
            "CREATE UNIQUE INDEX idx_numbers_phoneNumber_unique ON numbers(phoneNumber);"
        )
        conn.commit()
        logger.info("phoneNumber uchun  yaratildi.")
    else:
        logger.info("phoneNumber  allaqachon mavjud.")

    conn.close()
    logger.info("DB initsializatsiyasi yakunlandi.")




if __name__ == "__main__":
    init_db()
