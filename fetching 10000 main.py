import os
import socket
import ssl
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
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


def get_der(domain, verify=True, timeout=8):
    ctx = ssl.create_default_context()
    if not verify:  # we only READ the certificate here, we do not trust it
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((domain, 443), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
            return ssock.getpeercert(True)


def fetch_cert(domain):
    domain = domain.strip().lower()
    verify_error = None
    try:
        try:
            cert_bin = get_der(domain)
        except ssl.SSLCertVerificationError as e:
            # expired / self-signed / wrong hostname: still read and store the certificate
            verify_error = e.verify_message
            cert_bin = get_der(domain, verify=False)

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
            "verify_error": verify_error,  # None = trusted certificate
            "scanned_at": datetime.now(timezone.utc),
        }
        collection.update_one({"domain": domain}, {"$set": data}, upsert=True)
        print("Stored:", domain, f"({verify_error})" if verify_error else "")
        return "stored_unverified" if verify_error else "stored"

    except socket.gaierror:
        print("DNS failed:", domain);               return "dns_failed"
    except (socket.timeout, TimeoutError):
        print("Timeout:", domain);                  return "timeout"
    except ConnectionRefusedError:
        print("Refused (no HTTPS):", domain);       return "refused"
    except ConnectionResetError:
        print("Reset by server:", domain);          return "reset"
    except ssl.SSLError as e:
        print("SSL error:", domain, "->", e.reason); return "ssl_error"
    except OSError as e:
        print("Network error:", domain, "->", e);  return "network_error"
    except Exception as e:
        print("Error fetching:", domain, "->", repr(e)); return "other"


if __name__ == "__main__":
    collection.create_index("domain", unique=True)

    with open("domains.txt") as f:
        domains = [d.strip() for d in f if d.strip()]

    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(fetch_cert, domains))

    print("\n--- Summary ---")
    for status, n in Counter(results).most_common():
        print(f"{status:18} {n}")