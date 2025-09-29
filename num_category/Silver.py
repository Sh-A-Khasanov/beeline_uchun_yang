import aiohttp
import asyncio
import sqlite3
import json
import random

# config.json dan DB nomini olish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

# SQLite ulanish
conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT id, code, phonenumber 
    FROM full_combinations 
    WHERE category_name = 'Silver'
""")
rows = cur.fetchall()
cur.close()
conn.close()

BASE_URL = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
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
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",

]

async def fetch_json(session, url, attempt=1, max_retries=5):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 429 and attempt < max_retries:
                wait = random.uniform(5, 12) + attempt
                print(f"429. kutilyapti {wait:.1f}s (attempt {attempt})")
                await asyncio.sleep(wait)
                return await fetch_json(session, url, attempt + 1)
            else:
                print(f"HTTP {resp.status} URL: {url}")
                return None
    except Exception as e:
        if attempt < max_retries:
            await asyncio.sleep(random.uniform(3, 6))
            return await fetch_json(session, url, attempt + 1)
        print(f"RequestException: {e}")
        return None

async def process_row(session, fout, row):
    row_id = row["id"]
    warehouse_code = row["code"]
    phone_number_mask = row["phonenumber"]

    header = f"\n=== ID={row_id} Warehouse={warehouse_code} Mask={phone_number_mask} ===\n"
    fout.write(header)
    print(header.strip())

    # Birinchi sahifa
    first_url = f"{BASE_URL}?page=0&size=100&warehouse_code={warehouse_code}&phone_number_mask={phone_number_mask}"
    first_data = await fetch_json(session, first_url)
    if not first_data:
        fout.write("No data\n")
        return

    fout.write(json.dumps(first_data, ensure_ascii=False, indent=2) + "\n")
    total_pages = first_data.get("totalPages", 1)

    # Qolgan sahifalarni parallel olish
    tasks = []
    for p in range(1, total_pages):
        url = f"{BASE_URL}?page={p}&size=100&warehouse_code={warehouse_code}&phone_number_mask={phone_number_mask}"
        tasks.append(fetch_json(session, url))

    results = await asyncio.gather(*tasks)

    for i, data in enumerate(results, start=1):
        if data:
            fout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            print(f"[ID={row_id}] page={i+1} yozildi")

async def main():
    async with aiohttp.ClientSession() as session:
        with open("results.txt", "a", encoding="utf-8") as fout:
            for row in rows:
                await process_row(session, fout, row)

if __name__ == "__main__":
    asyncio.run(main())




























# import requests
# import random
# import time

# # Bir nechta User-Agent ro‘yxati
# USER_AGENTS = [
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
#     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
#     "Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
#     "Mozilla/5.0 (Linux; Android 15; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Edg/129.0.0.0",
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
#     "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
#     "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
#     "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
#     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
#     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",

# ]

# # Agar sizda proxylar bo‘lsa shu yerga qo‘shasiz
# PROXIES = [
#     None,  # proxy ishlatmasdan
#     # "http://user:pass@ip:port",
#     # "http://ip:port",
# ]

# URL = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/?page=1&size=100&warehouse_code=110&phone_number_mask=9989**101***"

# def get_data():
#     session = requests
#     headers = {
#         "Accept": "application/json, text/plain, */*",
#         "User-Agent": random.choice(USER_AGENTS),
#     }
#     proxy = random.choice(PROXIES)

#     try:
#         r = session.get(URL, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=15)
#         # requests.get("https://www.google.com", timeout=5)  # Oddiy so‘rov bilan sessiyani yangilash
#         if r.status_code == 200:
#             return r.json()
#         elif r.status_code == 429:
#             print("429 bloklandi. Session yangilanmoqda...")
#             # biroz kutib qaytadan urinib ko‘ramiz
#             time.sleep(random.uniform(3, 7))
#             return get_data()
#         else:
#             print(f"Xato: {r.status_code}")
#             return None
#     except Exception as e:
#         print("Xatolik:", e)
#         return None

# if __name__ == "__main__":
#     for i in range(100):
#         data = get_data()
#         if data:
#             print(f"+++++++++++++++++++++++ {i}:")
#             print("Natija:", data.get("content", [])[0] if "content" in data else data)
#         # time.sleep(random.uniform(1, 4))
#         # time.sleep(1)  # Har so‘rov orasida 2 soniya kutamiz
