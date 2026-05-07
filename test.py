from OpenSSL import SSL
import socket

try:
    ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
    sock = socket.socket()
    sock.settimeout(5)
    sock.connect(("google.com", 443))

    conn = SSL.Connection(ctx, sock)
    conn.set_tlsext_host_name(b"google.com")
    conn.set_connect_state()
    conn.do_handshake()

    cert = conn.get_peer_certificate()

    print("CERT OBJECT:", cert)

except Exception as e:
    print("ERROR:", e)