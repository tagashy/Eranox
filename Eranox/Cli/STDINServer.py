from Eranox.Core.Command import CommandFactory
from Eranox.Core.mythread import Thread
from Eranox.Server.Clients.Client import Client, AuthenticationState


class STDINClient(Client, Thread):
    type = "stdin"

    def __init__(self, authenticator):
        Client.__init__(self, authenticator)
        Thread.__init__(self)

    def init(self):
        self.authenticate()

    def authenticate(self):
        username = input("username:")
        password = input("password")
        self.user = self.authenticator.authenticate_user(username, password, False)
        self.authentication_state = AuthenticationState.AUTHENTICATED

    def main(self):
        cmd = input("Eranox>")
        self.queue.put(CommandFactory.create_command(cmd, print))

    def get_message(self):
        return self.queue.get_nowait()

    def send_message(self, msg):
        print(msg)

    def write(self, msg):
        print(msg)
