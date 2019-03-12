import argparse
from typing import Optional, IO

from Eranox.Agent.Actions.StorageCommands import Mount, GetFile,WriteFile,ListFile,ListStorage
from Eranox.Agent.Actions.Subprocess import Subprocess
from Eranox.Agent.Actions.commands import Pyexec, Pyeval, Stop, Ping, Monitor, System


class ArgparseLogger(argparse.ArgumentParser):
    def __init__(self, logger, *args, **kwargs):
        argparse.ArgumentParser.__init__(self, *args, **kwargs)
        self.logger = logger

    def error(self, message):
        self.logger.error(message)

    def _print_message(self, message: str, file: Optional[IO[str]] = ...):
        self.logger.error(message)


def init_cmds(logger):
    parser = ArgparseLogger(logger=logger)
    subparsers = parser.add_subparsers(help="commands", dest="command")
    Pyexec().add_to_parser(subparsers,logger)
    Pyeval().add_to_parser(subparsers,logger)
    Stop().add_to_parser(subparsers,logger)
    Ping().add_to_parser(subparsers,logger)
    Monitor().add_to_parser(subparsers,logger)
    System().add_to_parser(subparsers,logger)
    Subprocess().add_to_parser(subparsers,logger)
    Mount().add_to_parser(subparsers,logger)
    GetFile().add_to_parser(subparsers,logger)
    WriteFile().add_to_parser(subparsers,logger)
    ListFile().add_to_parser(subparsers,logger)
    ListStorage().add_to_parser(subparsers,logger)

    return parser
