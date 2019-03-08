import logging
from io import StringIO
from logging import error

from Eranox.Core.Command import CommandMessage, CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import StatusCode


def process_message(msg: Message, manager, controller):
    if msg.status_code == StatusCode.COMMAND.value:
        stream = StringIO()
        logHandler = logging.StreamHandler(stream, )
        logger = logging.getLogger(f"{controller.user}")
        logger.addHandler(logHandler)
        logger.setLevel(logging.ERROR)
        if controller.parser is None:
            controller.set_parser()
        parser = controller.parser

        parser.logger=logger
        msg = CommandMessage.from_message(msg)
        splitted = msg.message.get("command").split()
        try:
            args = parser.parse_args(splitted)
        except SystemExit:
            pass
        errors = stream.getvalue()
        if errors is None or len(errors) == 0:
            args.func(args, msg, controller, manager)
        else:
            controller.write(CommandReplyMessage(msg.uuid, "", errors if isinstance(errors, list) else [errors]))
        del logger
        del stream
    elif msg.status_code == StatusCode.COMMAND_REPLY.value:
        msg = CommandReplyMessage.from_message(msg)
        try:
            CommandFactory.mapping[msg.uuid](msg)
            del CommandFactory.mapping[msg.uuid]
        except Exception as e:
            error(e)
