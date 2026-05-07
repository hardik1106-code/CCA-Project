from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import ssl
from concurrent.futures import ThreadPoolExecutor

def get_cert(domain):
    try:
        cert_pem = ssl.get_server_certificate((domain, 443))
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())

        # Full certificate
        certificate = cert.public_bytes(serialization.Encoding.PEM).decode()

        # Public key
        public_key = cert.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        print("Domain:", domain)
        print("Subject:",cert.subject)
        print("Issuer:",cert.issuer)
        print("Valid From:",cert.not_valid_before_utc)
        print("Valid To:", cert.not_valid_after_utc)
        print("Certificate:\n", certificate)
        print("Public Key:\n", public_key)
        print("-" * 50)

    except Exception as e:
        print("Error fetching:", domain)


domains = [
    "cca.gov.in",
    "narl.gov.in",

]

# Run multiple scans simultaneously
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(get_cert, domains)
