from enum import Enum

from Eranox.Core.mythread import Thread
from EranoxAuth import AuthenticationError, Authenticator


class ClientRole(Enum):
    UNKNOWN = "UNKNOWN"
    AGENT = "AGENT"
    MASTER = "MASTER"
    SYSTEM = "SYSTEM"


class AuthenticationState(Enum):
    NOT_AUTHENTICATED = 0
    WAITING_REPLY = 1
    FAILURE = 2
    AUTHENTICATED = 3


class Client(Thread):
    def __init__(self, authenticator: Authenticator):
        Thread.__init__(self)
        self.user = None
        self.authentication_state = AuthenticationState.NOT_AUTHENTICATED
        self.authenticator = authenticator

    def authenticate(self, username: str, key: str):
        try:
            self.user = self.authenticator.authenticate_user(username, key)
            self.authentication_state = AuthenticationState.AUTHENTICATED
            return True
        except AuthenticationError:
            self.authentication_state = AuthenticationState.FAILURE
            return False

    def execute_order(self, order):
        raise NotImplementedError
