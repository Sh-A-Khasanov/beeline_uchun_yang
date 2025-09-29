# proxy_cleaner.py
# Python 3.8+ kerak
# pip install requests

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

PROXY_FILE = "proxy.txt"
BACKUP_FILE = f"proxy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
WORKING_FILE = "working.txt"
DEAD_FILE = "dead.txt"
TEST_URLS = ["http://httpbin.org/ip", "https://httpbin.org/ip"]
TIMEOUT = 8
MAX_WORKERS = 20

def load_proxies(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"{path} topilmadi")
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
    return [l for l in lines if l and not l.startswith("#")]

def test_proxy(proxy: str):
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    for url in TEST_URLS:
        try:
            r = requests.get(url, proxies=proxies, timeout=TIMEOUT)
            if r.status_code == 200:
                return (proxy, True, f"200 {url}")
            else:
                return (proxy, False, f"status {r.status_code} {url}")
        except requests.exceptions.RequestException as e:
            return (proxy, False, f"{type(e).__name__} {e}")
    return (proxy, False, "no response")

def main():
    p_path = Path(PROXY_FILE)
    proxies = load_proxies(p_path)
    if not proxies:
        print("proxy.txt ichida proxy yo'q.")
        return

    # zaxira
    p_path.write_text(p_path.read_text(encoding="utf-8"), encoding="utf-8")  # ensure readable
    Path(BACKUP_FILE).write_text("\n".join(proxies), encoding="utf-8")

    working = []
    dead = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(test_proxy, pr): pr for pr in proxies}
        for fut in as_completed(futures):
            pr = futures[fut]
            try:
                proxy, ok, reason = fut.result()
            except Exception as e:
                proxy, ok, reason = pr, False, f"exception {e}"
            if ok:
                working.append(proxy)
                print(f"[OK]   {proxy} -> {reason}")
            else:
                dead.append(f"{proxy}  # {reason}")
                print(f"[BAD]  {proxy} -> {reason}")

    # ishlaydiganlarni proxy.txt ga qayta yozish (ishlamaydiganlarni o'chiradi)
    Path(PROXY_FILE).write_text("\n".join(working), encoding="utf-8")
    Path(WORKING_FILE).write_text("\n".join(working), encoding="utf-8")
    Path(DEAD_FILE).write_text("\n".join(dead), encoding="utf-8")

    print("")
    print(f"Ishlaydiganlar: {len(working)}. Fayl: {PROXY_FILE} va {WORKING_FILE}")
    # print(f"Ishlamaydiganlar: {len(dead)}. Fayl: {DEAD_FILE}")
    print(f"Original zaxira: {BACKUP_FILE}")

if __name__ == "__main__":
    main()
