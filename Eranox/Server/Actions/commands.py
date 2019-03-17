import argparse
import keyword
from pprint import pformat
from typing import Optional, IO

import psutil

from Eranox.Core.Command import CommandMessage, CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import ROOT, ADMIN


class Action(object):
    subparser_data = {"args": [], "kwargs": {}}
    arguments = []

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, args, message: CommandMessage, controller, manager):
        controller.write("Catching empty run")

    def add_to_parser(self, subparsers, logger):
        n_parser = subparsers.add_parser(logger=logger, *self.subparser_data["args"], **self.subparser_data["kwargs"], )
        for argument in self.arguments:
            n_parser.add_argument(*argument["args"], **argument["kwargs"])
        n_parser.set_defaults(func=self)
        keyword.kwlist.append(self.subparser_data["args"][0])


class Pyexec(Action):
    subparser_data = {"args": ["pyexec"], "kwargs": {"help": "execute a python statement"}}
    permissions = ["pyexec", ROOT]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        do the exec func of python (allow to exec code from stdin)
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return:
        """
        query = " ".join(args.statement)
        res = None
        errors = []
        try:
            res = exec(query)
        except Exception as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class Pyeval(Action):
    subparser_data = {"args": ["pyeval"], "kwargs": {"help": "evaluate a python statement"}}
    arguments = [
        {"args": ["statement"], "kwargs": {"help": "the statement to execute", "nargs": "+"}}
    ]
    permissions = ["pyeval", ROOT]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        do the exec func of python (allow to exec code from stdin)
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """
        query = " ".join(args.statement)
        res = None
        errors = []
        try:
            res = eval(query)
        except Exception as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class Stop(Action):
    subparser_data = {"args": ["stop"], "kwargs": {"help": "stop cleanly the program"}}
    permissions = ["stop", ROOT]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        exit investigation mode
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """

        controller["stop"] = True


class Ping(Action):
    subparser_data = {"args": ["ping"], "kwargs": {"help": "reply pong"}}
    permissions = ["ping"]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        return PONG
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """
        res = None
        errors = []
        try:
            res = "PONG"
        except Exception as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class Monitor(Action):
    subparser_data = {"args": ["monitor"], "kwargs": {"help": "return systems information"}}
    permissions = ["ping"]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        return systems information
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """
        res = {}
        errors = []
        try:
            res["cpu_logical"] = psutil.cpu_count()
            res["cpu_physical"] = psutil.cpu_count(False)
            res["cpu_freq"] = psutil.cpu_freq()
            res["cpu_percent"] = psutil.cpu_percent()
            res["virtual_memory"] = str(dict(psutil.virtual_memory()))
        except Exception as e:
            errors = [str(e)]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class Register(Action):
    subparser_data = {"args": ["REGISTER"], "kwargs": {"help": "register a new account"}}
    arguments = [{"args": ["-u", "--user"], "kwargs": {"help": "the username", "required": True}},
                 {"args": ["-p", "--password"], "kwargs": {"help": "the password", "required": True}}]
    permissions = ["register"]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        return systems information
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """
        errors = []
        res = ""
        try:
            user = controller.authenticator.create_user(args.user, args.password)
            res = user.get("server_hash")
        except Exception as e:
            errors.append(e)
        controller.write(CommandReplyMessage(message.message.get("uuid"), res, errors=errors))


class ListClient(Action):
    subparser_data = {"args": ["list_client"], "kwargs": {"help": "list client connected to the server="}}
    permissions = [ADMIN, ROOT, "test"]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        return systems information
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """
        errors = []
        res = ""
        try:
            res = pformat(manager.clients, 4)
        except Exception as e:
            errors.append(e)
        controller.write(CommandReplyMessage(message.message.get("uuid"), res, errors=errors))


class SendCommandToClient(Action):
    subparser_data = {"args": ["send_msg"], "kwargs": {"help": "send a message to another client"}}
    arguments = [
        {"args": ["-m", "--message"], "kwargs": {"help": "the password", "required": True}},
        {"args": ["-t", "--targets"],
         "kwargs": {"help": "the client to send the message to", "default": [], "nargs": "+"}},
        {"args": ["-b", "--broadcast"],
         "kwargs": {"help": "the client to send all client", "default": False, "action": "store_true"}},
        {"args": ["-c", "--command"],
         "kwargs": {"help": "send the message as a command and redirect output to this session", "default": False,
                    "action": "store_true"}},
        {"args": ["-r", "--raw"], "kwargs": {"help": "send the message as it is", "default": False,
                                             "action": "store_true"}},
        {"args": ["-B", "--by"],
         "kwargs": {"help": "change the search of client type (don't touch if you don't understand what you're doing)",
                    "default": "name", }}

    ]
    permissions = [ADMIN, ROOT, "test", "scheduler"]

    def run(self, args, message: CommandMessage, controller, manager):
        """
        return systems information
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """
        if args.command:
            msg = CommandFactory.create_command(args.message, controller.write)
        elif args.raw:
            msg = args.message
        else:
            msg = Message()
        if args.broadcast:
            clients = manager.clients
        elif len(args.targets) > 0:
            clients = []
            for client in args.targets:
                clients.append(manager.get_client(args.by, client))
        else:
            controller.write(CommandReplyMessage(message.uuid, "no targets specified", errors=["invalid targets"]))
            return

        if len(clients) < 1:
            controller.write(CommandReplyMessage(message.uuid, "no clients found", errors=["invalid targets"]))
        else:
            for client in clients:
                client.send_message(msg)
                controller.write(CommandReplyMessage(message.uuid, {client: msg.uuid}, False))
            controller.write(CommandReplyMessage(message.uuid, f"all message are send"))


Actions = [Pyexec, Pyeval, Stop, Ping, Monitor, Register, ListClient, SendCommandToClient]


class ArgparseLogger(argparse.ArgumentParser):
    def __init__(self, logger=None, *args, **kwargs):
        argparse.ArgumentParser.__init__(self, *args, **kwargs)
        self.logger = logger

    def error(self, message):
        self.logger.error(message)

    def _print_message(self, message: str, file: Optional[IO[str]] = ...):
        self.logger.error(message)


def get_parser_for_user(user, authenticator, logger):
    parser = ArgparseLogger(logger)
    subparsers = parser.add_subparsers(help="commands", dest="command")
    if user is None:
        raise Exception("user is None")
    for action in Actions:
        for permission in action.permissions:
            if authenticator.can_user_do(permission, user):
                action().add_to_parser(subparsers, logger)
    return parser
