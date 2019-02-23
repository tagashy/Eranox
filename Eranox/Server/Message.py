from Eranox.constants import STATUS_CODE, StatusCode, MESSAGE, ERRORS


class Message(object):
    def __init__(self, data: dict = None, status_code: StatusCode = None, message: (dict, str) = None,
                 errors: list = None):
        if isinstance(data, dict):
            self.status_code = data.get(STATUS_CODE)
            self.message = data.get(MESSAGE)
            self.errors = data.get(ERRORS)
        elif status_code is not None and message is not None and errors is not None:
            self.status_code = status_code
            self.message = message
            self.errors = errors
        else:
            raise TypeError(data.__class__)

        if isinstance(self.status_code, StatusCode):
            self.status_code = self.status_code.value

    @property
    def status_code_obj(self):
        return [x for x in StatusCode if x.value == self.status_code]

    def to_dict(self):
        return {STATUS_CODE: self.status_code, MESSAGE: self.message, ERRORS: self.errors}



