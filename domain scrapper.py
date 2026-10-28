import re
import requests
from datetime import datetime, timedelta

# Set a specific date as "YYYY-MM-DD", or leave as None for the last Wednesday
SPECIFIC_DATE =None

if SPECIFIC_DATE:
    date_str =SPECIFIC_DATE
else:
    today = datetime.today()
    last_wednesday = today - timedelta(days=(today.weekday() - 2) % 7)
    date_str = last_wednesday.strftime("%Y-%m-%d")

url = f"https://subdomainfinder.c99.nl/scans/{date_str}/gov.in"
print("Fetching:", url)


def find_domains(html):
    return set(re.findall(r"[a-z0-9.-]+\.gov\.in", html.lower()))


# Try 1: plain request (fast, no browser)
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
print("Status:", response.status_code)
domains = find_domains(response.text)

# Try 2: if the list is loaded by JavaScript, use Chrome in the background (no window)
if not domains:
    print("Nothing found with requests, trying hidden Chrome...")
    import time
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(10)
    html = driver.page_source
    driver.quit()
    domains = find_domains(html)

    with open("page_debug.html", "w", encoding="utf-8") as f:
        f.write(html)   # saved so we can inspect it if still 0

print("Total domains found:", len(domains))

with open("domains.txt", "w") as f:
    for d in sorted(domains):
        f.write(d + "\n")