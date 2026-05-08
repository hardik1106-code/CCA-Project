import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient

# connect to MongoDB
client = MongoClient("mongodb+srv://hardikmalavliya_db_user:hardik1106@cluster0.8s5pnbn.mongodb.net/certdb")
db = client["certdb"]
collection = db["certificates"]


def fetch_cert(domain):
    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert_bin = ssock.getpeercert(True)

        if cert_bin is None:
            raise ValueError("Certificate not available")
        
        cert = x509.load_der_x509_certificate(cert_bin, default_backend())

        # certificate
        certificate = cert.public_bytes(
            serialization.Encoding.PEM
        ).decode()

        # public key
        public_key = cert.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # create document
        data = {
            "domain": domain,
            "subject": str(cert.subject),
            "issuer": str(cert.issuer),
            "valid_from": cert.not_valid_before_utc,
            "valid_to": cert.not_valid_after_utc,
            "certificate": certificate,
            "public_key": public_key
        }

        # insert into MongoDB
        collection.insert_one(data)

        print("Stored:", domain)

    except socket.timeout:
        print("Timeout:", domain)

    except Exception:
        print("Error fetching:", domain)


# read domains
with open("domains.txt") as f:
    domains = [d.strip() for d in f if d.strip()]


# parallel execution
with ThreadPoolExecutor(max_workers=15) as executor:
    executor.map(fetch_cert, domains)