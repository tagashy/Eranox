import re
import socket
import ssl
from datetime import datetime
from logging import error

from Eranox.Core.AuthenticationProtocol import AuthenticationProtocol, DEFAULT_PROTOCOL
from Eranox.Core.Command import CommandMessage, CommandReplyMessage
from Eranox.Core.Message import Message
from Eranox.Core.Network.SSL import SSL
from Eranox.Core.mythread import Thread
from Eranox.Core.utils import has_parameter
from Eranox.Server.Clients.Client import Client, AuthenticationState
from Eranox.constants import StatusCode, LOGIN
from EranoxAuth import Authenticator, AuthenticationError

MAX_RETRY = 200
AUTHENTICATION_SESSION_KEEP_ALIVE_SECONDS = 2 * 60


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


class TcpClient(Client, SSL, Thread):
    type = "ssl"

    login_regex = re.compile(
        "{\s*[\"\']username[\"\']\s*:\s*[\"\'](\S+)[\"\']\s*,\s*[\"\']password[\"\']\s*:\s*[\"\'](\S+)[\"\']\s*}")

    def __init__(self, hostname, ip, connection: socket.socket, authenticator: Authenticator,
                 banner_flag: str = "Welcome to Eranox server", protocol: AuthenticationProtocol = DEFAULT_PROTOCOL):
        Client.__init__(self, authenticator)
        SSL.__init__(self, connection, protocol)
        Thread.__init__(self)

        self.hostname = hostname
        self.ip = ip
        self.request_login_date = None

    def main(self):

        if self.authentication_state == AuthenticationState.AUTHENTICATED:
            SSL.main(self)
        elif self.authentication_state == AuthenticationState.FAILURE:
            self.stop()
            return
        elif self.authentication_state == AuthenticationState.NOT_AUTHENTICATED:
            self.login()
        elif self.authentication_state == AuthenticationState.PROCESSING_AUTHENTICATION:
            if (datetime.now() - self.request_login_date).total_seconds() < AUTHENTICATION_SESSION_KEEP_ALIVE_SECONDS:
                self.authenticate()
            else:
                self.authentication_state = AuthenticationState.NOT_AUTHENTICATED
        else:
            raise NotImplementedError()

    def end(self):
        self.connection.close()

    def stop(self):
        Thread.stop(self)
        self.authentication_state = AuthenticationState.NOT_AUTHENTICATED

    def authenticate(self):
        if self.protocol == AuthenticationProtocol.PASSWORD or self.protocol == AuthenticationProtocol.SHARED_KEY_PASSWORD:
            self.handle_auth_user_key()
        elif self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE or self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_DOUBLE:
            self.handle_auth_challenge()

    def handle_auth_challenge(self):
        msg = self.read()
        if msg is not None:
            if len(msg.errors) == 0:
                msg: CommandReplyMessage = CommandReplyMessage.from_message(msg)
                datas = msg.result
                if isinstance(datas, dict) and has_parameter(["username", "challenge"], datas):
                    try:
                        username = datas.get("username")
                        content, key = self.authenticator.authenticate_challenge(stage=1, username=username,
                                                                                 challenge=datas.get("challenge"))
                        self.send(StatusCode.AUTHENTICATION_CHALLENGE_STEP_2, content.decode("utf-8"))
                        msg = self.read()
                        datas = msg.message
                        if self.authenticator.authenticate_challenge(stage=3, username=username,
                                                                  challenge=datas, key=key,
                                                                  crypted_password=True if self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_DOUBLE else False):
                            self.authentication_state = AuthenticationState.AUTHENTICATED
                            self.send(**Message(status_code=StatusCode.AUTHENTICATION_SUCCESS,message="SUCESS",errors=[]).to_dict())

                        else:
                            self.authentication_state = AuthenticationState.FAILURE
                            self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR,
                                                errors=["invalid credentials or format"]).to_dict())

                    except AuthenticationError:
                        self.authentication_state = AuthenticationState.FAILURE
                        self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR, message="",
                                            errors=["invalid username or challenge"]).to_dict())
                else:
                    self.authentication_state = AuthenticationState.FAILURE
                    self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR, message="",
                                        errors=["invalid format"]).to_dict())
            else:
                error(msg.errors)

    def handle_auth_user_key(self):
        msg = self.read()
        if len(msg.errors) == 0:
            datas = msg.message
            if isinstance(datas, dict) and "username" in datas and "password" in datas:
                if self.auth_user_key(username=datas.get("username"), key=datas.get("password")):
                    self.send(**Message(status_code=StatusCode.AUTHENTICATION_SUCCESS).to_dict())
                else:
                    self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR,
                                        errors=["invalid credentials or format"]).to_dict())
            else:
                self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR,
                                    errors=["invalid credentials or format"]).to_dict())
        else:
            error(msg.errors)

    def auth_user_key(self, username: str, key: str):
        try:
            self.user = self.authenticator.authenticate_user(username, key,
                                                             crypted_password=False if self.protocol == AuthenticationProtocol.PASSWORD else True)
            self.authentication_state = AuthenticationState.AUTHENTICATED
            return True
        except AuthenticationError:
            self.authentication_state = AuthenticationState.FAILURE
            return False

    def login(self):
        msg = CommandMessage(f"{LOGIN} : {self.protocol.value}")
        self.send(**msg.to_dict())
        self.request_login_date = datetime.now()
        self.authentication_state = AuthenticationState.PROCESSING_AUTHENTICATION


    def get_message(self):
        return self.rcv_queue.get_nowait()

    def send_message(self,msg):
        return self.send(**msg.to_dict())