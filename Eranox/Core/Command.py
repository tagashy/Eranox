from uuid import uuid4

from Eranox.Core.Message import Message
from Eranox.constants import STATUS_CODE, MESSAGE, ERRORS, COMMAND, RESULT, UUID
from Eranox.constants import StatusCode


class Command(object):
    def __init__(self, command: str):
        self.uuid = uuid4()
        self.command = command

    def to_dict(self):
        return {UUID: str(self.uuid), COMMAND: self.command}


class CommandMessage(Message):
    def __init__(self, command: (str, Command), errors: list = []):
        if isinstance(command, str):
            command = Command(command)
        Message.__init__(self, status_code=StatusCode.COMMAND, message=command.to_dict(), errors=errors)

    @staticmethod
    def from_message(message: Message):
        msg = CommandMessage(message.message.get(COMMAND))
        msg.message[UUID] = message.message.get(UUID)
        return msg

    @property
    def uuid(self):
        return self.message.get(UUID)

    @property
    def command(self):
        return self.message.get(COMMAND)

    def to_dict(self, human_readable: bool = False):
        return {STATUS_CODE: self.status_code_obj if human_readable else self.status_code,
                MESSAGE: {UUID: self.uuid, COMMAND: self.command}, ERRORS: self.errors}


class CommandReplyMessage(Message):
    def __init__(self, uuid: str, result: (dict, str), errors: list = []):
        Message.__init__(self, status_code=StatusCode.COMMAND_REPLY, message={UUID: uuid, RESULT: result},
                         errors=errors)

    @staticmethod
    def from_message(message: Message) -> Message:
        msg = CommandReplyMessage(message.message.get(UUID), message.message.get(RESULT), message.errors)
        msg.message[UUID] = message.message.get(UUID)
        return msg

    @property
    def uuid(self):
        return self.message.get(UUID)

    @property
    def result(self):
        return self.message.get(RESULT)

    def to_dict(self, human_readable: bool = False):
        return {STATUS_CODE: self.status_code_obj if human_readable else self.status_code,
                MESSAGE: {UUID: self.uuid, RESULT: self.result}, ERRORS: self.errors}


def NoneFunc(message) -> None:
    pass


class CommandFactory(object):
    mapping = {}

    @staticmethod
    def create_command(command: str, return_func=NoneFunc, uuid: str = None):
        msg = CommandMessage(command)
        CommandFactory.mapping[str(msg.uuid) if uuid is None else uuid] = return_func
        return msg
