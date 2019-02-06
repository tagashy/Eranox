import argparse
import keyword
from pprint import pprint
from typing import Set


def init_cmds():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="investigation commands", dest="command")
    Pyexec().add_to_parser(subparsers)
    Pyeval().add_to_parser(subparsers)
    Stop().add_to_parser(subparsers)
    return parser


class Action(object):
    subparser_data = {"args": [], "kwargs": {}}
    arguments = []

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, args, context):
        print("Catching empy run")

    def add_to_parser(self, subparsers):
        n_parser = subparsers.add_parser(*self.subparser_data["args"], **self.subparser_data["kwargs"], )
        for argument in self.arguments:
            n_parser.add_argument(*argument["args"], **argument["kwargs"])
        n_parser.set_defaults(func=self)
        keyword.kwlist.append(self.subparser_data["args"][0])


class Pyexec(Action):
    subparser_data = {"args": ["pyexec"], "kwargs": {"help": "execute a python statement"}}
    arguments = [
        {"args": ["statement"], "kwargs": {"help": "the statement to execute", "nargs": "+"}}
    ]

    def run(self, args, context):
        """
        do the exec func of python (allow to exec code from stdin)
        :param args: the args object returned by parse_args
        :return: None
        """
        query = " ".join(args.statement)
        res = exec(query)
        print(res)


class Pyeval(Action):
    subparser_data = {"args": ["pyeval"], "kwargs": {"help": "evaluate a python statement"}}
    arguments = [
        {"args": ["statement"], "kwargs": {"help": "the statement to execute", "nargs": "+"}}
    ]

    def run(self, args, context):
        """
        do the exec func of python (allow to exec code from stdin)
        :param args: the args object returned by parse_args
        :param context: the context object loaded for investigation (unused)
        :return: None
        """
        query = " ".join(args.statement)
        res = eval(query)
        print(res)


class Stop(Action):
    subparser_data = {"args": ["stop"], "kwargs": {"help": "stop cleanly the program"}}

    def run(self, args, context):
        """
        exit investigation mode
        :param args: the args object returned by parse_args (unused)
        :param context: the context object loaded for investigation
        :return: nothing
        """
        context["stop"] = True

