from enum import Enum

from Eranox.Core.mythread import Thread
from EranoxAuth import Authenticator


class ClientRole(Enum):
    UNKNOWN = "UNKNOWN"
    AGENT = "AGENT"
    MASTER = "MASTER"
    SYSTEM = "SYSTEM"


class AuthenticationState(Enum):
    NOT_AUTHENTICATED = 0
    PROCESSING_AUTHENTICATION = 1
    FAILURE = 2
    AUTHENTICATED = 3


class Client(Thread):
    def __init__(self, authenticator: Authenticator):
        Thread.__init__(self)
        self.user = None
        self.authentication_state = AuthenticationState.NOT_AUTHENTICATED
        self.authenticator = authenticator

    def authenticate(self):
        pass
