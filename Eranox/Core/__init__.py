import json
from logging import debug, error

from Eranox.Core.Command import CommandMessage, CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import StatusCode
from Eranox.Server.Actions.commands import get_parser_for_user


def process_message(message: str, authenticator, controller):
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
            parser = get_parser_for_user(controller.user, authenticator)
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