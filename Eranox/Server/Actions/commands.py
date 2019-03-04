import argparse
import keyword

import psutil

from Eranox.Core.Command import CommandMessage, CommandReplyMessage


def init_cmds(user, authenticator):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="commands", dest="command")
    Login().add_to_parser(subparsers)
    Pyexec().add_to_parser(subparsers)
    Pyeval().add_to_parser(subparsers)
    Stop().add_to_parser(subparsers)
    Ping().add_to_parser(subparsers)
    Monitor().add_to_parser(subparsers)
    return parser


class Action(object):
    subparser_data = {"args": [], "kwargs": {}}
    arguments = []

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, args, message: CommandMessage, controller):
        controller.write("Catching empty run")

    def add_to_parser(self, subparsers):
        n_parser = subparsers.add_parser(*self.subparser_data["args"], **self.subparser_data["kwargs"], )
        for argument in self.arguments:
            n_parser.add_argument(*argument["args"], **argument["kwargs"])
        n_parser.set_defaults(func=self)
        keyword.kwlist.append(self.subparser_data["args"][0])


class Login(Action):
    permissions = ["root"]

    subparser_data = {"args": ["LOGIN"], "kwargs": {"help": "login the client"}}

    def run(self, args, message: CommandMessage, controller):
        controller.login(message.message.get("uuid"))


class Pyexec(Action):
    subparser_data = {"args": ["pyexec"], "kwargs": {"help": "execute a python statement"}}
    permissions = ["pyexec", "root"]

    def run(self, args, message: CommandMessage, controller):
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
    permissions = ["pyeval", "root"]

    def run(self, args, message: CommandMessage, controller):
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
    permissions = ["stop", "root"]

    def run(self, args, message: CommandMessage, controller):
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

    def run(self, args, message: CommandMessage, controller):
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


class Monitor(Action):
    subparser_data = {"args": ["monitor"], "kwargs": {"help": "return systems information"}}
    permissions = ["ping"]

    def run(self, args, message: CommandMessage, controller):
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
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors)
        controller.write(msg)


class Register(Action):
    subparser_data = {"args": ["REGISTER"], "kwargs": {"help": "register a new account"}}
    arguments = [{"args": ["-u", "--user"], "kwargs": {"help": "the username", "required": True}},
                 {"args": ["-p", "--password"], "kwargs": {"help": "the password", "required": True}}]
    permissions = ["register"]

    def run(self, args, message: CommandMessage, controller):
        """
        return systems information
        :param args: the args object returned by parse_args (unused)
        :param controller: the controller object who called the function
        :return: nothing
        """
        errors = []
        try:
            user = controller.authenticator.create_user(args.user, args.password)
            res = user.get("server_hash")
        except Exception as e:
            errors.append(e)
        controller.write(CommandReplyMessage(message.message.get("uuid"), res, errors))


Actions = [Login, Pyexec, Pyeval, Stop, Ping, Monitor, Register]


def get_parser_for_user(user, authenticator):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="commands", dest="command")
    for action in Actions:
        for permission in action.permissions:
            if authenticator.can_user_do(permission, user):
                action().add_to_parser(subparsers)
    return parser