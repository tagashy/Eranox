from enum import Enum

from Eranox.Server.Authentication.Authenticator import Authenticator
from Eranox.Server.mythread import Thread


class ClientRole(Enum):
    UNKNOWN = "UNKNOWN"
    AGENT = "AGENT"
    MASTER = "MASTER"
    SYSTEM = "SYSTEM"


class AuthenticationState(Enum):
    NOT_AUTHENTICATED = 0
    FAILURE = 1
    AUTHENTICATED = 2


class Client(Thread):
    def __init__(self, hostname, ip, authenticator: Authenticator):
        Thread.__init__(self)
        self.role = ClientRole.UNKNOWN
        self.authentication_state = AuthenticationState.NOT_AUTHENTICATED
        self.hostname = hostname
        self.ip = ip
        self.authenticator = authenticator

    def authenticate(self, key):
        if self.authenticator.authenticate_user(self.hostname, key):
            self.authentication_state = AuthenticationState.AUTHENTICATED
        else:
            self.authentication_state = AuthenticationState.FAILURE

    def execute_order(self, order):
        raise NotImplementedError
