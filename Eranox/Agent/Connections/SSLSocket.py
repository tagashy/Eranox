import socket
import ssl

hostname = '127.0.0.1'
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.load_verify_locations('../../Server/data/certificate.crt')
context.check_hostname=False
with socket.create_connection((hostname, 8443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname,) as ssock:
        print(ssock.version())