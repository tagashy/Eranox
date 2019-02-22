import re
import select
import socket
import ssl
from logging import debug
from queue import Queue

from Eranox.Server.Client import Client, AuthenticationState
from Eranox.Server.mythread import Thread
from EranoxAuth import Authenticator


class SocketServer(Thread):
    def __init__(self, cert_path: str = '../data/certificate.crt', private_key_path='../data/privatekey.key',
                 bindaddr: str = '127.0.0.1', port: int = 8443, authenticator: Authenticator = Authenticator()):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(cert_path, private_key_path)
        self.authenticator = authenticator
        self.bindaddr = bindaddr
        self.port = port
        self.sock = self.ssock = None
        self.clients = []
        Thread.__init__(self)

    def init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.bind((self.bindaddr, self.port))
        self.sock.listen(5)
        self.ssock = self.context.wrap_socket(self.sock, server_side=True)

    def main(self):
        conn, addr = self.ssock.accept()
        client = TcpClient("", addr, conn, self.authenticator)
        self.clients.append(client)
        client.start()


class TcpClient(Client):
    login_regex = re.compile(
        "{\s*[\"\']username[\"\']\s*:\s*[\"\'](\S+)[\"\']\s*,\s*[\"\']password[\"\']\s*:\s*[\"\'](\S+)[\"\']\s*}")

    def __init__(self, hostname, ip, connection: socket.socket, authenticator: Authenticator,
                 banner_flag: str = "Welcome to Eranox server"):
        Client.__init__(self, authenticator)
        self.hostname = hostname
        self.ip = ip
        self.connection = connection
        self.rcv_queue = Queue()
        self.send_queue = Queue()
        self.waiting_reply_queue = Queue()
        self.unknown_packet_queue = Queue()
        self.banner_flag = banner_flag

    def init(self):
        self.send(self.banner_flag)

    def main(self):
        if self.authentication_state == AuthenticationState.NOT_AUTHENTICATED:
            self.login()
        elif self.authentication_state == AuthenticationState.FAILURE:
            self.stop()
            return
        elif self.authentication_state == AuthenticationState.AUTHENTICATED:
            self.authenticated_main()
        else:
            raise NotImplementedError()

    def authenticated_main(self):
        readable, writable, exceptional = select.select([self.connection], [], [])

    def end(self):
        self.connection.close()

    def login(self):
        self.send("Credentials?\r\n")
        res = self.login_regex.search(self.read())
        if res is None:
            self.send("Invalid format")
            return
        else:
            username, password = res.groups()
        if self.authenticate(username, password):
            self.send("Authentication Success")
        else:
            self.send("authentication failure")

    def send(self, message: str):
        debug(message)
        self.connection.send(message.encode("utf-8"))

    def read(self) -> str:
        data = self.connection.read().decode("utf-8")
        debug(data)
        return data
