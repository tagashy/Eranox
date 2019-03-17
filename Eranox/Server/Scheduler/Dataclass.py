from datetime import datetime


class Action(object):
    command: str
    when: datetime
    every_x_seconds: int
    callback: None

    def __init__(self, command: str, when: datetime = None, every_x_seconds: int = None, callback=None):
        assert not (when is None and every_x_seconds is None)
        self.command = command
        self.when = when
        self.every_x_seconds = every_x_seconds
        self.callback = callback
