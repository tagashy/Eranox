import logging
from io import StringIO
from logging import error
from shlex import split

from Eranox.Core.Command import CommandMessage, CommandReplyMessage, CommandFactory
from Eranox.Core.Message import Message
from Eranox.constants import StatusCode


def process_message(msg: Message, controller, **kwargs):
    if msg.status_code == StatusCode.COMMAND.value:
        stream = StringIO()
        logHandler = logging.StreamHandler(stream, )
        logger = logging.getLogger(f"{controller.user}")
        logger.addHandler(logHandler)
        logger.setLevel(logging.ERROR)
        if kwargs.get("parser") is None:
            if controller.parser is None:
                if hasattr(controller, "set_parser"):
                    controller.set_parser(logger)
                else:
                    print("controllers hqs no set_parser")
            parser = controller.parser
        else:
            if "init_cmds" in kwargs:
                parser = kwargs.get("init_cmds")(logger)
            else:
                parser = kwargs.get("parser")
                parser.logger = logger
        msg = CommandMessage.from_message(msg)
        try:
            args = parser.parse_args(split(msg.message.get("command")))
        except SystemExit as e:
            pass
        except TypeError as e:
            pass
        errors = stream.getvalue()
        if errors is None or len(errors) == 0 or errors == "":
            manager = kwargs.get("manager")
            if manager is not None:
                args.func(args, msg, controller, manager)
            else:
                args.func(args, msg, controller)
        else:
            controller.write(CommandReplyMessage(msg.uuid, "", errors=errors if isinstance(errors, list) else [errors]))
    elif msg.status_code == StatusCode.COMMAND_REPLY.value:
        msg = CommandReplyMessage.from_message(msg)
        try:
            cmd = CommandFactory.mapping[msg.uuid]
            cmd.get('func')(*cmd.get("args", []), msg=msg, **cmd.get("kwargs", {}))
            if msg.complete:
                del CommandFactory.mapping[msg.uuid]
        except Exception as e:
            error(e)
    elif msg.status_code == StatusCode.INVALID_MESSAGE.value:
        error("invalid message")
        for m_error in msg.errors:
            error(m_error)
