from logging import basicConfig, DEBUG

from Eranox.Core.Command import CommandMessage, Command
from Eranox.Server.Protocol.SSL import SocketServer
from EranoxAuth import Authenticator, Role, DefaultEngine

if __name__ == '__main__':
    basicConfig(level=DEBUG)
    auth = Authenticator(DefaultEngine("sqlite:///eranox.db"))
    auth.create_user("ANONYMOUS", "", Role.ANONYMOUS)
    auth.create_user("tagashy", "123456", Role.ROOT)
    auth.create_user("admin", "admin", Role.ADMIN)
    auth.create_user("test", "test", Role.USER)

    ss = SocketServer(cert_path="Eranox/Server/data/certificate.crt",
                      private_key_path="Eranox/Server/data/privatekey.key", authenticator=auth)
    ss.start()
    import time

    time.sleep(10)
    ss.clients[0].send_queue.put(CommandMessage(Command("ping")))
    ss.clients[0].send_queue.put(CommandMessage(Command("pyeval 1+1")))
    ss.clients[0].send_queue.put(CommandMessage(Command("ping")))

    time.sleep(200)

    import socket
    import ssl

    hostname = '127.0.0.1'
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations('Eranox/Server/data/certificate.crt')
    context.check_hostname = False
    with socket.create_connection((hostname, 8443)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname, ) as ssock:
            print(ssock.version())
            print(ssock.read())
            print(ssock.read())
            print(ssock.send('{"username":"toto","password":"123456"}'.encode("utf-8")))
            print(ssock.read())
