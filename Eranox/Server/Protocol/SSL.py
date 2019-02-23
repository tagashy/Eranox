import json
import re
import socket
import ssl
from json import JSONDecodeError
from logging import debug, warning
from queue import Queue, Empty

from Eranox.Core.mythread import Thread
from Eranox.Server.Client import Client, AuthenticationState
from Eranox.Server.Command import CommandFactory
from Eranox.Server.Message import Message
from Eranox.constants import STATUS_CODE, StatusCode, MESSAGE, ERRORS,LOGIN
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
        self.connection.setblocking(False)
        self.rcv_queue = Queue()
        self.send_queue = Queue()
        self.waiting_reply_queue = Queue()
        self.unknown_packet_queue = Queue()
        self.banner_flag = banner_flag

    def init(self):
        self.__send(self.banner_flag)

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
        try:
            data = self.send_queue.get_nowait()
            if isinstance(data, Message):
                self.send(**data.to_dict())
            elif isinstance(data, dict):
                self.send(**data)
            else:
                warning(f"Invalid message {data}")
        except Empty:
            try:
                data = self.read_no_wait()
                if len(data) > 0:
                    self.rcv_queue.put(data)
            except ssl.SSLWantReadError:
                pass

    def end(self):
        self.connection.close()

    def login(self):
        msg = CommandFactory.create_command(LOGIN)
        self.send(**msg.to_dict())
        try:
            res = json.loads(self.read())
            if isinstance(res, str):
                res = json.loads(res)
        except JSONDecodeError:
            self.authentication_state = AuthenticationState.FAILURE
            self.send(StatusCode.AUTHENTICATION_ERROR, "Authentication failure", errors=["Invalid format"])
            return

        if res is None or "username" not in res or "password" not in res:
            self.authentication_state = AuthenticationState.FAILURE
            self.send(StatusCode.AUTHENTICATION_ERROR, "Authentication failure", errors=["Invalid format"])

            return
        else:
            username = res.get("username")
            password = res.get("password")
        if self.authenticate(username, password):
            self.send(StatusCode.AUTHENTICATION_SUCCESS, "Authentication Success", errors=[])
            return
            self.commands = get_commands_for_user(self.user)
        else:
            self.send(StatusCode.AUTHENTICATION_ERROR, "Authentication failure", errors=["Invalid Credentials"])

    def send(self, status_code: StatusCode, message, errors: list = []):
        status_code = status_code.value if isinstance(status_code, StatusCode) else status_code
        data = {STATUS_CODE: status_code, MESSAGE: message, ERRORS: errors}
        debug(f"send: {data}")
        self.__send(data)

    def __send(self, message: (dict, str)):
        try:
            self.connection.send(json.dumps(message).encode("utf-8"))
        except JSONDecodeError:
            warning(f"send message cannot be dumped !!! class= {message.__class__}")
            if isinstance(message, str):
                self.connection.send(message.encode("utf-8"))

    def read(self):
        data = None
        while data is None:
            try:
                data = self.read_no_wait()
            except ssl.SSLWantReadError:
                pass
        return data

    def read_no_wait(self) -> str:
        data = self.connection.read().decode("utf-8")
        debug(f"read: {data}")
        return data
