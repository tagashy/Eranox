import base64
from uuid import uuid4

from Eranox.Core.Message import Message
from Eranox.constants import STATUS_CODE, MESSAGE, ERRORS, COMMAND, RESULT, UUID, COMPLETE, B64_ENCODED
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
    def __init__(self, uuid: str, result: (dict, str, bytes), complete: bool = True, errors: list = [],
                 b64_encode: bool = None):
        if b64_encode is None:
            b64_encode = False if not isinstance(result, bytes) else True
            result = result if not b64_encode else base64.b64encode(result)
        elif b64_encode and isinstance(result, str):
            result = result.encode("utf-8")
        Message.__init__(self, status_code=StatusCode.COMMAND_REPLY,
                         message={UUID: uuid, RESULT: result, COMPLETE: complete, B64_ENCODED: b64_encode},
                         errors=errors)

    @staticmethod
    def from_message(message: Message) -> Message:
        msg = CommandReplyMessage(message.message.get(UUID), message.message.get(RESULT),
                                  message.message.get(COMPLETE, True), message.errors,
                                  b64_encode=message.message.get(B64_ENCODED))
        return msg

    @property
    def uuid(self):
        return self.message.get(UUID)

    @property
    def result(self):
        return self.message.get(RESULT) if not self.b64_encoded else base64.b64decode(self.message.get(RESULT))

    @property
    def __result(self):
        return self.message.get(RESULT) if not self.b64_encoded else self.message.get(RESULT).decode("utf-8")

    @property
    def complete(self):
        return self.message.get(COMPLETE)

    @property
    def b64_encoded(self):
        return self.message.get(B64_ENCODED, False)

    def to_dict(self, human_readable: bool = False):
        return {STATUS_CODE: self.status_code_obj if human_readable else self.status_code,
                MESSAGE: {UUID: self.uuid, RESULT: self.result if human_readable else self.__result,
                          COMPLETE: self.complete,
                          B64_ENCODED: self.b64_encoded},
                ERRORS: self.errors}


def NoneFunc(message) -> None:
    pass


class CommandFactory(object):
    mapping = {}

    @staticmethod
    def create_command(command: str, return_func=None, uuid: str = None, args: list = [], kwargs: dict = {}):
        if return_func is None:
            return_func = NoneFunc
        msg = CommandMessage(command)
        CommandFactory.mapping[str(msg.uuid) if uuid is None else uuid] = {"func": return_func, "args": args,
                                                                           "kwargs": kwargs}
        return msg
