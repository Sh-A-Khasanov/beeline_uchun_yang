#!/usr/bin/env python3
# coding: utf-8

"""
Beeline numbers scraper with rotating proxies and rotating User-Agents.
Requirements:
  pip install aiohttp
Usage:
  - Put proxies in proxy.txt (one per line). Format examples:
      http://1.2.3.4:8080
      http://user:pass@1.2.3.4:8080
  - Put DB name in config/config.json as {"db_name": "your.db_name"}
  - Run: python beeline_scraper_with_proxies.py
"""

import aiohttp
import asyncio
import sqlite3
import json
import random
from urllib.parse import urlencode
import time
import os
from aiohttp import ClientTimeout, BasicAuth

# --------- Config load ----------
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config.get("db_name", "hemis_api.db")
URL = "https://nomer.beeline.uz/msapi/web/rms-new/phone-numbers"

# --------- DB init ----------
conn = sqlite3.connect(DB_NAME, check_same_thread=True)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS numbers_esim (
    id INTEGER PRIMARY KEY,
    phoneNumber TEXT UNIQUE,
    name TEXT,
    price REAL,
    cancelDate TEXT,
    code TEXT,
    n1 TEXT,
    n2 TEXT,
    n3 TEXT,
    n4 TEXT,
    n5 TEXT,
    n6 TEXT,
    n7 TEXT
)
""")
conn.commit()

# --------- User agents ----------
USER_AGENTS = [
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
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
]

# --------- Proxy load ----------
PROXY_FILE = "proxy.txt"
WORKING_PROXY_FILE = "working_proxies.txt"

def load_proxies(path=PROXY_FILE):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    return lines

def save_working_proxies(proxies, path=WORKING_PROXY_FILE):
    with open(path, "w", encoding="utf-8") as f:
        for p in proxies:
            f.write(p + "\n")

# --------- Helper: parse proxy for auth ----------
def parse_proxy_auth(proxy_url):
    # returns (proxy, aiohttp.BasicAuth or None)
    # proxy_url may be like http://user:pass@1.2.3.4:8080
    if "@" in proxy_url:
        # split scheme://user:pass@host:port
        try:
            scheme, rest = proxy_url.split("://", 1)
            creds, host = rest.split("@", 1)
            if ":" in creds:
                user, pwd = creds.split(":", 1)
            else:
                user, pwd = creds, ""
            proxy = f"{scheme}://{host}"
            auth = BasicAuth(user, pwd)
            return proxy, auth
        except Exception:
            return proxy_url, None
    return proxy_url, None

# --------- Test proxies concurrently ----------
async def test_single_proxy(session, proxy_raw, sem, test_url="https://httpbin.org/ip"):
    async with sem:
        proxy, proxy_auth = parse_proxy_auth(proxy_raw)
        try:
            timeout = ClientTimeout(total=10)
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            async with session.get(test_url, proxy=proxy, proxy_auth=proxy_auth, timeout=timeout, headers=headers) as resp:
                if resp.status == 200:
                    return proxy_raw
        except Exception:
            return None
    return None

async def filter_working_proxies(proxies, concurrency=20):
    if not proxies:
        return []
    timeout = ClientTimeout(total=12)
    connector = aiohttp.TCPConnector(ssl=False, limit_per_host=concurrency)
    sem = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [asyncio.create_task(test_single_proxy(session, p, sem)) for p in proxies]
        results = await asyncio.gather(*tasks)
    working = [r for r in results if r]
    return working

# --------- Phone split ----------
def split_phone(phone_number: str):
    code = phone_number[:5]   # 99891
    digits = list(phone_number[5:])
    # pad digits to length 7 if shorter
    while len(digits) < 7:
        digits.append(None)
    return code, digits

# --------- Save to DB ----------
def save_to_db(content):
    for item in content:
        phoneNumber = item.get("phoneNumber")
        if not phoneNumber:
            continue
        code, digits = split_phone(phoneNumber)
        values = (
            item.get("id"),
            phoneNumber,
            item.get("name"),
            item.get("price"),
            item.get("cancelDate"),
            code,
            *digits[:7]
        )
        cursor.execute("""
            INSERT OR IGNORE INTO numbers_esim
            (id, phoneNumber, name, price, cancelDate, code,
             n1, n2, n3, n4, n5, n6, n7)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
    conn.commit()


# --------- Fetch with rotating proxy + UA ----------
async def fetch(session, phone, page, proxies):
    params = {
        "phone_number_mask": phone,
        "lang": "uz",
        "page": page,
        "size": 100,
        "include_details": "true"
    }
    url = f"{URL}?{urlencode(params)}"

    # choose random proxy and UA
    proxy_raw = random.choice(proxies) if proxies else None
    proxy, proxy_auth = parse_proxy_auth(proxy_raw) if proxy_raw else (None, None)
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for attempt in range(5):
        try:
            timeout = ClientTimeout(total=30)
            async with session.get(url, headers=headers, proxy=proxy, proxy_auth=proxy_auth, timeout=timeout) as resp:
                status = resp.status
                if status == 429:
                    wait_time = random.uniform(5, 15)
                    print(f"429. IP={proxy_raw} | wait {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    # rotate proxy & UA on 429
                    proxy_raw = random.choice(proxies) if proxies else None
                    proxy, proxy_auth = parse_proxy_auth(proxy_raw) if proxy_raw else (None, None)
                    headers = {"User-Agent": random.choice(USER_AGENTS)}
                    continue
                resp.raise_for_status()
                data = await resp.json()
                print(f"OK: phone={phone} page={page} IP={proxy_raw} UA={headers['User-Agent'][:30]}...")
                return data
        except Exception as e:
            backoff = random.uniform(1.5, 5.0) * (attempt + 1)
            print(f"Request error ({proxy_raw}): {e}. backoff {backoff:.1f}s")
            await asyncio.sleep(backoff)
            # rotate proxy and UA between attempts
            proxy_raw = random.choice(proxies) if proxies else None
            proxy, proxy_auth = parse_proxy_auth(proxy_raw) if proxy_raw else (None, None)
            headers = {"User-Agent": random.choice(USER_AGENTS)}
    return None

# --------- Process single phone ----------
async def process_phone(phone, index, session, proxies):
    # longer pause every 15 requests
    if index % 15 == 0 and index > 0:
        pause = random.uniform(8, 15)
        print(f"{index} requests done. sleeping {pause:.1f}s")
        await asyncio.sleep(pause)

    data = await fetch(session, phone, 0, proxies)
    if not data:
        print(f"No data for {phone} (page 0)")
        return

    content = data.get("data", {}).get("content", [])
    save_to_db(content)

    total_pages = data.get("data", {}).get("totalPages", 1)
    print(f"{phone}: total pages {total_pages}")

    for page in range(1, total_pages):
        data_page = await fetch(session, phone, page, proxies)
        if not data_page:
            print(f"{phone}: page {page} failed")
            continue
        content = data_page.get("data", {}).get("content", [])
        save_to_db(content)
        print(f"{phone}: page {page+1}/{total_pages} saved")
        await asyncio.sleep(random.uniform(2, 6.0))

# --------- Main ----------
async def main():
    # load proxies, test them, keep working ones
    proxies_all = load_proxies()
    print(f"Loaded {len(proxies_all)} proxies from {PROXY_FILE}")

    if proxies_all:
        print("Testing proxies. This may take a while...")
        working = await filter_working_proxies(proxies_all, concurrency=30)
        print(f"Working proxies: {len(working)}")
        save_working_proxies(working)
    else:
        working = []

    # read phones from DB table full_combinations
    cursor.execute("SELECT phonenumber FROM full_combinations")
    rows = cursor.fetchall()
    phones = [r[0] for r in rows]
    print(f"Loaded {len(phones)} phones from DB")

    # session for scraping
    timeout = ClientTimeout(total=40)
    connector = aiohttp.TCPConnector(ssl=False, limit_per_host=50)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for idx, phone in enumerate(phones):
            await process_phone(phone, idx, session, working)
            await asyncio.sleep(random.uniform(2.0, 6.0))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        conn.close()
