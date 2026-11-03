import os
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

collection = MongoClient(os.getenv("MONGOURL"))["certdb"]["certificates"]


def get_cert(domain, verify=True):
    context = ssl.create_default_context()
    if not verify:  # only used to READ a certificate that failed verification
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((domain, 443), timeout=4) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            return ssock.getpeercert(True)


def fetch_cert(domain):
    verify_error = None
    try:
        try:
            cert_bin = get_cert(domain)
        except ssl.SSLCertVerificationError as e:
            verify_error = e.verify_message  # e.g. "Hostname mismatch ..." or "certificate has expired"
            cert_bin = get_cert(domain, verify=False)

        if not cert_bin:
            raise ValueError("no certificate received")
        cert = x509.load_der_x509_certificate(cert_bin)

        # CA ID = Authority Key Identifier (not every certificate has one)
        ca_id = None
        try:
            ext = cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier)
            if ext.value.key_identifier:
                ca_id = ext.value.key_identifier.hex()
        except x509.ExtensionNotFound:
            pass

        data = {
            "domain": domain,
            "subject": cert.subject.rfc4514_string(),
            "issuer": cert.issuer.rfc4514_string(),
            "valid_from": cert.not_valid_before_utc,
            "valid_to": cert.not_valid_after_utc,
            "certificate": cert.public_bytes(serialization.Encoding.PEM).decode(),
            "public_key": cert.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode(),
            "ca_id": ca_id,
            "verify_error": verify_error,  # None = trusted certificate
            "scanned_at": datetime.now(timezone.utc),
        }

        # upsert: running the script again updates the record, no duplicates
        collection.update_one({"domain": domain}, {"$set": data}, upsert=True)
        print("Stored:", domain, "(not trusted)" if verify_error else "")

    except Exception as e:
        print("Failed:", domain, "-", e)


if __name__ == "__main__":
    collection.create_index("domain", unique=True)

    with open("domains.txt") as f:
        domains = sorted({d.strip().lower() for d in f if d.strip()})

    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(fetch_cert, domains)
