import requests

domain = "igod.gov.in"

url = f"https://crt.sh/?q=%25.{domain}&output=json"

response = requests.get(url)
data = response.json()

subdomains = set()

for entry in data:
    names = entry['name_value'].split('\n')
    for name in names:
        if domain in name:
            subdomains.add(name.strip())

print("Discovered Subdomains:\n")

for sub in sorted(subdomains):
    print(sub)
