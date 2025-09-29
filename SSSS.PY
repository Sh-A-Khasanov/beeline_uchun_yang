import requests
import sqlite3
import json
import time
import random

# config.json dan DB nomini olish
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config["db_name"]

# SQLite ulanish
conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# full_combinations jadvalidan code va phonenumber olish
cur.execute("SELECT id, code, phonenumber FROM full_combinations")
rows = cur.fetchall()

BASE_URL = "https://nomer.beeline.uz/msapi/web/rms-new/phone-numbers?phone_number_mask=9989****8008&lang=uz&page=0&size=90&include_details=true"  # oxirida '?' emas

# Katta User-Agent ro'yxati (misol uchun bir necha ta)
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
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

def fetch_json_with_retries(url, max_retries=5):
    """Har urinishda yangi random User-Agent tanlaydi va 429 bo'lsa kutib qayta urinadi."""
    for attempt in range(1, max_retries + 1):
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                wait = random.uniform(5, 12) + attempt  # ortib boruvchi interval
                print(f"429. kutilyapti {wait:.1f}s (attempt {attempt}) UA={headers['User-Agent']}")
                time.sleep(wait)
                continue
            print(f"HTTP {r.status_code} returned. URL: {url}")
            return None
        except requests.RequestException as e:
            wait = random.uniform(3, 6)
            print(f"RequestException: {e}. {wait:.1f}s kutilyapti (attempt {attempt})")
            time.sleep(wait)
    return None

# Faylga append bilan yozamiz
with open("results.txt", "a", encoding="utf-8") as fout:
    for row in rows:
        row_id = row["id"]
        warehouse_code = row["code"]
        phone_number_mask = row["phonenumber"]

        header = f"\n=== ID={row_id} Warehouse={warehouse_code} Mask={phone_number_mask} ===\n"
        print(header.strip())
        fout.write(header)

        # Avval page=None bilan birinchi sahifani olish emas; API 0-based bo'lishi mumkin,
        # shuning uchun page=0 dan boshlaymiz va server javobidagi 'number' va 'totalPages'ni tekshiramiz.
        page = 0
        size = 100

        # Birinchi so'rovni olib totalPages va start index aniqlaymiz
        first_url = f"{BASE_URL}"
        print("Requesting:", first_url)
        fout.write(f"Requesting: {first_url}\n")

        first_data = fetch_json_with_retries(first_url)
        if not first_data:
            fout.write("No data or error on first request.\n")
            print("No data or error on first request.")
            # kichik pauza va keyingi kombinatsiyaga o'tish
            time.sleep(random.uniform(1.5, 3))
            continue

        # first_data dan start va totalPages aniqlash
        start_index = first_data.get("number", 0)
        total_pages = first_data.get("totalPages", 1)

        # Birinchi sahifa natijasini yozish
        fout.write(json.dumps(first_data, ensure_ascii=False, indent=2) + "\n")
        print(f"page={start_index+1} yozildi")

        # Agar total_pages mos kelmasa yoki 1 bo'lsa ham ishlaydi.
        # range(start_index+1, start_index+total_pages) — 0-based API uchun to'g'ri.
        for p in range(start_index + 1, start_index + total_pages):
            url = f"{BASE_URL}"
            print("Requesting:", url)
            fout.write(f"Requesting: {url}\n")

            data = fetch_json_with_retries(url)
            if not data:
                fout.write(f"No data or error on page {p}.\n")
                print(f"No data or error on page {p}. Davom etilyapti.")
                break

            fout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            print(f"page={p+1} yozildi")

            # API ni zo'riqtirmaslik uchun tasodifiy kutish
            time.sleep(random.uniform(1.0, 2.5))

        # kichik pauza keyingi maskga o'tishdan oldin
        time.sleep(random.uniform(2.0, 4.0))

# Resurslarni yopish
cur.close()
conn.close()
print("Barcha tugadi. Natijalar results.txt ga yozildi.")




























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
