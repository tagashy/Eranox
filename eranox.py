import argparse
from logging import basicConfig, DEBUG

from Eranox.constants import AGENT_ACTION, CLI_ACTION, SERVER_ACTION

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="set the logging to debug", default=False, action="store_true")
subparsers = parser.add_subparsers(help='sub-command help', dest="action")
server = subparsers.add_parser(SERVER_ACTION)
server.add_argument("-c", "--config-file", default="config.yml")
server.add_argument("-i", "--stdin", default=False, action="store_true", help="enable stdin client on the server")
server.add_argument("-b", "--bind_addr", default=None, help="override config bind_addr")
server.add_argument("--scheduler", default=True, action="store_false", help="deactivate the scheduler")
agent = subparsers.add_parser(AGENT_ACTION)
agent.add_argument("-c", "--config-file", default="config.yml")
agent.add_argument("-i", "--install", default=False, action="store_true", help="register itself")
cli = subparsers.add_parser(CLI_ACTION)
cli.add_argument("-c", "--config-file", default="config.yml")
args = parser.parse_args()
if args.verbose:
    basicConfig(level=DEBUG)
if args.action == SERVER_ACTION:
    from Eranox.Server.main import Core

    Core(args)
elif args.action == AGENT_ACTION:
    from Eranox.Agent.main import Core

    Core(args)
elif args.action == CLI_ACTION:
    from Eranox.Cli.main import Core

    Core(args)
else:
    raise NotImplementedError()
