import os
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import ExtensionOID
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGOURL"))
collection = client["certdb"]["certificates"]


def get_ca_id(pem):
    """Authority Key Identifier (hex) of the issuing CA, or None if the cert has none."""
    cert = x509.load_pem_x509_certificate(pem.encode())
    try:
        ext = cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier)
        return ext.value.key_identifier.hex() if ext.value.key_identifier else None
    except x509.ExtensionNotFound:
        return None


def fetch_cert(domain):
    domain = domain.strip().lower()
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert_bin = ssock.getpeercert(True)

        if cert_bin is None:
            raise ValueError("Certificate not available")

        cert = x509.load_der_x509_certificate(cert_bin, default_backend())
        certificate = cert.public_bytes(serialization.Encoding.PEM).decode()
        public_key = cert.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        data = {
            "domain": domain,
            "subject": str(cert.subject),
            "issuer": str(cert.issuer),
            "valid_from": cert.not_valid_before_utc,
            "valid_to": cert.not_valid_after_utc,
            "certificate": certificate,
            "public_key": public_key,
            "ca_id": get_ca_id(certificate),
            "scanned_at": datetime.now(timezone.utc),
        }

        # upsert: re-running the scan updates the record instead of duplicating it
        collection.update_one({"domain": domain}, {"$set": data}, upsert=True)
        print("Stored:", domain)

    except socket.timeout:
        print("Timeout:", domain)
    except Exception as e:  # print the reason so bugs are not hidden
        print("Error fetching:", domain, "->", repr(e))


if __name__ == "__main__":
    # needs duplicate-free data: run dedupe_certs.py once if the collection already has duplicates
    collection.create_index("domain", unique=True)

    with open("domains.txt") as f:
        domains = [d.strip() for d in f if d.strip()]

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(fetch_cert, domains)
