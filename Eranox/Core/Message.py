from Eranox.constants import STATUS_CODE, MESSAGE, ERRORS
from Eranox.constants import StatusCode


class Message(object):
    def __init__(self, data: dict = None, status_code: StatusCode = None, message: (dict, str) = None,
                 errors: list = None):
        if isinstance(int, StatusCode):
            status_code = StatusCode(status_code)
        if isinstance(data, dict):
            self.status_code = data.get(STATUS_CODE)
            self.message: dict = data.get(MESSAGE)
            self.errors = data.get(ERRORS)
        elif status_code is not None and message is not None and errors is not None:
            self.status_code = status_code
            self.message: dict = message
            self.errors = errors
        else:
            raise TypeError(data.__class__)

        if isinstance(self.status_code, StatusCode):
            self.status_code = self.status_code.value

    @property
    def status_code_obj(self):
        return [x for x in StatusCode if x.value == self.status_code]

    def to_dict(self, human_readable: bool = False):
        return {STATUS_CODE: self.status_code_obj if human_readable else self.status_code, MESSAGE: self.message, ERRORS: self.errors}

    def __str__(self):
        return str(self.to_dict(True))

    def __repr__(self):
        return str(self)


class InvalidMessage(Message):
    def __init__(self, msg: Message, errors: list = []):
        Message.__init__(self, status_code=StatusCode.INVALID_MESSAGE, message=msg, errors=errors)
