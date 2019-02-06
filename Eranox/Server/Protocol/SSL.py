import socket
import ssl
from queue import Queue
from Eranox.Server.Client import Client
from Eranox.Server.mythread import Thread

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('../data/certificate.crt', '../data/privatekey.key')


class SocketServer(Thread):
    def __init__(self, bindaddr: str = '127.0.0.1', port: int = 8443):
        self.bindaddr = bindaddr
        self.port = port
        self.sock = self.ssock = None
        self.clients = []
        Thread.__init__(self)

    def init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.bind((self.bindaddr, self.port))
        self.sock.listen(5)
        self.ssock = context.wrap_socket(self.sock, server_side=True)

    def main(self):
        conn, addr = self.ssock.accept()
        TcpClient("", addr, conn)


class TcpClient(Client):
    def __init__(self, hostname, ip, connection):
        Client.__init__(self, hostname, ip)
        self.connection = connection
        self.rcv_queue=Queue()
        self.send_queue = Queue()
        self.waiting_reply_queue = Queue()
        self.unknown_packet_queue = Queue()

    def main(self):
        pass



if __name__ == '__main__':
    ss = SocketServer()
    ss.start()
    import time

    time.sleep(200)
