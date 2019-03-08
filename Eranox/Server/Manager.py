from queue import Empty
from typing import List

from Eranox.Core import process_message
from Eranox.Core.Command import CommandFactory
from Eranox.Core.Message import InvalidMessage, Message
from Eranox.Core.mythread import Thread
from Eranox.Server.Clients.Client import Client
from Eranox.Server.Clients.SSL import SocketServer, AuthenticationState
from EranoxAuth import Authenticator, Engine, DefaultEngine, DEFAULT_ENGINE_PATH


class Manager(Thread):
    def __init__(self, config: dict, authenticator: type = Authenticator,
                 engine: Engine = DefaultEngine(DEFAULT_ENGINE_PATH), *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        cert_path = config.get("cert_path", "data/certificate.crt")
        private_key_path = config.get("private_key_path", "data/privatekey.key")
        bindaddr: str = config.get("bindaddr", "127.0.0.1")
        port: int = config.get("port", 8443)
        auth = authenticator(engine)
        self.authenticator = auth
        self.socket_server = SocketServer(cert_path=cert_path, private_key_path=private_key_path, authenticator=auth,
                                          bindaddr=bindaddr, port=port)
        self.other_clients = []
        self.waiting_commands = {}

    def init(self):
        self.socket_server.start()

    def main(self):
        new_client = []
        for client in self.clients:
            if client.authentication_state == AuthenticationState.AUTHENTICATED:
                try:
                    message: Message = client.get_message()
                    try:
                        process_message(message, self, client)
                    except Exception as e:
                        client.send_message(InvalidMessage(message, errors=[e]))
                except Empty:
                    if client.type == "ssl":
                        command = CommandFactory.create_command("monitor", print_message)
                        client.send_message(command)
                        command = CommandFactory.create_command("ping")
                        client.send_message(command)

    @property
    def clients(self):
        clients: List[Client] = []
        for client in self.socket_server.clients:
            clients.append(client)
        for client in self.other_clients:
            clients.append(client)
        return clients

    def add_client(self, client: Client):
        if isinstance(client, Client):
            self.other_clients.append(client)
        else:
            raise TypeError(client)


def print_message(msg):
    print(msg)


if __name__ == '__main__':
    manager = Manager({"bindaddr": "0.0.0.0"},timing=10)
    test = manager.authenticator.get_user("test")
    msg, rnd = manager.authenticator.authenticate_challenge(0, server_hash=test.server_hash)
    msg2, key = manager.authenticator.authenticate_challenge(1, username=test.name, challenge=msg)
    msg3 = manager.authenticator.authenticate_challenge(2, decryption_key=rnd, password="test", challenge=msg2)
    result = manager.authenticator.authenticate_challenge(3, username=test.name, challenge=msg3, key=key,
                                                          crypted_password=False)
    from Eranox.Server.Clients.STDIN import STDINClient

    manager.authenticator.create_permission("test", user=test )
    stdin = STDINClient(manager.authenticator)
    print(result)
    manager.start()
    manager.add_client(stdin)
    stdin.start()
    import time

    time.sleep(10)
