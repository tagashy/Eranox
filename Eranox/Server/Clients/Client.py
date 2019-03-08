from enum import Enum

from Eranox.Core.mythread import Thread
from Eranox.Server.Actions.commands import get_parser_for_user
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
    type = "default"

    def __init__(self, authenticator: Authenticator):
        Thread.__init__(self)
        self.user = None
        self.authentication_state = AuthenticationState.NOT_AUTHENTICATED
        self.authenticator = authenticator
        self.parser = None

    def get_message(self):
        pass

    def send_message(self, msg):
        pass

    def authenticate(self):
        pass

    def set_parser(self,logger):
        self.parser = get_parser_for_user(self.user, self.authenticator,logger)
