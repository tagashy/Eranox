import json
from logging import error
from queue import Empty

from Eranox.Core.mythread import Thread
from Eranox.Server.Command import CommandReplyMessage, CommandFactory
from Eranox.Server.Message import Message, StatusCode
from Eranox.Server.Protocol.SSL import SocketServer
from EranoxAuth import Authenticator, Engine, DefaultEngine, DEFAULT_ENGINE_PATH, Role


class Manager(Thread):
    def __init__(self, config: dict, authenticator: type = Authenticator,
                 engine: Engine = DefaultEngine(DEFAULT_ENGINE_PATH), *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        cert_path = config.get("cert_path", "data/certificate.crt")
        private_key_path = config.get("private_key_path", "data/privatekey.key")
        auth = authenticator(engine)
        self.authenticator = auth
        self.socket_server = SocketServer(cert_path=cert_path, private_key_path=private_key_path, authenticator=auth)
        self.waiting_commands = {}

    def init(self):
        self.socket_server.start()

    def main(self):
        new_client = []
        for client in self.socket_server.clients:
            try:
                message = client.rcv_queue.get_nowait()
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    continue
                msg = Message(message)
                if msg.status_code == StatusCode.COMMAND_REPLY.value:
                    msg = CommandReplyMessage.from_message(msg)
                    try:
                        CommandFactory.mapping[msg.uuid](msg)
                        del CommandFactory.mapping[msg.uuid]
                    except Exception as e:
                        error(e)
            except Empty:
                command = CommandFactory.create_command("monitor", print_message)
                client.send(**command.to_dict())
                command = CommandFactory.create_command("ping")
                client.send(**command.to_dict())


def print_message(msg):
    print(msg.to_dict())


if __name__ == '__main__':
    manager = Manager({}, timing=10)
    manager.authenticator.create_user("ANONYMOUS", "", Role.ANONYMOUS)
    manager.authenticator.create_user("tagashy", "123456", Role.ROOT)
    manager.authenticator.create_user("admin", "admin", Role.ADMIN)
    manager.authenticator.create_user("test", "test", Role.USER)
    manager.start()
    import time

    time.sleep(10)
