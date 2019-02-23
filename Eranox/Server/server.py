from queue import Empty

from Eranox.Core.mythread import Thread


class Server(Thread):
    def main(self):
        try:
            order=self.queue.get_nowait()
        except Empty:
            pass
