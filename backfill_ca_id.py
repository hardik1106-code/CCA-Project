from pathlib import Path
from pymongo import MongoClient
from cryptography import x509
from cryptography.x509.oid import ExtensionOID
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent / ".env"
print(".env path:", env_path, "| exists:", env_path.exists())
load_dotenv(env_path)
print("MONGOURL =", os.getenv("MONGOURL"))

url = os.getenv("MONGOURL")
if not url:
    raise SystemExit("MONGOURL is not set. Check the .env file name, location and variable name.")
print("Connecting to:", url.split("@")[-1])   # hides username/password

client = MongoClient(url, serverSelectionTimeoutMS=8000)
client.admin.command("ping")                  # fails fast if unreachable
print("Connected OK")

col = client["certdb"]["certificates"]
print("Documents in certdb.certificates:", col.count_documents({}))

def get_ca_id(pem):
    cert = x509.load_pem_x509_certificate(pem.encode())
    try:
        ext = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_KEY_IDENTIFIER)
        return ext.value.key_identifier.hex() if ext.value.key_identifier else None
    except x509.ExtensionNotFound:
        return None

updated = 0
for doc in col.find({"ca_id": {"$exists": False}}, {"certificate": 1}):
    if not doc.get("certificate"):
        continue
    col.update_one({"_id": doc["_id"]}, {"$set": {"ca_id": get_ca_id(doc["certificate"])}})
    updated += 1
print("Updated:", updated)