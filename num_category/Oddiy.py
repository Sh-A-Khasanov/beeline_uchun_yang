import requests
import random
import time

# Bir nechta User-Agent ro‘yxati
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

# Agar sizda proxylar bo‘lsa shu yerga qo‘shasiz
PROXIES = [
    None,  # proxy ishlatmasdan
    # "http://user:pass@ip:port",
    # "http://ip:port",
]

URL = "https://nomer.beeline.uz/msapi/web/rms/phone-numbers/?page=1&size=100&warehouse_code=110&phone_number_mask=9989**101***"

def get_data():
    session = requests
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": random.choice(USER_AGENTS),
    }
    proxy = random.choice(PROXIES)

    try:
        r = session.get(URL, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=15)
        # requests.get("https://www.google.com", timeout=5)  # Oddiy so‘rov bilan sessiyani yangilash
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            print("429 bloklandi. Session yangilanmoqda...")
            # biroz kutib qaytadan urinib ko‘ramiz
            time.sleep(random.uniform(3, 7))
            return get_data()
        else:
            print(f"Xato: {r.status_code}")
            return None
    except Exception as e:
        print("Xatolik:", e)
        return None

if __name__ == "__main__":
    for i in range(100):
        data = get_data()
        if data:
            print(f"+++++++++++++++++++++++ {i}:")
            print("Natija:", data.get("content", [])[0] if "content" in data else data)
        # time.sleep(random.uniform(1, 4))
        # time.sleep(1)  # Har so‘rov orasida 2 soniya kutamiz
