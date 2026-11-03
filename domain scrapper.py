import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URL = "https://subdomainfinder.c99.nl/scans/{date}/gov.in"


def get_domains(driver, date):
    driver.get(URL.format(date=date))
    time.sleep(5)  # wait for the page to load
    found = set()
    for a in driver.find_elements(By.TAG_NAME, "a"):
        host = urlparse(a.get_attribute("href") or "").netloc.lower()
        if host.endswith(".gov.in"):
            found.add(host)
    return found


options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

# c99 may not have a scan for every day, so try the last 14 days until one has domains
new_domains = set()
for i in range(14):
    date = (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
    try:
        new_domains = get_domains(driver, date)
    except Exception as e:
        print(date, "failed:", e)
        continue
    print(date, "->", len(new_domains), "domains")
    if new_domains:
        break
driver.quit()

# never overwrite domains.txt with an empty result
if not new_domains:
    print("No domains found, domains.txt was not changed")
    raise SystemExit

# keep the old domains and add the new ones
try:
    with open("domains.txt") as f:
        old_domains = set(f.read().split())
except FileNotFoundError:
    old_domains = set()

all_domains = old_domains | new_domains
with open("domains.txt", "w") as f:
    f.write("\n".join(sorted(all_domains)) + "\n")

print(f"domains.txt now has {len(all_domains)} domains ({len(all_domains - old_domains)} new)")
