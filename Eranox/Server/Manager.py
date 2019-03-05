from queue import Empty

from Eranox.Core import process_message
from Eranox.Core.Command import CommandFactory
from Eranox.Core.mythread import Thread
from Eranox.Server.Actions.commands import get_parser_for_user
from Eranox.Server.Protocol.SSL import SocketServer, AuthenticationState
from EranoxAuth import Authenticator, Engine, DefaultEngine, DEFAULT_ENGINE_PATH, Role


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
        self.waiting_commands = {}

    def init(self):
        self.socket_server.start()

    def main(self):
        new_client = []
        for client in self.socket_server.clients:
            if client.authentication_state == AuthenticationState.AUTHENTICATED:
                try:
                    message = client.rcv_queue.get_nowait()
                    process_message(message, self.authenticator, client)
                except Empty:
                    command = CommandFactory.create_command("monitor", print_message)
                    client.send(**command.to_dict())
                    command = CommandFactory.create_command("ping")
                    client.send(**command.to_dict())


def print_message(msg):
    print(msg.to_dict())


if __name__ == '__main__':
    manager = Manager({"bindaddr": "0.0.0.0"}, timing=10)
    test=manager.authenticator.get_user("test")
    msg, rnd = manager.authenticator.authenticate_challenge(0, server_hash=test.server_hash)
    msg2, key = manager.authenticator.authenticate_challenge(1, username=test.name, challenge=msg)
    msg3 = manager.authenticator.authenticate_challenge(2, decryption_key=rnd, password="test", challenge=msg2)
    result = manager.authenticator.authenticate_challenge(3, username=test.name, challenge=msg3,key=key,crypted_password=False)
    print(result)
    manager.start()
    import time

    time.sleep(10)
