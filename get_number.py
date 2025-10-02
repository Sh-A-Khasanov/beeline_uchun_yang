import time
import json
import random
import sqlite3
import requests
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# config.json o‘qish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

SIM_PAGE_URL = "https://nomer.beeline.uz/sim"
API_BASE = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/random"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/119.0",
]

PROXIES = [
    # agar qo'lingizdagi proxilar bo'lsa shu yerga qo'shing,
    # yoki PROXIES bo'sh bo'lsa skript avtomatik bepul proxylardan topadi.
]

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8",
}

PROXYSCRAPE_URL = (
    "https://api.proxyscrape.com/?request=getproxies&proxytype=http"
    "&timeout=5000&country=all&ssl=all&anonymity=all"
)

# ---------- proxy yuklash va tekshirish ----------
def fetch_proxies_from_proxyscrape(limit=200):
    try:
        r = requests.get(PROXYSCRAPE_URL, timeout=10)
        raw = r.text.strip().splitlines()
        raw = [p.strip() for p in raw if p.strip()]
        return raw[:limit]
    except Exception:
        return []

def check_proxy_alive(proxy, test_url="https://nomer.beeline.uz", timeout=6):
    try:
        resp = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=timeout)
        return proxy if resp.status_code == 200 else None
    except Exception:
        return None

def fetch_and_check_proxies(max_good=40, workers=30):
    raw = fetch_proxies_from_proxyscrape(limit=1000)
    good = []
    if not raw:
        return good
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(check_proxy_alive, p): p for p in raw}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                good.append(res)
                if len(good) >= max_good:
                    break
    return good




def save_json_to_db(json_items, warehouse_row_id=None, regions_id=None):
    """
    Yangi elementlar bazaga yoziladi.
    Agar id yoki phoneNumber mavjud bo'lsa, yozilmaydi (skip).
    Konsolga nechta yangi yozilganini chiqaradi.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    inserted = 0
    skipped = 0

    for item in json_items:
        item_id = item.get("id")
        phone = item.get("phoneNumber")

        # tekshirish: id yoki phoneNumber borligini aniqlaymiz
        cur.execute("SELECT 1 FROM numbers WHERE id=? OR (phoneNumber IS NOT NULL AND phoneNumber=?) LIMIT 1", (item_id, phone))
        if cur.fetchone():
            skipped += 1
            continue

        cur.execute("""
        INSERT INTO numbers (
            id, phoneNumber, regions_id, warehouse_row_id, ctnStatus, phoneNumberStatus, phoneNumberStatusId,
            warehouseCode, price, marketCodes, warehouse, warehouseId,
            createdAt, updatedAt, createdBy, createdById, modifiedBy, modifiedById
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            item_id,
            phone,
            regions_id,
            warehouse_row_id,
            item.get("ctnStatus"),
            item.get("phoneNumberStatus"),
            item.get("phoneNumberStatusId"),
            item.get("warehouseCode"),
            item.get("price"),
            ",".join(item.get("marketCodes", [])) if item.get("marketCodes") else None,
            item.get("warehouse"),
            item.get("warehouseId"),
            item.get("createdAt"),
            item.get("updatedAt"),
            item.get("createdBy"),
            item.get("createdById"),
            item.get("modifiedBy"),
            item.get("modifiedById")
        ))
        inserted += 1

    conn.commit()
    conn.close()

    print(f"{SIM_PAGE_URL}Bazaga yozildi: {inserted} ta yangi raqam. Skipped (allaqachon mavjud): {skipped} ta.")


# ---------- Selenium va cookie ----------
def start_selenium(proxy=None, user_agent=None, headless=True):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    # Headless mode (ko‘rinmaydigan rejim)
    if headless:
        chrome_options.add_argument("--headless=new")  # Chrome 109+ uchun

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def get_cookies_from_driver(driver):
    driver.get(SIM_PAGE_URL)
    time.sleep(4)
    selenium_cookies = driver.get_cookies()
    cookie_dict = {c["name"]: c["value"] for c in selenium_cookies}
    return cookie_dict

def cookies_dict_to_header(cookie_dict):
    return "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

def build_proxy_dict(proxy):
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}

# ---------- yordamchi: warehouses o'qish ----------
def get_warehouses_from_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        # warehouses jadvalidan id, code va regions_id olinadi
        cur.execute("SELECT id, code, regions_id FROM warehouses")
        rows = cur.fetchall()
        # har bir element: {"row_id": id, "code": code, "regions_id": regions_id}
        return [{"row_id": r[0], "code": r[1], "regions_id": r[2]} for r in rows]
    finally:
        conn.close()

# ---------- asosiy oqim ----------
def main():
    session = requests.Session()

    global PROXIES
    if not PROXIES:
        print("PROXIES bo'sh. Bepul proxylar yuklanmoqda va tekshirilmoqda...")
        found = fetch_and_check_proxies(max_good=40, workers=30)
        if found:
            PROXIES = found
            print(f"Topildi va ro'yxatga qo'shildi: {len(PROXIES)} proxilar.")
        else:
            print("Ishlaydigan proxy topilmadi. Faqat User-Agent rotation bilan davom etiladi.")

    proxy_cycle = itertools.cycle(PROXIES) if PROXIES else None
    ua_cycle = itertools.cycle(USER_AGENTS)

    current_proxy = next(proxy_cycle) if proxy_cycle else None
    current_ua = next(ua_cycle)

    # Selenium boshlash va cookie olish
    driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
    cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))

    warehouses = get_warehouses_from_db()
    if not warehouses:
        print("Warehouses jadvalidan hech nima topilmadi. Avval warehouses jadvalini to'ldiring.")
        return

    try:
        for wh in warehouses:
            warehouse_code = wh["code"]
            warehouse_row_id = wh["row_id"]
            regions_id = wh["regions_id"]

            page = 1
            size = 100

            while True:
                params = {"page": page, "size": size, "warehouse_code": warehouse_code}
                full_url = f"{API_BASE}?page={page}&size={size}&warehouse_code={warehouse_code}"

                headers = COMMON_HEADERS.copy()
                headers["User-Agent"] = current_ua
                headers["Cookie"] = cookie_header
                headers["Referer"] = SIM_PAGE_URL

                proxies_param = build_proxy_dict(current_proxy)

                print(f"So‘rov yuborilyapti: {full_url}")
                print(f"Ishlatilayotgan proxy: {current_proxy}")
                print(f"Ishlatilayotgan User-Agent: {current_ua}")

                resp = None
                try:
                    resp = session.get(API_BASE, params=params, headers=headers, proxies=proxies_param, timeout=25)
                except Exception as e:
                    print(f"Request error: {e}")
                    # tarmoq/proxy muammosi bo'lsa yangi proxy va UA ga o'tish
                    if proxy_cycle:
                        current_proxy = next(proxy_cycle)
                        print(f"Request exception — yangi proxy: {current_proxy}")
                    current_ua = next(ua_cycle)
                    print(f"Request exception — yangi UA: {current_ua}")

                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
                    cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))
                    time.sleep(3)
                    continue

                print(f"Status code: {resp.status_code}")

                if resp.status_code == 429:
                    # aynan shu yerda proxy va UAni almashtiramiz
                    print("429 olindi. Proxy va User-Agent yangilanmoqda, Selenium qayta ishga tushadi.")
                    if proxy_cycle:
                        current_proxy = next(proxy_cycle)
                        print(f"429 -> yangi proxy: {current_proxy}")
                    else:
                        current_proxy = None
                    current_ua = next(ua_cycle)
                    print(f"429 -> yangi UA: {current_ua}")

                    try:
                        driver.quit()
                    except Exception:
                        pass

                    driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
                    cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))

                    # qisqa kutish va keyin aynan shu page ni qayta urinish
                    time.sleep(5 + random.randint(0,5))
                    continue

                if resp.status_code != 200:
                    print("200 qaytmayapti. Keyingi warehouse yoki page ga o'tish.")
                    time.sleep(2)
                    break

                try:
                    data = resp.json()
                except Exception:
                    print("JSON parse qilolmadi.")
                    break

                total_pages = data.get("totalPages", 1)
                items = data.get("content", [])
                if items:
                    save_json_to_db(items, warehouse_row_id=warehouse_row_id, regions_id=regions_id)
                    print(f"Bazaga yozildi: {len(items)} ta raqam (warehouse_row_id={warehouse_row_id}, regions_id={regions_id}, page={page})")
                else:
                    print("Sahifada item topilmadi.")

                if page >= total_pages:
                    break
                page += 1

                # ixtiyoriy: sahifa almashtirganda UA yoki proxyni ham yangilash mumkin
                # current_ua = next(ua_cycle)
                # if proxy_cycle: current_proxy = next(proxy_cycle)

                time.sleep(random.randint(5, 12))

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        session.close()

if __name__ == "__main__":
    main()
































































# import time
# import json
# import random
# import sqlite3
# import requests
# import itertools
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options

# # config.json o‘qish
# with open("config/config.json", "r", encoding="utf-8") as f:
#     config = json.load(f)

# DB_NAME = config["db_name"]

# SIM_PAGE_URL = "https://nomer.beeline.uz/sim"
# API_BASE = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/random"

# # USER_AGENTS misoli
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
#     "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/119.0",
# ]

# # Agar sizda qo'lda proxylaringiz bo'lsa shu ro'yxatga qo'shing.
# PROXIES = [
#     # "http://user:pass@1.2.3.4:8080",
#     # "http://5.6.7.8:3128",
# ]

# COMMON_HEADERS = {
#     "Accept": "application/json, text/plain, */*",
#     "Accept-Language": "en-US,en;q=0.9,uz;q=0.8",
# }

# # ---------- proxy yuklash va tekshirish ----------
# PROXYSCRAPE_URL = (
#     "https://api.proxyscrape.com/?request=getproxies&proxytype=http"
#     "&timeout=5000&country=all&ssl=all&anonymity=all"
# )

# def fetch_proxies_from_proxyscrape(limit=200):
#     try:
#         r = requests.get(PROXYSCRAPE_URL, timeout=10)
#         raw = r.text.strip().splitlines()
#         raw = [p.strip() for p in raw if p.strip()]
#         return raw[:limit]
#     except Exception:
#         return []

# def check_proxy_alive(proxy, test_url="https://nomer.beeline.uz", timeout=6):
#     try:
#         resp = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=timeout)
#         return proxy if resp.status_code == 200 else None
#     except Exception:
#         return None

# def fetch_and_check_proxies(max_good=40, workers=30):
#     raw = fetch_proxies_from_proxyscrape(limit=1000)
#     good = []
#     if not raw:
#         return good

#     with ThreadPoolExecutor(max_workers=workers) as ex:
#         futures = {ex.submit(check_proxy_alive, p): p for p in raw}
#         for fut in as_completed(futures):
#             res = fut.result()
#             if res:
#                 good.append(res)
#                 if len(good) >= max_good:
#                     break
#     return good

# # ---------- DB ----------
# def init_db():
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS numbers (
#             id INTEGER PRIMARY KEY,
#             phoneNumber TEXT,
#             warehouses_id INTEGER,
#             ctnStatus TEXT,
#             phoneNumberStatus TEXT,
#             phoneNumberStatusId INTEGER,
#             warehouseCode INTEGER,
#             price INTEGER,
#             marketCodes TEXT,
#             warehouse TEXT,
#             warehouseId INTEGER,
#             createdAt TEXT,
#             updatedAt TEXT,
#             createdBy TEXT,
#             createdById INTEGER,
#             modifiedBy TEXT,
#             modifiedById INTEGER
#         );
#     """)
#     conn.commit()
#     conn.close()

# def save_json_to_db(json_items):
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     for item in json_items:
#         cur.execute("""
#         INSERT OR REPLACE INTO numbers (
#             id, phoneNumber, ctnStatus, phoneNumberStatus, phoneNumberStatusId,
#             warehouseCode, price, marketCodes, warehouse, warehouseId,
#             createdAt, updatedAt, createdBy, createdById, modifiedBy, modifiedById
#         ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
#         """, (
#             item.get("id"),
#             item.get("phoneNumber"),

#             item.get("ctnStatus"),
#             item.get("phoneNumberStatus"),
#             item.get("phoneNumberStatusId"),
#             item.get("warehouseCode"),
#             item.get("price"),
#             ",".join(item.get("marketCodes", [])) if item.get("marketCodes") else None,
#             item.get("warehouse"),
#             item.get("warehouseId"),
#             item.get("createdAt"),
#             item.get("updatedAt"),
#             item.get("createdBy"),
#             item.get("createdById"),
#             item.get("modifiedBy"),
#             item.get("modifiedById"),
#         ))
#     conn.commit()
#     conn.close()

# # ---------- Selenium va cookie ----------
# def start_selenium(proxy=None, user_agent=None):
#     chrome_options = Options()
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")
#     if proxy:
#         chrome_options.add_argument(f'--proxy-server={proxy}')
#     if user_agent:
#         chrome_options.add_argument(f'--user-agent={user_agent}')
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
#     return driver

# def get_cookies_from_driver(driver):
#     driver.get(SIM_PAGE_URL)
#     time.sleep(4)
#     selenium_cookies = driver.get_cookies()
#     cookie_dict = {c["name"]: c["value"] for c in selenium_cookies}
#     return cookie_dict

# def cookies_dict_to_header(cookie_dict):
#     return "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

# # ---------- yordamchi ----------
# def build_proxy_dict(proxy):
#     if not proxy:
#         return None
#     return {"http": proxy, "https": proxy}

# # ---------- asosiy oqim ----------
# def main():
#     init_db()
#     session = requests.Session()

#     # Agar PROXIES bo'sh bo'lsa, avtomatik topamiz va tekshiramiz
#     global PROXIES
#     if not PROXIES:
#         print("PROXIES ro'yxati bo'sh. Bepul proxylar yuklanmoqda va tekshirilmoqda...")
#         found = fetch_and_check_proxies(max_good=40, workers=30)
#         if found:
#             PROXIES = found
#             print(f"Topildi va ishlaydigan proxylardan {len(PROXIES)} ta ro'yxatga qo'shildi.")
#         else:
#             print("Ishlaydigan proxy topilmadi. Skript faqat User-Agent rotation bilan davom etadi.")

#     proxy_cycle = itertools.cycle(PROXIES) if PROXIES else None
#     ua_cycle = itertools.cycle(USER_AGENTS)

#     current_proxy = next(proxy_cycle) if proxy_cycle else None
#     current_ua = next(ua_cycle)

#     # Selenium boshlash va cookie olish
#     driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
#     cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))

#     # warehouse kodlarini o'qish
#     conn = sqlite3.connect(DB_NAME)
#     cur = conn.cursor()
#     try:
#         cur.execute("SELECT code FROM warehouses")
#         rows = cur.fetchall()
#         warehouse_codes = [r[0] for r in rows]
#     finally:
#         conn.close()

#     try:
#         for warehouse_code in warehouse_codes:
#             page = 1
#             size = 90

#             while True:
#                 params = {"page": page, "size": size, "warehouse_code": warehouse_code}
#                 full_url = f"{API_BASE}?page={page}&size={size}&warehouse_code={warehouse_code}"

#                 headers = COMMON_HEADERS.copy()
#                 headers["User-Agent"] = current_ua
#                 headers["Cookie"] = cookie_header
#                 headers["Referer"] = SIM_PAGE_URL

#                 proxies_param = build_proxy_dict(current_proxy)

#                 print(f"So‘rov yuborilyapti: {full_url}")
#                 print(f"Ishlatilayotgan proxy: {current_proxy}")
#                 print(f"Ishlatilayotgan User-Agent: {current_ua}")

#                 resp = None
#                 try:
#                     resp = session.get(API_BASE, params=params, headers=headers, proxies=proxies_param, timeout=25)
#                 except Exception as e:
#                     print(f"Request error: {e}")
#                     # proxy yoki tarmoq muammosi bo'lsa, yangi proxyga o'tish
#                     if proxy_cycle:
#                         current_proxy = next(proxy_cycle)
#                     current_ua = next(ua_cycle)
#                     # seleniumni yangilab cookie olishga urinish
#                     try:
#                         driver.quit()
#                     except Exception:
#                         pass
#                     driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
#                     cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))
#                     time.sleep(3)
#                     continue

#                 print(f"Status code: {resp.status_code}")

#                 if resp.status_code == 429:
#                     print("429 olindi. Proxy va User-Agentni o'zgartiraman, Seleniumni qayta ishga tushiraman.")
#                     # yangi proxy va UA
#                     if proxy_cycle:
#                         current_proxy = next(proxy_cycle)
#                     else:
#                         current_proxy = None
#                     current_ua = next(ua_cycle)

#                     try:
#                         driver.quit()
#                     except Exception:
#                         pass

#                     driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
#                     cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))

#                     # serverni tinchtirish uchun kutish
#                     time.sleep(5 + random.randint(0,5))
#                     continue

#                 if resp.status_code != 200:
#                     print("200 qaytmayapti. Keyingi sahifa yoki warehouse ga o'tish.")
#                     time.sleep(2)
#                     break

#                 # JSON va yozish
#                 try:
#                     data = resp.json()
#                 except Exception:
#                     print("JSON parse qilolmadi.")
#                     break

#                 total_pages = data.get("totalPages", 1)
#                 items = data.get("content", [])
#                 if items:
#                     save_json_to_db(items)
#                     print(f"Bazaga yozildi: {len(items)} ta raqam (warehouse_code={warehouse_code}, page={page})")
#                 else:
#                     print("Sahifada item topilmadi.")

#                 if page >= total_pages:
#                     break
#                 page += 1

#                 # navbatdagi so'rov uchun UA va proxy maydonini yangilash imkoniyati (opsional)
#                 # current_ua = next(ua_cycle)  # agar har sahifada UA almashtirmoqchi bo'lsangiz izohni oching
#                 # current_proxy = next(proxy_cycle) if proxy_cycle else current_proxy

#                 time.sleep(random.randint(5, 12))

#     finally:
#         try:
#             driver.quit()
#         except Exception:
#             pass
#         session.close()

# if __name__ == "__main__":
#     main()
