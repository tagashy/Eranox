"""import sys
import traceback
from importlib import reload

import Eranox.Agent.Actions.commands as commands

try:
    import readline
except ImportError:
    print("Module readline not available.")
else:
    import rlcompleter

    readline.parse_and_bind("tab: complete")


def investigation_core(context):
    parser = commands.init_cmds()
    while not context.get("stop", False):
        cmd = input("STDIN>")
        if cmd.strip() == "reload":
            reload(commands)
            parser = commands.init_cmds()
        elif cmd.strip() == "help":
            parser.print_help()
        else:
            try:
                args = parser.parse_args(cmd.split())
                args.func(args=args, context=context)
            except SystemExit as e:
                pass
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)


"""


