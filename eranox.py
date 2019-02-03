import argparse

from Eranox.constants import AGENT_ACTION, CLI_ACTION, SERVER_ACTION

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help', dest="action")
server = subparsers.add_parser(SERVER_ACTION)
server.add_argument("--config-file", default="config.yml")
agent = subparsers.add_parser("agent")
cli = subparsers.add_parser("cli")
args = parser.parse_args()

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
