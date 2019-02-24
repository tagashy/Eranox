import json
from logging import debug, error

from Eranox.Core.Command import CommandMessage, CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import StatusCode


def process_message(message: str, parser, controller):
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