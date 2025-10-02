import time
import json
import random
import sqlite3
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from setting.full_combinations import generate_phonenumber, get_kategoriya







# Logging konfiguratsiyasi: chiroyli format, keraksiz loglarni o'chirish
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# config.json o‘qish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

SIM_PAGE_URL = "https://nomer.beeline.uz/sim"
API_BASE = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/"
# API_BASE = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/random"
# https://nomer.beeline.uz/msapi/web/rms/phone-numbers/?page=0&size=90&warehouse_code=1201&phone_number_mask=9989****1131

USER_AGENTS = [
    #  "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 15; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Edg/129.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
]

PROXIES = [
    # agar qo'lingizdagi proxilar bo'lsa shu yerga qo'shing,
    # yoki PROXIES bo'sh bo'lsa skript avtomatik bepul proxylardan topadi.
]

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8",
}

PROXY_API_URLS = [
    "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=5000&country=all&ssl=all&anonymity=all",
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://openproxylist.xyz/http.txt"
]

# ---------- proxy yuklash va tekshirish ----------
def fetch_proxies_from_apis(limit=200):
    logger.info("Proxylarni API'lardan yuklash boshlandi.")
    raw_proxies = []
    for url in PROXY_API_URLS:
        try:
            logger.debug(f"API dan yuklash: {url}")
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            proxies = r.text.strip().splitlines()
            proxies = [p.strip() for p in proxies if p.strip() and ':' in p]
            raw_proxies.extend(proxies)
            logger.info(f"{url} dan {len(proxies)} ta proxy topildi.")
            if len(raw_proxies) >= limit:
                break
        except Exception as e:
            logger.error(f"API {url} dan proxy olishda xato: {e}")
            continue
    raw_proxies = list(set(raw_proxies))[:limit]
    logger.info(f"Jami {len(raw_proxies)} ta noyob proxy topildi.")
    return raw_proxies

def check_proxy_alive(proxy, test_url="https://nomer.beeline.uz", timeout=6):
    logger.debug(f"Proxy tekshirilmoqda: {proxy}")
    try:
        resp = requests.get(test_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=timeout)
        if resp.status_code == 200:
            logger.info(f"Yaxshi proxy topildi: {proxy}")
            return proxy
        else:
            logger.debug(f"Proxy {proxy} ishlamadi: status {resp.status_code}")
            return None
    except Exception as e:
        logger.debug(f"Proxy {proxy} da xato: {e}")
        return None

def fetch_and_check_proxies(max_good=40, workers=20):
    logger.info("Ishlaydigan proxylarni yuklash va tekshirish boshlandi.")
    raw = fetch_proxies_from_apis(limit=1000)
    if not raw:
        logger.warning("Hech qanday proxy topilmadi.")
        return []
    
    good = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(check_proxy_alive, p): p for p in raw}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                good.append(res)
                if len(good) >= max_good:
                    logger.info(f"Maksimal {max_good} ta proxy topildi, to'xtatilmoqda.")
                    break
    logger.info(f"Jami {len(good)} ta ishlaydigan proxy topildi.")
    return good


def save_json_to_db(json_items, warehouse_row_id=None, regions_id=None):
    logger.info("Ma'lumotlarni DB ga saqlash boshlandi.")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    inserted = 0
    skipped = 0

    for item in json_items:
        item_id = item.get("id")
        phone = item.get("phoneNumber")

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

    logger.info(f"Bazaga yozildi: {inserted} ta yangi raqam. Skipped (mavjud): {skipped} ta.")

# ---------- Selenium va cookie ----------
def start_selenium(proxy=None, user_agent=None, headless=True):
    logger.info("Selenium drayveri ishga tushirilmoqda.")
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")  # Keraksiz loglarni o'chirish
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Chrome loglarini o'chirish

    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    if headless:
        chrome_options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    logger.info("Selenium drayveri tayyor.")
    return driver

def get_cookies_from_driver(driver):
    logger.info("Cookie'larni olish uchun sahifa yuklanmoqda.")
    driver.get(SIM_PAGE_URL)
    time.sleep(4)
    selenium_cookies = driver.get_cookies()
    cookie_dict = {c["name"]: c["value"] for c in selenium_cookies}
    logger.info("Cookie'lar olingan.")
    return cookie_dict

def cookies_dict_to_header(cookie_dict):
    return "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

def build_proxy_dict(proxy):
    if not proxy:
        return None
    return {"http": f"http://{proxy}", "https": f"http://{proxy}"}

# ---------- yordamchi: warehouses o'qish ----------
def get_warehouses_from_db(region_filter=15):
    logger.info(f"Region_id={region_filter} bo'lgan warehouses ma'lumotlarini DB dan olish boshlandi.")
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, code, regions_id FROM warehouses WHERE regions_id=?", (region_filter,))
        rows = cur.fetchall()
        warehouses = [{"row_id": r[0], "code": r[1], "regions_id": r[2]} for r in rows]
        logger.info(f"{len(warehouses)} ta warehouse topildi.")
        return warehouses
    finally:
        conn.close()


    

# ---------- asosiy oqim ----------
import sqlite3
import random
import time
import requests
# import boshqa kerakli modul va sozlamalar (COMMON_HEADERS, API_BASE, start_selenium va hokazo)


def get_phone_masks_from_db(db_path=DB_NAME, limit=None):
    """
    full_combinations jadvalidan phonenumber ustunini o'qib ro'yxat qaytaradi.
    Agar masklar bir xil takrorlansa, DISTINCT bilan chiqaradi.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        sql = "SELECT DISTINCT phonenumber FROM full_combinations WHERE phonenumber IS NOT NULL"
        if limit:
            sql += f" LIMIT {int(limit)}"
        cur.execute(sql)
        rows = cur.fetchall()
        masks = [r[0] for r in rows if r and r[0]]
        return masks
    finally:
        cur.close()
        conn.close()


def main():
    session = requests.Session()

    global PROXIES
    if not PROXIES:
        logger.info("PROXIES bo'sh, bepul proxylar yuklanmoqda.")
        PROXIES = fetch_and_check_proxies(max_good=40, workers=20)
        if PROXIES:
            logger.info(f"Topildi: {len(PROXIES)} ta proxy.")
        else:
            logger.warning("Ishlaydigan proxy topilmadi. User-Agent rotation bilan davom etiladi.")

    proxy_list = PROXIES
    ua_list = USER_AGENTS

    proxy_idx = 0
    ua_idx = 0

    current_proxy = proxy_list[proxy_idx] if proxy_list else None
    current_ua = ua_list[ua_idx]

    driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
    cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))

    warehouses = get_warehouses_from_db()
    if not warehouses:
        logger.error("Warehouses jadvalidan hech nima topilmadi. Avval to'ldiring.")
        return

    # <-- BU YERDA masklarni DB dan o'qiymiz
    phone_masks = get_phone_masks_from_db()
    if not phone_masks:
        logger.warning("full_combinations jadvalidan telefon masklari topilmadi.")
        # agar topilmasa default bir mask ishlatish uchun:
        phone_masks = ["9989******15"]

    try:
        for wh in warehouses:
            warehouse_code = wh["code"]
            warehouse_row_id = wh["row_id"]
            regions_id = wh["regions_id"]
            logger.info(f"Warehouse ishlov berilmoqda: code={warehouse_code}, row_id={warehouse_row_id}, regions_id={regions_id}")

            # Har bir warehouse uchun barcha masklarni aylaymiz
            for phone_number_mask in phone_masks:
                page = 0
                size = 100

                # Agar juda ko'p mask bo'lsa, ixtiyoriy yoki namunalash qo'yish mumkin.
                logger.info(f"Bag'langan mask: {phone_number_mask} bilan ishlanmoqda (warehouse={warehouse_code})")

                while True:

                    # params dictionary ishlatmaymiz
                    url = (
                        f"{API_BASE}?page={page}"
                        f"&size={size}"
                        f"&warehouse_code={warehouse_code}"
                        f"&phone_number_mask={phone_number_mask}"
                    )

                    headers = COMMON_HEADERS.copy()
                    headers["User-Agent"] = current_ua
                    headers["Cookie"] = cookie_header
                    headers["Referer"] = SIM_PAGE_URL

                    proxies_param = build_proxy_dict(current_proxy)

                    logger.debug(f"Proxy: {current_proxy}, User-Agent: {current_ua}")
                    print("So‘rov yuborilgan URL:", url)  # <-- aniq qaysi URL ketayotganini ko‘rasiz

                    try:
                        resp = session.get(url, headers=headers, proxies=proxies_param, timeout=25)
                        status_code = resp.status_code
                        logger.info(f"Status code: {status_code}")
                        print("Javob (birinchi 500 belgi):", resp.text[:500])  # <-- qaytgan contentni ham ko‘rasiz
                    except Exception as e:
                        logger.error(f"So'rovda xato: {e}")
                        status_code = None



                    if status_code == 429 or status_code is None:
                        # ua/proxy yangilash mantiqi shu joyda qoldirildi (sizning avvalgi mantiqingiz)
                        ua_idx += 1
                        if ua_idx >= len(ua_list):
                            ua_idx = 0
                            proxy_idx += 1
                            if proxy_idx >= len(proxy_list):
                                new_proxies = fetch_and_check_proxies(max_good=40, workers=10)
                                if not new_proxies:
                                    logger.error("Yangi proxy topilmadi. To'xtatilmoqda.")
                                    return
                                proxy_list = new_proxies
                                proxy_idx = 0
                        current_proxy = proxy_list[proxy_idx] if proxy_list else None
                        current_ua = ua_list[ua_idx]
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        try:
                            driver = start_selenium(proxy=current_proxy, user_agent=current_ua)
                        except Exception as e:
                            logger.error(f"New driver start failed: {e}. Skipping retry.")
                            continue
                        cookie_header = cookies_dict_to_header(get_cookies_from_driver(driver))
                        time.sleep(10 + random.randint(0, 10))
                        continue

                    if status_code != 200:
                        logger.warning("200 qaytmayapti. Keyingi mask yoki warehouse ga o'tish.")
                        time.sleep(1)
                        break

                    try:
                        data = resp.json()
                    except Exception as e:
                        logger.error(f"JSON parse xatosi: {e}")
                        break

                    total_pages = data.get("totalPages", 1)
                    items = data.get("content", [])
                    if items:
                        save_json_to_db(items, warehouse_row_id=warehouse_row_id, regions_id=regions_id)
                        logger.info(f"{len(items)} ta raqam saqlandi (mask={phone_number_mask}) ({page}/{total_pages})")
                    else:
                        logger.info("Sahifada item topilmadi.")

                    if page >= total_pages:
                        logger.info(f"Mask uchun barcha sahifalar tugadi (mask={phone_number_mask}, total_pages={total_pages}).")
                        break
                    page += 1

                    time.sleep(random.randint(5, 12))

                # masklar orasida qisqacha pauza
                time.sleep(random.randint(1, 3))

    finally:
        try:
            driver.quit()
            logger.info("Selenium drayveri yopildi.")
        except Exception:
            pass
        session.close()
        logger.info("Sessiya yopildi.")
















if __name__ == "__main__":
    main()


























































































# import time
# import json
# import random
# import sqlite3
# import requests
# import logging
# from concurrent.futures import ThreadPoolExecutor
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options

# # Logging sozlamalari
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     filename='scraper.log',
#     filemode='a'
# )
# logger = logging.getLogger(__name__)

# # Config o'qish
# with open("config/config.json", "r", encoding="utf-8") as f:
#     config = json.load(f)

# DB_NAME = config["db_name"]
# SIM_PAGE_URL = "https://nomer.beeline.uz/sim"
# API_BASE = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/random"

# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
#     "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/129.0.0.0 Mobile Safari/537.36"
# ]

# PROXY_API_URLS = [
#     "https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=5000&country=all&ssl=all&anonymity=all",
#     "https://www.proxy-list.download/api/v1/get?type=http"
# ]

# COMMON_HEADERS = {
#     "Accept": "application/json, text/plain, */*",
#     "Accept-Language": "en-US,en;q=0.9,uz;q=0.8"
# }

# def fetch_proxies(limit=100):
#     logger.info("Proxylarni yuklash boshlandi")
#     proxies = set()
#     for url in PROXY_API_URLS:
#         try:
#             r = requests.get(url, timeout=10)
#             r.raise_for_status()
#             proxies.update(p.strip() for p in r.text.splitlines() if ':' in p)
#             if len(proxies) >= limit:
#                 break
#         except Exception as e:
#             logger.error(f"Proxy API xatosi: {url}, {e}")
#     logger.info(f"{len(proxies)} ta proxy topildi")
#     return list(proxies)

# def check_proxy(proxy, test_url="https://nomer.beeline.uz", timeout=5):
#     try:
#         resp = requests.get(test_url, proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=timeout)
#         if resp.status_code == 200:
#             logger.info(f"Yaxshi proxy: {proxy}")
#             return proxy
#         return None
#     except Exception:
#         logger.debug(f"Proxy xatosi: {proxy}")
#         return None

# def get_working_proxies(max_proxies=20, workers=30):
#     proxies = fetch_proxies()
#     if not proxies:
#         logger.warning("Proxy topilmadi")
#         return []
#     working = []
#     with ThreadPoolExecutor(max_workers=workers) as executor:
#         results = executor.map(check_proxy, proxies)
#         working = [p for p in results if p]
#         if working:
#             logger.info(f"{len(working)} ta ishlaydigan proxy topildi")
#         return working[:max_proxies]

# def init_db():
#     logger.info("DB initsializatsiyasi")
#     with sqlite3.connect(DB_NAME) as conn:
#         cur = conn.cursor()
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS numbers (
#                 id INTEGER PRIMARY KEY,
#                 phoneNumber TEXT UNIQUE,
#                 warehouse_row_id INTEGER,
#                 regions_id INTEGER,
#                 ctnStatus TEXT,
#                 phoneNumberStatus TEXT,
#                 phoneNumberStatusId INTEGER,
#                 warehouseCode INTEGER,
#                 price INTEGER,
#                 marketCodes TEXT,
#                 warehouse TEXT,
#                 warehouseId INTEGER,
#                 createdAt TEXT,
#                 updatedAt TEXT,
#                 createdBy TEXT,
#                 createdById INTEGER,
#                 modifiedBy TEXT,
#                 modifiedById INTEGER
#             )
#         """)
#         conn.commit()
#     logger.info("DB tayyor")

# def save_to_db(items, warehouse_row_id, regions_id):
#     logger.info(f"DB ga {len(items)} ta yozish boshlandi")
#     with sqlite3.connect(DB_NAME) as conn:
#         cur = conn.cursor()
#         inserted, skipped = 0, 0
#         for item in items:
#             try:
#                 cur.execute("""
#                     INSERT OR IGNORE INTO numbers (
#                         id, phoneNumber, warehouse_row_id, regions_id, ctnStatus, phoneNumberStatus,
#                         phoneNumberStatusId, warehouseCode, price, marketCodes, warehouse, warehouseId,
#                         createdAt, updatedAt, createdBy, createdById, modifiedBy, modifiedById
#                     ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
#                 """, (
#                     item.get("id"), item.get("phoneNumber"), warehouse_row_id, regions_id,
#                     item.get("ctnStatus"), item.get("phoneNumberStatus"), item.get("phoneNumberStatusId"),
#                     item.get("warehouseCode"), item.get("price"),
#                     ",".join(item.get("marketCodes", [])) if item.get("marketCodes") else None,
#                     item.get("warehouse"), item.get("warehouseId"), item.get("createdAt"),
#                     item.get("updatedAt"), item.get("createdBy"), item.get("createdById"),
#                     item.get("modifiedBy"), item.get("modifiedById")
#                 ))
#                 inserted += cur.rowcount
#                 if cur.rowcount == 0:
#                     skipped += 1
#             except Exception as e:
#                 logger.error(f"DB yozish xatosi: {e}")
#         conn.commit()
#     logger.info(f"Yozildi: {inserted}, o'tkazib yuborildi: {skipped}")

# def get_selenium_driver(proxy=None, user_agent=None):
#     logger.info("Selenium drayveri ishga tushmoqda")
#     options = Options()
#     options.add_argument("--headless=new")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     if proxy:
#         options.add_argument(f"--proxy-server={proxy}")
#     if user_agent:
#         options.add_argument(f"--user-agent={user_agent}")
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     logger.info("Drayver tayyor")
#     return driver

# def get_cookies(driver):
#     logger.info("Cookie olish boshlandi")
#     driver.get(SIM_PAGE_URL)
#     time.sleep(3)
#     cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
#     logger.info("Cookie'lar olindi")
#     return cookies

# def get_warehouses():
#     logger.info("Warehouses o'qish")
#     with sqlite3.connect(DB_NAME) as conn:
#         cur = conn.cursor()
#         cur.execute("SELECT id, code, regions_id FROM warehouses")
#         warehouses = [{"row_id": r[0], "code": r[1], "regions_id": r[2]} for r in cur.fetchall()]
#     logger.info(f"{len(warehouses)} ta warehouse topildi")
#     return warehouses

# def main():
#     logger.info("Skript boshlandi")
#     init_db()
#     session = requests.Session()
#     proxies = get_working_proxies()
#     user_agents = USER_AGENTS
#     proxy_idx = 0
#     ua_idx = 0

#     driver = get_selenium_driver(proxies[proxy_idx] if proxies else None, user_agents[ua_idx])
#     cookies = get_cookies(driver)
#     cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
#     driver.quit()
#     logger.info("Selenium drayveri yopildi")

#     warehouses = get_warehouses()
#     if not warehouses:
#         logger.error("Warehouse topilmadi")
#         return

#     for wh in warehouses:
#         warehouse_code = wh["code"]
#         warehouse_row_id = wh["row_id"]
#         regions_id = wh["regions_id"]
#         logger.info(f"Warehouse: code={warehouse_code}, row_id={warehouse_row_id}")

#         page = 1
#         size = 100
#         while True:
#             headers = COMMON_HEADERS.copy()
#             headers["User-Agent"] = user_agents[ua_idx]
#             headers["Cookie"] = cookie_header
#             proxies_dict = {"http": f"http://{proxies[proxy_idx]}", "https": f"http://{proxies[proxy_idx]}"} if proxies else None

#             params = {"page": page, "size": size, "warehouse_code": warehouse_code}
#             logger.info(f"So'rov: page={page}, warehouse_code={warehouse_code}")

#             try:
#                 resp = session.get(API_BASE, params=params, headers=headers, proxies=proxies_dict, timeout=15)
#                 logger.info(f"Status: {resp.status_code}")
#                 if resp.status_code != 200:
#                     logger.warning(f"Xato status: {resp.status_code}")
#                     if resp.status_code == 429:
#                         ua_idx = (ua_idx + 1) % len(user_agents)
#                         proxy_idx = (proxy_idx + 1) % len(proxies) if proxies else 0
#                         logger.info(f"Yangilandi: UA={user_agents[ua_idx]}, Proxy={proxies[proxy_idx] if proxies else 'None'}")
#                         time.sleep(random.uniform(5, 10))
#                         continue
#                     break

#                 data = resp.json()
#                 items = data.get("content", [])
#                 if not items:
#                     logger.info("Ma'lumot topilmadi")
#                     break

#                 save_to_db(items, warehouse_row_id, regions_id)
#                 total_pages = data.get("totalPages", 1)
#                 if page >= total_pages:
#                     logger.info(f"Barcha sahifalar tugadi: {total_pages}")
#                     break
#                 page += 1
#                 time.sleep(random.uniform(3, 7))

#             except Exception as e:
#                 logger.error(f"So'rov xatosi: {e}")
#                 ua_idx = (ua_idx + 1) % len(user_agents)
#                 proxy_idx = (proxy_idx + 1) % len(proxies) if proxies else 0
#                 time.sleep(random.uniform(5, 10))

#     session.close()
#     logger.info("Skript yakunlandi")

# if __name__ == "__main__":
#     main()