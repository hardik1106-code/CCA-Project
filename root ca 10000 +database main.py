import socket
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.utils import CryptographyDeprecationWarning
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import os


load_dotenv()  # Load environment variables from .env file

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)


# ================= TLS =================
def get_cert_chain(domain):
    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:

                chain = []

                # Try to get full chain (Python 3.11+)
                if hasattr(ssock, "get_verified_chain"):
                    der_chain = ssock.get_verified_chain()
                    for der in der_chain:
                        cert = x509.load_der_x509_certificate(der, default_backend())
                        chain.append(cert)
                else:
                    # fallback: only leaf
                    der_cert = ssock.getpeercert(binary_form=True)
                    if der_cert:
                        cert = x509.load_der_x509_certificate(der_cert, default_backend())
                        chain.append(cert)

                return domain, chain, None

    except Exception as e:
        return domain, None, str(e)


# ================= DOMAIN LOADER =================
def load_domains(file_path="domains.txt"):
    domains = []

    try:
        with open(file_path, "r") as f:
            for line in f:
                domain = line.strip()

                if not domain or domain.startswith("#"):
                    continue

                domain = domain.replace("http://", "").replace("https://", "")
                domain = domain.split("/")[0]

                try:
                    domain = domain.encode("idna").decode("ascii")
                except:
                    continue

                domains.append(domain)

    except FileNotFoundError:
        print("domains.txt not found")
        return []

    return domains


# ================= WORKER =================
def process_domain(domain):
    domain, chain, error = get_cert_chain(domain)

    if error:
        return {
            "domain": domain,
            "error": error,
            "scanned_at": datetime.utcnow()
        }

    if not chain:
        return {
            "domain": domain,
            "error": "No certificate received",
            "scanned_at": datetime.utcnow()
        }

    try:
        leaf = chain[0]

        data = {
            "domain": domain,
            "leaf": {
                "subject": leaf.subject.rfc4514_string(),
                "issuer": leaf.issuer.rfc4514_string()
            },
            "intermediates": [],
            "root": chain[-1].issuer.rfc4514_string(),
            "error": None,
            "scanned_at": datetime.utcnow()
        }

        # Intermediates
        if len(chain) > 1:
            for cert in chain[1:]:
                data["intermediates"].append({
                    "subject": cert.subject.rfc4514_string(),
                    "issuer": cert.issuer.rfc4514_string()
                })

        return data

    except Exception as e:
        return {
            "domain": domain,
            "error": str(e),
            "scanned_at": datetime.utcnow()
        }


# ================= MAIN =================
if __name__ == "__main__":

    # Load domains
    domains = load_domains("domains.txt")
    print(f"Loaded {len(domains)} domains")

    if not domains:
        exit()

    # MongoDB Connection
    MONGO_URL = os.getenv("MONGOURL")
    client = MongoClient(MONGO_URL)
    db = client["cert_scanner"]
    collection = db["certificates"]

    # Create index (avoids duplicates)
    collection.create_index("domain", unique=True)

    MAX_THREADS = 20  # safe + fast

    # 🔹 Threaded scanning
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_domain, d) for d in domains]

        for future in as_completed(futures):
            try:
                result = future.result()

                #  Upsert (insert or update)
                collection.update_one(
                    {"domain": result["domain"]},
                    {"$set": result},
                    upsert=True
                )

                print(f"Stored: {result['domain']}")

            except Exception as e:
                print("THREAD ERROR:", e)