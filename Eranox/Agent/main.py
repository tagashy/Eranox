import json
from logging import debug

from ruamel.yaml import YAML

from Eranox.Agent.Actions.commands import init_cmds
from Eranox.Agent.Connections.SSLSocket import SSLController, Controller
from Eranox.Server.Command import CommandMessage
from Eranox.Server.Message import Message
from Eranox.constants import StatusCode

yaml = YAML(typ="safe")


def Core(args):
    config_file = args.config_file
    data = yaml.load(open(config_file))
    password = data.get("password")
    username = data.get("username")
    cert_path = data.get("cert_path")
    ssl = SSLController('127.0.0.1', 8443, cert_path, username, password, False)
    ssl.start()
    parser = init_cmds()
    while True:
        message = ssl.read_no_wait()
        if message is not None:
            process_message(message, parser, ssl)


def process_message(message: str, parser, controller: Controller):
    if isinstance(message, bytes):
        message = message.decode()
    try:
        res = json.loads(message)
        try:
            msg = Message(res)
        except TypeError as e:
            debug(e)
            print(res)
            return
        if msg.status_code == StatusCode.COMMAND.value:
            msg = CommandMessage.from_message(msg)
            args = parser.parse_args(msg.message.get("command").split())
            args.func(args, msg, controller)
    except json.JSONDecodeError:
        pass


if __name__ == '__main__':
    from logging import DEBUG, basicConfig

    basicConfig(level=DEBUG)
