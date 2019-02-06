#  coding: utf8
from __future__ import unicode_literals

try:
    import Queue
except ModuleNotFoundError:
    import queue as Queue
import threading
import time


class Thread(threading.Thread):
    """
    override of threading.Thread to offer a stop mechanism, a queue from default a
    """

    def __init__(self, timing=0):
        threading.Thread.__init__(self)
        self.started = False
        self.error = None
        self.pause = False
        self._stop = threading.Event()
        self.queue = Queue.Queue()
        self.timing = timing

    def stop(self):
        """
        tell the thread to stop when he finish his current job

        :return: Nothing what did you expect
        """
        self._stop.set()

    @property
    def stopped(self):
        """
        check if the bot has been stopped

        :return: is the bot stopped
        """
        return self._stop.isSet()

    def end(self):
        """
        method call when bot end

        :return: Nothing what did you expect
        """
        print("ENDING")
        exit(0)

    def init(self):
        """
        method called before entering main loop, allow to make initialisation of stuff

        :return: Nothing what did you expect
        """
        pass

    def run(self):
        """
        main loop of thread,will exec init, then run main in loop until the thread is stopped, then it called end

        :return: Nothing what did you expect
        """
        self.init()
        self.started = True
        while not self.stopped:
            self.main()
            time.sleep(self.timing)
        self.end()

    def main(self):
        """
        main loop

        :return: Nothing what did you expect
        """
        pass
