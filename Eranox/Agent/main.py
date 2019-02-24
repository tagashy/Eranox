import json
from logging import debug, error

from ruamel.yaml import YAML

from Eranox.Agent.Actions.commands import init_cmds
from Eranox.Agent.Connections.SSLSocket import SSLController, Controller
from Eranox.Core.Command import CommandMessage
from Eranox.Core.Command import CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import StatusCode

yaml = YAML(typ="safe")


def Core(args):
    config_file = args.config_file
    data = yaml.load(open(config_file))
    password = data.get("password")
    username = data.get("username")
    server_hash = data.get("server_hash")
    cert_path = data.get("cert_path")
    server_addr = data.get("server_addr", '127.0.0.1')
    port = data.get("port", 8443)
    ssl = SSLController(server_addr, port, cert_path, username, password, server_hash, check_hostname=False)
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
        elif msg.status_code == StatusCode.COMMAND_REPLY.value:
            msg = CommandReplyMessage.from_message(msg)
            try:
                CommandFactory.mapping[msg.uuid](msg)
                del CommandFactory.mapping[msg.uuid]
            except Exception as e:
                error(e)
    except json.JSONDecodeError:
        pass


if __name__ == '__main__':
    from logging import DEBUG, basicConfig

    basicConfig(level=DEBUG)
