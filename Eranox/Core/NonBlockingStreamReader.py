from threading import Thread

from queue import Queue, Empty
from logging import error

class NonBlockingStreamReader(object):

    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while True:
                data = stream.read()
                if data:
                    for encoding in ["utf-8", "cp850"]:
                        try:
                            data = data.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            error(f"error using decoding codex {encoding} to decode {data} ")
                            continue
                    queue.put(data)
                else:
                    raise UnexpectedEndOfStream

        self._t = Thread(target=_populateQueue,
                         args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def read(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None,
                               timeout=timeout)
        except Empty:
            return None


class UnexpectedEndOfStream(Exception): pass
