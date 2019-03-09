from Eranox.Agent.Connections.SSLSocket import SSLController
from Eranox.Core.Command import CommandFactory
from Eranox.Core.mythread import Thread
from Eranox.Server.Clients.Client import AuthenticationState
from Eranox.Core.AuthenticationProtocol import AuthenticationProtocol, DEFAULT_PROTOCOL


class STDINClient(Thread):
    type = "stdin"

    def __init__(self, hostname, port, certificate_path, username, password, authenticator, server_hash, check_hostname,
                 protocol: AuthenticationProtocol = DEFAULT_PROTOCOL):
        Thread.__init__(self)
        if username is None:
            username = input("username>")
        if password is None:
            password = input("password>")
        if server_hash is None:
            server_hash = input("server_hash>")
        self.ssl = SSLController(hostname, port, certificate_path, username, password, authenticator, server_hash,
                                 check_hostname, protocol)

    def init(self):
        self.ssl.start()

    def main(self):
        cmd = input("Eranox>")
        self.ssl.write(CommandFactory.create_command(cmd, print))

