import re
import socket
import ssl
from logging import error
from typing import Union

from Eranox.Core.AuthenticationProtocol import AuthenticationProtocol, DEFAULT_PROTOCOL
from Eranox.Core.Command import CommandMessage, CommandReplyMessage
from Eranox.Core.Message import Message
from Eranox.Core.Network.SSL import SSL
from Eranox.Core.mythread import Thread
from Eranox.constants import LOGIN
from Eranox.constants import StatusCode
from EranoxAuth.authenticate import Authenticator
from EranoxAuth.authenticate import encrypt


class SSLController(SSL, Thread):
    def __init__(self, hostname: str, port: int, certificate_path: str, username: str, password: str,
                 authenticator: Authenticator,
                 server_hash: str = None, check_hostname: bool = True,
                 protocol: AuthenticationProtocol = DEFAULT_PROTOCOL):
        self.authenticator = authenticator
        self.__password = password
        self.username = username
        self.server_hash = server_hash
        Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(certificate_path)
        context.check_hostname = check_hostname
        self.context = context
        self.connection = None
        self.protocol = protocol
        self.sock = socket.create_connection((self.hostname, self.port))
        ssock = self.context.wrap_socket(self.sock, server_hostname=self.hostname, )
        SSL.__init__(self, ssock, self.protocol)
        self.auth_version_regex = re.compile(f"{LOGIN} : (\S+)")

    @property
    def user(self):
        return self.username

    def check_protocol_version(self, msg: CommandMessage) -> Union[bool, None]:
        if isinstance(msg.command, str):
            res = self.auth_version_regex.search(msg.command)
            if res is not None:
                if self.protocol.value == res.group(1):
                    return True
                else:
                    return False
        return None

    def init(self):
        stop = False
        while not stop:
            data = self.read()
            msg = CommandMessage.from_message(data)
            res = self.check_protocol_version(msg)
            if res is True:
                if not self.authenticate(msg):
                    self.stop()
                stop = True

            elif res is False:
                self.send_mismatch_version(msg)
                stop = True
                self.stop()
            else:
                pass

    def send_mismatch_version(self, msg: CommandMessage):
        self.send(**CommandReplyMessage(msg.uuid, "", errors=[
            f"Version mismatch. Client only support auth protocol {self.protocol.value}"]).to_dict())

    def handle_auth_user_key(self, msg: CommandMessage):
        self.send(**CommandReplyMessage(msg.uuid, {"username": self.username, "password": self.__password}).to_dict())
        msg = self.read()
        if msg.status_code == StatusCode.AUTHENTICATION_SUCCESS:
            return True
        else:
            error(msg.errors)
            return False

    def authenticate(self, msg: CommandMessage) -> bool:
        if self.protocol == AuthenticationProtocol.PASSWORD or self.protocol == AuthenticationProtocol.SHARED_KEY_PASSWORD:
            return self.handle_auth_user_key(msg)
        elif self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE or self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_DOUBLE or self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_KEEP_ENCRYPTED:
            return self.handle_auth_challenge(msg)

    def handle_auth_challenge(self, msg: CommandMessage):
        enc_key=None
        challenge, key = self.authenticator.authenticate_challenge(0, server_hash=self.server_hash)
        self.send(**CommandReplyMessage(msg.uuid,
                                        {"username": self.username, "challenge": challenge.decode("utf-8")}).to_dict())
        msg = self.read()
        if len(msg.errors) == 0 and msg.status_code == StatusCode.AUTHENTICATION_CHALLENGE_STEP_2.value:
            if self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE_DOUBLE:
                password = encrypt(self.__password, self.server_hash)
                content = self.authenticator.authenticate_challenge(2, decryption_key=key, password=password,
                                                                    challenge=msg.message, keep_encrypt=False)

            elif self.protocol == AuthenticationProtocol.SHARED_KEY_BASED_CHALLENGE:
                password = self.__password
                content = self.authenticator.authenticate_challenge(2, decryption_key=key, password=password,
                                                                    challenge=msg.message, keep_encrypt=False)
            else:
                password = self.__password
                content, enc_key = self.authenticator.authenticate_challenge(2, decryption_key=key, password=password,
                                                                         challenge=msg.message, keep_encrypt=True)
            msg = Message(status_code=StatusCode.AUTHENTICATION_CHALLENGE_STEP_2, message=content.decode("utf-8"),
                          errors=[])
            self.send(**msg.to_dict())
            self.enc_key = enc_key

            msg = self.read()
            if msg.status_code == StatusCode.AUTHENTICATION_SUCCESS.value:
                return True
            else:
                error(msg.errors)
                return False
        else:
            error(msg.errors)

    def end(self):
        self.connection.close()
        self.sock.close()


if __name__ == '__main__':
    ssl = SSLController('127.0.0.1', 8443, '../../Server/data/certificate.crt', False)
    hostname = '127.0.0.1'
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations('../../Server/data/certificate.crt')
    context.check_hostname = False
