from uuid import uuid4

from Eranox.Core.Message import Message
from Eranox.constants import StatusCode


class Command(object):
    def __init__(self, command: str):
        self.uuid = uuid4()
        self.command = command

    def to_dict(self):
        return {"uuid": str(self.uuid), "command": self.command}


class CommandMessage(Message):
    def __init__(self, command: (str, Command), errors: list = []):
        if isinstance(command, str):
            command = Command(command)
        Message.__init__(self, status_code=StatusCode.COMMAND, message=command.to_dict(), errors=errors)

    @staticmethod
    def from_message(message: Message) -> Message:
        msg = CommandMessage(message.message.get("command"))
        msg.message["uuid"] = message.message.get("uuid")
        return msg

    @property
    def uuid(self):
        return self.message.get("uuid")


class CommandReplyMessage(Message):
    def __init__(self, uuid: str, result: (dict, str), errors: list = []):
        Message.__init__(self, status_code=StatusCode.COMMAND_REPLY, message={"uuid": uuid, "result": result},
                         errors=errors)

    @staticmethod
    def from_message(message: Message) -> Message:
        msg = CommandReplyMessage(message.message.get("uuid"), message.message.get("result"), message.errors)
        msg.message["uuid"] = message.message.get("uuid")
        return msg

    @property
    def uuid(self):
        return self.message.get("uuid")


def NoneFunc(message):
    pass


class CommandFactory():
    mapping = {}

    @staticmethod
    def create_command(command: str, return_func=NoneFunc):
        msg = CommandMessage(command)
        CommandFactory.mapping[str(msg.uuid)] = return_func
        return msg
