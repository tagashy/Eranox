import datetime
from threading import Lock
from typing import List

from Eranox.Core.Command import CommandFactory
from Eranox.Server.Clients.Client import Client, AuthenticationState
from Eranox.Server.Scheduler.Dataclass import Action


class Scheduler(Client):
    def __init__(self, authenticator, username: str = "scheduler"):
        Client.__init__(self, authenticator=authenticator)
        self.__commands: List[Action] = []
        self.__recurrent_command: List[Action] = []
        self.__lock = Lock()
        self.replies = {}
        self.callbacks = {}
        self.user = authenticator.get_user(username)
        self.user.server_hash = self.user.user_hash = None
        self.authentication_state = AuthenticationState.AUTHENTICATED

    def get_commands_to_execute(self, now: datetime.datetime):
        with self.__lock:
            commands = [x for x in self.__commands if x.when < now]
            for x in commands:
                del self.__commands[self.__commands.index(x)]
        return commands

    def get_time_to_sleep(self):
        with self.__lock:
            if len(self.__commands) > 0:
                action = min(self.__commands, key=lambda x: x.when)
                seconds = (action.when - datetime.datetime.now()).total_seconds()
                return seconds if seconds > 0 else 0
        return 1

    def add_command(self, command: str, target: str = None, when: datetime.datetime = None, every_x_seconds: int = None,
                    callback=None):
        if target is not None:
            if target in ["all", "broadcast"]:
                command = f"send_msg -b -c -m '{command}'"
            else:
                command = f"send_msg -t {target} -c -m '{command}'"
        if every_x_seconds is None and when is None:
            raise ValueError()
        elif every_x_seconds is None:
            with self.__lock:
                self.__commands.append(Action(command, when, every_x_seconds, callback))
        elif when is None:
            with self.__lock:
                self.__recurrent_command.append(Action(command, datetime.datetime.now(), every_x_seconds, callback))
        else:
            with self.__lock:
                self.__recurrent_command.append(Action(command, when, every_x_seconds, callback))

    def get_message(self):
        return self.queue.get_nowait()

    def main(self):
        now = datetime.datetime.now()
        commands = self.get_commands_to_execute(now)

        for command in commands:
            msg = CommandFactory.create_command(command.command)
            self.replies[msg.uuid] = command.callback
            self.queue.put(msg)
        with self.__lock:
            for command in self.__recurrent_command:
                if command not in self.__commands:
                    command.when += datetime.timedelta(seconds=command.every_x_seconds)
                    self.__commands.append(command)
        self.timing = self.get_time_to_sleep()

    def remove_command(self, **kwargs):
        def remove_from_actions(action_list, **kwargs):
            rm_commands = []
            for command in action_list:
                for key in kwargs:
                    if hasattr(command, key):
                        if getattr(command, key) == kwargs.get(key):
                            continue
                        else:
                            break
                    else:
                        raise KeyError(key)
                else:
                    rm_commands.append(command)
            for command in rm_commands:
                action_list.remove(command)

        remove_from_actions(self.__commands, **kwargs)
        remove_from_actions(self.__recurrent_command, **kwargs)

    def write(self, msg):
        if msg.uuid in self.replies:
            for uuid in msg.result.values():
                self.callbacks[uuid] = self.replies[msg.uuid]
            if msg.complete:
                del self.replies[msg.uuid]
        elif msg.uuid in self.callbacks:
            self.callbacks[msg.uuid](msg)
        else:
            print(f"No ID for")
            print(msg)
