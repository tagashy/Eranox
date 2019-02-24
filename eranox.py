import argparse
from logging import basicConfig, DEBUG

from Eranox.constants import AGENT_ACTION, CLI_ACTION, SERVER_ACTION

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="set the logging to debug", default=False, action="store_true")
subparsers = parser.add_subparsers(help='sub-command help', dest="action")
server = subparsers.add_parser(SERVER_ACTION)
server.add_argument("-c", "--config-file", default="config.yml")
agent = subparsers.add_parser("agent")
agent.add_argument("-c", "--config-file", default="config.yml")

cli = subparsers.add_parser("cli")
args = parser.parse_args()
if args.verbose:
    basicConfig(level=DEBUG)
if args.action == SERVER_ACTION:
    from Eranox.Server.main import Core

    Core(args)
elif args.action == AGENT_ACTION:
    from logging import basicConfig, DEBUG

    basicConfig(level=DEBUG)
    from Eranox.Agent.main import Core

    Core(args)
elif args.action == CLI_ACTION:
    from Eranox.Cli.main import Core

    Core(args)
else:
    raise NotImplementedError()
