import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime, timedelta


def get_last_saturday():
    today = datetime.today()
    days_since_saturday =(today.weekday() - 5) % 7
    last_saturday =today-timedelta(days=days_since_saturday)
    return last_saturday.strftime("%Y-%m-%d")


def scrape_gov_domains():
    date_str = get_last_saturday()
    url = f"https://subdomainfinder.c99.nl/scans/{date_str}/gov.in"

    print("Fetching:", url)

    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    domains = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if ".gov.in" in href:
            domain = urlparse(href).netloc
            if domain:
                domains.add(domain)

    return list(domains)


domains = scrape_gov_domains()

print("Total domains found:", len(domains))

with open("domains.txt", "w") as f:
    for d in domains:
        f.write(d + "\n")