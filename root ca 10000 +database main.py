import os
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from cryptography import x509
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

collection = MongoClient(os.getenv("MONGOURL"))["cert_scanner"]["certificates"]


def get_chain(domain, verify=True):
    """Returns the certificate chain (leaf first). The full chain needs Python 3.13 or newer."""
    context = ssl.create_default_context()
    if not verify:  # only used to READ a chain that failed verification
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((domain, 443), timeout=4) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            if hasattr(ssock, "get_verified_chain"):  # Python 3.13+: full chain
                ders = ssock.get_verified_chain() if verify else ssock.get_unverified_chain()
            else:  # older Python: only the leaf certificate
                ders = [d for d in [ssock.getpeercert(True)] if d]

    return [x509.load_der_x509_certificate(der) for der in ders]


def scan_domain(domain):
    verify_error = None
    try:
        try:
            chain = get_chain(domain)
        except ssl.SSLCertVerificationError as e:
            verify_error = e.verify_message
            chain = get_chain(domain, verify=False)

        if not chain:
            raise ValueError("no certificate received")

        data = {
            "domain": domain,
            "leaf": {
                "subject": chain[0].subject.rfc4514_string(),
                "issuer": chain[0].issuer.rfc4514_string(),
            },
            "intermediates": [
                {"subject": c.subject.rfc4514_string(), "issuer": c.issuer.rfc4514_string()}
                for c in chain[1:]
            ],
            "root": chain[-1].issuer.rfc4514_string(),
            "verify_error": verify_error,
            "error": None,
            "scanned_at": datetime.now(timezone.utc),
        }
    except Exception as e:
        data = {"domain": domain, "error": str(e), "scanned_at": datetime.now(timezone.utc)}

    collection.update_one({"domain": domain}, {"$set": data}, upsert=True)
    print("Stored:", domain, "- error" if data.get("error") else "")


if __name__ == "__main__":
    collection.create_index("domain", unique=True)

    with open("domains.txt") as f:
        domains = sorted({d.strip().lower() for d in f if d.strip()})
    print(f"Loaded {len(domains)} domains")

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(scan_domain, domains)
