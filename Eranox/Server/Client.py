from enum import Enum
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
    def __init__(self, hostname,ip):
        Thread.__init__(self)
        self.role = ClientRole.UNKNOWN
        self.authentication_state = AuthenticationState.NOT_AUTHENTICATED
        self.hostname = hostname
        self.ip=ip

    def authenticate(self,key):
        raise NotImplementedError

    def execute_order(self,order):
        raise NotImplementedError
