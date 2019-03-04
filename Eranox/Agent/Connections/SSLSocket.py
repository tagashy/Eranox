import json
import socket
import ssl
from logging import error, debug
from queue import Empty, Queue

from Eranox.Agent.Connections.Controller import Controller
from Eranox.Core.mythread import Thread
from Eranox.Core.Message import Message


class SSLController(Controller, Thread):
    def __init__(self, hostname: str, port: int, certificate_path: str, username: str, password: str,
                 server_hash: str = None, check_hostname: bool = True):
        Controller.__init__(self, username, password, server_hash)
        Thread.__init__(self)
        self.hostname = hostname
        self.port = port
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(certificate_path)
        context.check_hostname = check_hostname
        self.context = context
        self.read_queue = Queue()
        self.sock = None
        self.ssock = None

    def init(self):
        self.sock = socket.create_connection((self.hostname, self.port))
        self.ssock = self.context.wrap_socket(self.sock, server_hostname=self.hostname, )
        self.ssock.setblocking(False)

    def main(self):
        try:
            data = self.queue.get_nowait()
            self.ssock.send(data)
        except Empty:
            try:
                data = self.ssock.read()
                if len(data) > 0:
                    self.read_queue.put(data)
            except ssl.SSLWantReadError:
                pass

    def end(self):
        self.ssock.close()
        self.sock.close()

    def write(self, s: (dict, str)):
        if isinstance(s, Message):
            s = s.to_dict()
        try:
            debug(f"write: {s}")
            res = json.dumps(s)
            self.queue.put(res.encode("utf-8"))
        except json.JSONDecodeError:
            error(f"data to send are could not been dumped : {s}")

    def read_no_wait(self):
        try:
            data = self.read_queue.get_nowait()
            debug(f"read_no_wait: {data}")
            return data
        except Empty:
            return None

    def read(self):
        data = self.read_queue.get()
        debug(f"read: {data}")
        return data


if __name__ == '__main__':
    ssl = SSLController('127.0.0.1', 8443, '../../Server/data/certificate.crt', False)
    hostname = '127.0.0.1'
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations('../../Server/data/certificate.crt')
    context.check_hostname = False

