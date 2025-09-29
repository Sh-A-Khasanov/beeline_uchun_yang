import aiohttp
import asyncio
import sqlite3
import json
import random
import time
from pathlib import Path

# --- sozlamalar ---
file_name = "Bronze"
LOG_FILE = Path(f"{file_name}.log")

PROXIES = []
MAX_TOTAL_CONCURRENCY = 4    # umumiy parallel ishlar
MAX_PER_ROW_CONCURRENCY = 2  # bitta row uchun parallel sahifalar
TCP_CONN_LIMIT = 15

MIN_SLEEP = 0.8   # sekinlashtirish uchun oshirildi
MAX_SLEEP = 2.5

MAX_RETRIES = 6
BACKOFF_BASE = 2.0
BACKOFF_JITTER = 1.0

BASE_URL = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/131.0.0.0 Safari/537.36",
]

# --- DB sozlamalari ---
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

# --- semaforlar ---
sem = asyncio.Semaphore(MAX_TOTAL_CONCURRENCY)
page_sem = asyncio.Semaphore(MAX_PER_ROW_CONCURRENCY)

# global log faylini ochamiz
log_fh = open(LOG_FILE, "w", encoding="utf-8")


def log(msg: str, to_console=True):
    """Loglarni faylga yozish va ixtiyoriy ravishda ekranga chiqarish"""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    log_fh.write(line)
    log_fh.flush()
    if to_console:
        print(line, end="")


def make_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "uz-UZ,uz;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": BASE_URL,
        "Connection": "keep-alive",
    }


def choose_proxy():
    return random.choice(PROXIES) if PROXIES else None


async def fetch_json(session, url, attempt=1):
    proxy = choose_proxy()
    headers = make_headers()
    await asyncio.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))

    try:
        async with sem:
            # --- qo‘shimcha log ---
            log(f"GET {url} (attempt={attempt})")

            async with session.get(url, headers=headers, timeout=30, proxy=proxy) as resp:
                if resp.status == 200:
                    try:
                        return await resp.json()
                    except Exception:
                        return None
                if resp.status == 429 and attempt <= MAX_RETRIES:
                    wait = BACKOFF_BASE ** attempt + random.uniform(0, BACKOFF_JITTER)
                    log(f"429: {wait:.1f}s kutilyapti (attempt={attempt}) URL={url}")
                    await asyncio.sleep(wait)
                    return await fetch_json(session, url, attempt + 1)
                if 500 <= resp.status < 600 and attempt <= MAX_RETRIES:
                    wait = (BACKOFF_BASE ** attempt) / 2 + random.uniform(0, BACKOFF_JITTER)
                    log(f"Server {resp.status}: {wait:.1f}s kutilyapti (attempt={attempt}) URL={url}")
                    await asyncio.sleep(wait)
                    return await fetch_json(session, url, attempt + 1)
                return None
    except Exception as e:
        if attempt <= MAX_RETRIES:
            wait = random.uniform(1, 4)
            log(f"Xato: {e}, {wait:.1f}s kutilyapti (attempt={attempt}) URL={url}")
            await asyncio.sleep(wait)
            return await fetch_json(session, url, attempt + 1)
        return None



async def fetch_page_limited(session, url):
    async with page_sem:
        return await fetch_json(session, url)


def save_to_db(conn, file_name, content, regions_id, warehouse_code):
    cur = conn.cursor()
    for item in content:
        cur.execute(f"""
            INSERT OR REPLACE INTO {file_name} (
                id, phoneNumber, ctnStatus, phoneNumberStatus, phoneNumberStatusId,
                warehouseCode, price, warehouse, warehouseId, createdAt, updatedAt,
                createdBy, createdById, modifiedBy, modifiedById,
                regionId, warehouseCodeInput
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("id"),
            item.get("phoneNumber"),
            item.get("ctnStatus"),
            item.get("phoneNumberStatus"),
            item.get("phoneNumberStatusId"),
            item.get("warehouseCode"),
            item.get("price"),
            item.get("warehouse"),
            item.get("warehouseId"),
            item.get("createdAt"),
            item.get("updatedAt"),
            item.get("createdBy"),
            item.get("createdById"),
            item.get("modifiedBy"),
            item.get("modifiedById"),
            regions_id,
            warehouse_code
        ))
    conn.commit()


async def process_row(session, row):
    row_id = row["id"]
    regions_id = row["regions_id"]
    warehouse_code = row["code"]
    phone_number_mask = row["phonenumber"]

    log(f"=== ID={row_id} Region={regions_id} Warehouse={warehouse_code} Mask={phone_number_mask} ===")

    first_url = f"{BASE_URL}?page=0&size=100&warehouse_code={warehouse_code}&phone_number_mask={phone_number_mask}"
    first_data = await fetch_json(session, first_url)
    if not first_data:
        log("No data")
        return

    conn = sqlite3.connect(DB_NAME)
    save_to_db(conn, file_name, first_data.get("content", []), regions_id, warehouse_code)
    conn.close()

    total_pages = first_data.get("totalPages", 1)
    if not isinstance(total_pages, int) or total_pages < 1:
        total_pages = 1

    for p in range(1, total_pages):
        url = f"{BASE_URL}?page={p}&size=100&warehouse_code={warehouse_code}&phone_number_mask={phone_number_mask}"
        data = await fetch_page_limited(session, url)
        if data:
            conn = sqlite3.connect(DB_NAME)
            save_to_db(conn, file_name, data.get("content", []), regions_id, warehouse_code)
            conn.close()
            log(f"[ID={row_id}] page={p+1} yozildi")
        else:
            log(f"[ID={row_id}] page={p+1} error")

        await asyncio.sleep(random.uniform(1.2, 3.0))  # sekinlashtirish

    await asyncio.sleep(random.uniform(2.0, 4.0))  # row oralig‘ida ham kutish








# --- proxylarni yuklash va tekshirish ---
async def check_proxy(session, proxy: str) -> bool:
    test_url = "https://httpbin.org/ip"
    try:
        async with session.get(test_url, proxy=proxy, timeout=8) as resp:
            if resp.status == 200:
                ip_data = await resp.json()
                log(f"Proxy OK: {proxy} → {ip_data}")
                return True
    except Exception as e:
        log(f"Proxy ERROR: {proxy} ({e})", to_console=False)
    return False


async def load_and_filter_proxies(proxy_file="proxies.txt"):
    global PROXIES
    path = Path(proxy_file)
    if not path.exists():
        log("Proxy fayl topilmadi")
        return

    with open(path, "r", encoding="utf-8") as f:
        raw_proxies = [line.strip() for line in f if line.strip()]

    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_proxy(session, pr) for pr in raw_proxies]
        results = await asyncio.gather(*tasks)

    # ishlaydiganlarni qoldiramiz
    PROXIES = [pr for pr, ok in zip(raw_proxies, results) if ok]

    # faqat ishlaydiganlarni faylga qayta yozamiz
    with open(path, "w", encoding="utf-8") as f:
        for pr in PROXIES:
            f.write(pr + "\n")

    log(f"Ishlaydigan proxylar soni: {len(PROXIES)}")





















async def main():
    await load_and_filter_proxies("proxies.txt")   # proxylarni tekshirish

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, regions_id, code, phonenumber 
        FROM full_combinations 
        WHERE category_name = ?
    """, (file_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    connector = aiohttp.TCPConnector(limit=TCP_CONN_LIMIT, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        for row in rows:
            await process_row(session, row)


if __name__ == "__main__":
    asyncio.run(main())
    log_fh.close()
