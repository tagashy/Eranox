import json
import re
import socket
import ssl
from datetime import datetime
from json import JSONDecodeError
from logging import debug, warning, error
from queue import Queue, Empty
from typing import Union, List

from Eranox.Core.AuthenticationProtocol import AuthenticationProtocol, DEFAULT_PROTOCOL
from Eranox.Core.Command import CommandMessage
from Eranox.Core.Message import Message
from Eranox.Core.mythread import Thread
from Eranox.Server.Client import Client, AuthenticationState
from Eranox.constants import STATUS_CODE, StatusCode, MESSAGE, ERRORS, LOGIN
from EranoxAuth import Authenticator, AuthenticationError

MAX_RETRY = 200
AUTHENTICATION_SESSION_KEEP_ALIVE_SECONDS = 2 * 60


def has_parameter(parameter: Union[str, List[str]], kwargs: dict):
    if isinstance(parameter, str):
        if parameter in kwargs:
            return True
        else:
            return False
    elif isinstance(parameter, list):
        for param in parameter:
            if not has_parameter(param, kwargs):
                return False
        else:
            return True
    else:
        raise NotImplementedError()


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
                 banner_flag: str = "Welcome to Eranox server", protocol: AuthenticationProtocol = DEFAULT_PROTOCOL):
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
        self.request_login_date = None
        self.protocol = protocol

    def init(self):
        self.__send(self.banner_flag)

    def main(self):

        if self.authentication_state == AuthenticationState.AUTHENTICATED:
            self.authenticated_main()
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
            except ssl.SSLWantReadError as e:
                pass
            except ssl.SSLError as e:
                error(e)
            except socket.error as e:
                self.stop()
                error(e)

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
        if len(msg.errors) == 0:
            datas = msg.message
            if isinstance(datas, dict) and has_parameter(["username", "challenge"], datas):
                try:
                    username = datas.get("username")
                    msg, key = self.authenticator.authenticate_challenge(stage=1, username=username,
                                                                         challenge=datas.get("challenge"))
                    self.send(StatusCode.AUTHENTICATION_CHALLENGE_STEP_2, msg)
                    msg = self.read()
                    datas = msg.message
                    if isinstance(datas, dict) and has_parameter(["challenge"], datas):
                        self.authenticator.authenticate_challenge(stage=3, username=username,
                                                                  challenge=datas.get("challenge"), key=key,
                                                                  crypted_password=True if AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_DOUBLE else False)
                    else:
                        self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR, message="",
                                            errors=["invalid format"]).to_dict())
                except AuthenticationError:
                    self.send(**Message(status_code=StatusCode.AUTHENTICATION_ERROR, message="",
                                        errors=["invalid username or challenge"]).to_dict())
            else:
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
        msg = CommandMessage(f"{LOGIN} : {self.protocol}")
        self.send(**msg.to_dict())
        self.request_login_date = datetime.now()
        self.authentication_state = AuthenticationState.PROCESSING_AUTHENTICATION

    def send(self, status_code: StatusCode, message, errors: list = []):
        status_code = status_code.value if isinstance(status_code, StatusCode) else status_code
        data = {STATUS_CODE: status_code, MESSAGE: message, ERRORS: errors}
        debug(f"send: {data}")
        self.__send(data)

    def __send(self, message: (dict, str), counter: int = 0):
        try:
            self.connection.send(json.dumps(message).encode("utf-8"))
        except JSONDecodeError:
            warning(f"send message cannot be dumped !!! class= {message.__class__}")
            if isinstance(message, str):
                self.connection.send(message.encode("utf-8"))
        except ssl.SSLWantWriteError:
            if counter < MAX_RETRY:
                self.__send(message, counter + 1)
            else:
                error(f"cannot send {message} because max retry on ssl.WantWrite")
        except ConnectionError:
            self.stop()
        except OSError:
            self.stop()

    def __read(self):
        data = None
        while data is None:
            try:
                data = self.read_no_wait()
            except ssl.SSLWantReadError:
                pass
        return data

    def __read_no_wait(self) -> str:
        data = self.connection.read().decode("utf-8")
        debug(f"read: {data}")
        return data

    def read(self, no_wait: bool = False, retry: int = MAX_RETRY) -> Message:
        data = ''
        counter = 0
        while counter < retry:
            if no_wait:
                data += self.__read_no_wait()
            else:
                data += self.__read()
            try:
                res = json.loads(data)
            except JSONDecodeError:
                counter += 1
                continue
            if not isinstance(res, dict):
                raise Exception()
            else:
                return Message(res)

    def write(self, s: (dict, str)):
        if isinstance(s, Message):
            s = s.to_dict()
        try:
            debug(f"write: {s}")
            res = json.dumps(s)
            self.send_queue.put(res.encode("utf-8"))
        except json.JSONDecodeError:
            error(f"data to send are could not been dumped : {s}")
