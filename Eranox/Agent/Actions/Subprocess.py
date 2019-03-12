import subprocess
import uuid
from threading import Lock
from typing import Dict, Callable

from Eranox.Agent.Actions.commands import Action
from Eranox.Agent.Connections.Controller import Controller
from Eranox.Core.Command import CommandMessage, CommandReplyMessage
from Eranox.Core.NonBlockingStreamReader import NonBlockingStreamReader
from Eranox.Core.mythread import Thread


class Activity(object):
    def __init__(self, process: subprocess.Popen, write: Callable[[str, bool], None] = None,
                 read: Callable[[], str] = None):
        self.process = process
        self.stdout = NonBlockingStreamReader(process.stdout)
        self.stderr = NonBlockingStreamReader(process.stderr)
        self.write = write
        self.read = read


class ActivityProcessor(Thread):
    activities: Dict[uuid.UUID, Activity] = {}
    acc_lock = Lock()

    @staticmethod
    def add_activity_to_monitor(activity):
        with ActivityProcessor.acc_lock:
            uid = uuid.uuid4()
            if uid not in ActivityProcessor.activities:
                ActivityProcessor.activities[uid] = activity
                return uid
            else:
                return ActivityProcessor.add_activity_to_monitor(activity)

    def send_input(self, uid, msg):
        if uid not in ActivityProcessor.activities:
            return None
        else:
            ActivityProcessor.activities[uid].process.stdin.write(msg)

    def main(self):
        new_activities = {}
        with ActivityProcessor.acc_lock:
            for uid, activity in ActivityProcessor.activities.items():
                poll_res = activity.process.poll()
                if poll_res is None:  # process running
                    if activity.write is not None and activity.process.stdout is not None:
                        data = activity.stdout.read()
                        data = data if data is not None else activity.stderr.read()
                        if data is not None:
                            activity.write(data, [], False)
                    new_activities[uid] = activity
                else:
                    if activity.write is not None and activity.process.stdout is not None:
                        data = True
                        while data:
                            data = activity.stdout.read()
                            data = data if data is not None else activity.stderr.read()
                            if data is not None:
                                activity.write(data, [], False)
                    activity.write(poll_res, [], True)
            ActivityProcessor.activities = new_activities


class Subprocess(Action):
    subparser_data = {"args": ["exec"], "kwargs": {"help": "execute a program and "}}
    arguments = [
        {"args": ["statement"], "kwargs": {"help": "the statement to execute", "nargs": "+"}},
        {"args": ["-i"],
         "kwargs": {"dest": "stdin", "help": "keep stdin open for incoming message", "action": "store_true",
                    "default": False}},
        {"args": ["-o"],
         "kwargs": {"dest": "stdout", "help": "keep stdout open to redirect output to you", "action": "store_true",
                    "default": False}},
        {"args": ["-pt"], "kwargs": {"help": "indicate the processor timing (dev feature)", "type": int}},
    ]
    __processor = None

    @staticmethod
    def check_processor(timing: int = 10):
        if Subprocess.__processor is None:
            Subprocess.__processor = ActivityProcessor(timing=timing)
            Subprocess.__processor.start()
        return Subprocess.__processor

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        do the exec func of python (allow to exec code from stdin)
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """
        self.check_processor()
        res = None
        errors = []
        write = lambda res, errors, finished: controller.write(
            CommandReplyMessage(message.message.get("uuid"), res, finished, errors=errors))
        if args.stdin:
            stdin = subprocess.PIPE
            read = lambda: controller.read()
        else:
            read = None
            stdin = None
        if args.stdout:
            stdout = subprocess.PIPE
        else:
            stdout = None
        try:
            process = subprocess.Popen(args.statement, stdin=stdin, stdout=stdout, stderr=stdout)
            ActivityProcessor.add_activity_to_monitor(Activity(process, write, read))
            res = "process created"
        except BaseException as e:
            errors = [e]
        write(res, errors, False)
