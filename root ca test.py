import socket
from OpenSSL import SSL, crypto
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import certifi
import warnings
from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

def resolve_domain(domain):
    try:
        return socket.getaddrinfo(domain, 443)
    except socket.gaierror as e:
        raise Exception(f"DNS resolution failed: {e}")


def get_cert_chain(domain):
    sock = socket.create_connection((domain, 443))

    context = SSL.Context(SSL.TLS_CLIENT_METHOD)
    context.set_verify(SSL.VERIFY_NONE, lambda *args: True)

    conn = SSL.Connection(context, sock)
    conn.set_tlsext_host_name(domain.encode())
    conn.set_connect_state()
    conn.do_handshake()

    cert_chain = conn.get_peer_cert_chain()

    parsed_chain = []

    for cert in cert_chain:
        cert_der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
        parsed = x509.load_der_x509_certificate(cert_der, default_backend())
        parsed_chain.append(parsed)

    conn.close()
    sock.close()

    return parsed_chain

def load_domains(file_path="domains.txt"):
    domains = []
    with open(file_path, "r") as f:
        for line in f:
            domain = line.strip()

            if not domain or domain.startswith("#"):
                continue

            # Remove protocol if present
            domain = domain.replace("http://", "").replace("https://", "")

            # Remove paths
            domain = domain.split("/")[0]

            domains.append(domain)

    return domains


# Load Mozilla CA bundle
def load_root_store():
    roots = []

    with open(certifi.where(), "rb") as f:
        data = f.read()

    for cert in data.split(b"-----END CERTIFICATE-----"):
        if b"-----BEGIN CERTIFICATE-----" in cert:
            cert += b"-----END CERTIFICATE-----"
            parsed = x509.load_pem_x509_certificate(cert, default_backend())
            roots.append(parsed)

    return roots


# Find Root CA from trust store
def find_root_ca(intermediate, root_store):
    for root in root_store:
        if intermediate.issuer == root.subject:
            return root
    return None


# ===================== MAIN =====================

domains = load_domains("domains.txt")

root_store = load_root_store()

for domain in domains:
    print(f"\n\n#### {domain} ####\n")

    try:
        chain = get_cert_chain(domain)

        print("Certificate Chain:\n")
        for i, cert in enumerate(chain):
            print(f"{i+1}. Subject: {cert.subject.rfc4514_string()}")
            print(f"   Issuer : {cert.issuer.rfc4514_string()}\n")

        # Identify Leaf and Intermediate
        leaf = chain[0]
        intermediate = chain[-1]

        # Find Root CA
        root = find_root_ca(intermediate, root_store)

        print("========== FINAL RESULT ==========\n")

        print("Leaf Certificate:")
        print(leaf.subject.rfc4514_string())

        print("\nIntermediate Certificate:")
        print(intermediate.subject.rfc4514_string())

        if root:
            print("\nRoot CA:")
            print(root.subject.rfc4514_string())
        else:
            print("\nRoot CA not found in trust store")

    except Exception as e:
        print(f" Skipping {domain}: {e}")
    continue