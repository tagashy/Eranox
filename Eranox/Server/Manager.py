from queue import Empty

from Eranox.Core.Command import CommandFactory
from Eranox.Core import process_message
from Eranox.Core.mythread import Thread
from Eranox.Server.Protocol.SSL import SocketServer
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
            parser = get_parser_for_client(client)
            try:
                message = client.rcv_queue.get_nowait()
                process_message(message, parser, client)
            except Empty:
                command = CommandFactory.create_command("monitor", print_message)
                client.send(**command.to_dict())
                command = CommandFactory.create_command("ping")
                client.send(**command.to_dict())


def print_message(msg):
    print(msg.to_dict())


if __name__ == '__main__':
    manager = Manager({"bindaddr": "0.0.0.0"}, timing=10)
    anon = manager.authenticator.create_user("ANONYMOUS", "", Role.ANONYMOUS)
    taga = manager.authenticator.create_user("tagashy", "123456", Role.ROOT)
    admin = manager.authenticator.create_user("admin", "admin", Role.ADMIN)
    test = manager.authenticator.create_user("test", "test", Role.USER)
    admin_grp = manager.authenticator.create_group("admin")
    manager.authenticator.add_user_to_group(user=admin, group=admin_grp)
    print(f"groups of user {anon}:{manager.authenticator.get_groups_of_user(anon)}")
    print(f"groups of user {taga}:{manager.authenticator.get_groups_of_user(taga)}")
    print(f"groups of user {admin}:{manager.authenticator.get_groups_of_user(admin)}")
    print(f"groups of user {test}:{manager.authenticator.get_groups_of_user(test)}")
    manager.start()
    import time

    time.sleep(10)
