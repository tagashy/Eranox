import argparse
import keyword

from Eranox.Agent.Connections.Controller import Controller
from Eranox.Server.Command import CommandMessage, CommandReplyMessage


def init_cmds():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="investigation commands", dest="command")
    Login().add_to_parser(subparsers)
    Pyexec().add_to_parser(subparsers)
    Pyeval().add_to_parser(subparsers)
    Stop().add_to_parser(subparsers)
    Ping().add_to_parser(subparsers)
    return parser


class Action(object):
    subparser_data = {"args": [], "kwargs": {}}
    arguments = []

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, args, message: CommandMessage, controller: Controller):
        controller.write("Catching empty run")

    def add_to_parser(self, subparsers):
        n_parser = subparsers.add_parser(*self.subparser_data["args"], **self.subparser_data["kwargs"], )
        for argument in self.arguments:
            n_parser.add_argument(*argument["args"], **argument["kwargs"])
        n_parser.set_defaults(func=self)
        keyword.kwlist.append(self.subparser_data["args"][0])


class Login(Action):
    subparser_data = {"args": ["LOGIN"], "kwargs": {"help": "login the client"}}

    def run(self, args, message: CommandMessage, controller: Controller):
        controller.login()


class Pyexec(Action):
    subparser_data = {"args": ["pyexec"], "kwargs": {"help": "execute a python statement"}}

    def run(self, args, message: CommandMessage, controller: Controller):
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
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors)
        controller.write(msg)


class Pyeval(Action):
    subparser_data = {"args": ["pyeval"], "kwargs": {"help": "evaluate a python statement"}}
    arguments = [
        {"args": ["statement"], "kwargs": {"help": "the statement to execute", "nargs": "+"}}
    ]

    def run(self, args, message: CommandMessage, controller: Controller):
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
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors)
        controller.write(msg)


class Stop(Action):
    subparser_data = {"args": ["stop"], "kwargs": {"help": "stop cleanly the program"}}

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        exit investigation mode
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """

        controller["stop"] = True


class Ping(Action):
    subparser_data = {"args": ["ping"], "kwargs": {"help": "reply pong"}}

    def run(self, args, message: CommandMessage, controller: Controller):
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
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors)
        controller.write(msg)
