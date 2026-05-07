import socket
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.utils import CryptographyDeprecationWarning
import sys

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)


# ================= TLS =================
def get_cert_chain(domain):
    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:

                chain = []

                #  Try to get full chain
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
        return f"{domain} -> {error}"

    if not chain:
        return f"{domain} -> No certificate received"

    try:
        result = [f"\n#### {domain} ####"]

        #  Leaf
        leaf = chain[0]
        result.append("\nLeaf Certificate:")
        result.append(f"Subject: {leaf.subject.rfc4514_string()}")
        result.append(f"Issuer : {leaf.issuer.rfc4514_string()}")

        #  Intermediate(s)
        if len(chain) > 1:
            for i, cert in enumerate(chain[1:], start=1):
                result.append(f"\nIntermediate {i}:")
                result.append(f"Subject: {cert.subject.rfc4514_string()}")
                result.append(f"Issuer : {cert.issuer.rfc4514_string()}")
        else:
            result.append("\nIntermediate: Not provided by server")

        #  Root (derived)
        result.append("\nRoot CA (from last issuer):")
        result.append(chain[-1].issuer.rfc4514_string())

        return "\n".join(result)

    except Exception as e:
        return f"{domain} processing error: {e}"


# ================= MAIN =================
if __name__ == "__main__":

    domains = load_domains("domains.txt")
    print(f"Loaded {len(domains)} domains")

    if not domains:
        exit()

    MAX_THREADS = 20  # safe + fast

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_domain, d) for d in domains]

        for future in as_completed(futures):
            try:
                print(future.result())
            except Exception as e:
                print("THREAD ERROR:", e)