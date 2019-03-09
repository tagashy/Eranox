from queue import Queue

MAX_RETRY = 200
AUTHENTICATION_SESSION_KEEP_ALIVE_SECONDS = 2 * 60
import json
import socket
import ssl
from json import JSONDecodeError
from logging import debug, warning, error
from queue import Empty
from EranoxAuth.authenticate import encrypt, decrypt
from Eranox.Core.AuthenticationProtocol import AuthenticationProtocol, DEFAULT_PROTOCOL
from Eranox.Core.Message import Message
from Eranox.Core.mythread import Thread
from Eranox.constants import STATUS_CODE, StatusCode, MESSAGE, ERRORS


class SSL(Thread):
    def __init__(self, connection, protocol: AuthenticationProtocol = DEFAULT_PROTOCOL):
        Thread.__init__(self)
        self.connection = connection
        self.connection.setblocking(False)
        self.rcv_queue = Queue()
        self.send_queue = Queue()
        self.protocol = protocol
        self.enc_key = None

    def stop(self):
        self.connection.close()
        exit(1)

    def send(self, status_code: StatusCode, message, errors: list = []):
        status_code = status_code.value if isinstance(status_code, StatusCode) else status_code
        data = {STATUS_CODE: status_code, MESSAGE: message, ERRORS: errors}
        debug(f"send: {data}")
        self.__send(data)

    def __send(self, message: (dict, str), counter: int = 0):
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        elif isinstance(message, Message):
            message = message.to_dict()
        if isinstance(message, dict):
            if isinstance(message.get("message"), Message):
                message["message"] = message.get("message").to_dict()
            errors = message.get("errors")
            for i in range(len(errors)):
                errors[i] = str(errors[i])
        try:
            if self.enc_key is None:
                self.connection.send(json.dumps(message).encode("utf-8"))
            else:
                self.connection.send(encrypt(json.dumps(message), self.enc_key))

        except JSONDecodeError:
            warning(f"send message cannot be dumped !!! class= {message.__class__}")
            if isinstance(message, str):
                if self.enc_key is None:
                    self.connection.send(message.encode("utf-8"))
                else:
                    self.connection.send(encrypt(message.encode("utf-8"), self.enc_key))
        except ssl.SSLWantWriteError:
            if counter < MAX_RETRY:
                self.__send(message, counter + 1)
            else:
                error(f"cannot send {message} because max retry on ssl.WantWrite")
        except ConnectionError as e:
            error(e)
            self.stop()
        except OSError as e:
            error(e)
            self.stop()

    def __read(self):
        data = None
        while data is None:
            try:
                data = self.__read_no_wait()
            except ssl.SSLWantReadError:
                pass
        return data

    def __read_no_wait(self) -> str:
        data = self.connection.read()
        data=data.decode("utf-8")
        if self.enc_key is not None:
            data = decrypt(data, self.enc_key).decode("utf-8")

        debug(f"read: {data}")
        return data

    def read(self, no_wait: bool = False, retry: int = MAX_RETRY) -> Message:
        data = ''
        counter = 0
        while counter < retry:
            if no_wait:
                data += self.__read_no_wait()
            else:
                data += self.__read()
            try:
                res = json.loads(data)
            except JSONDecodeError:
                counter += 1
                continue
            if not isinstance(res, dict):
                raise Exception()
            else:
                return Message(res)

    def write(self, s: (dict, str)):
        if isinstance(s, Message):
            self.send_queue.put(s)
        else:
            try:
                debug(f"write: {s}")
                res = json.dumps(s)
                self.send_queue.put(res.encode("utf-8"))
            except json.JSONDecodeError:
                error(f"data to send are could not been dumped : {s}")

    def get_data(self):
        return self.rcv_queue.get()

    def main(self):
        try:
            data = self.send_queue.get_nowait()
            if isinstance(data, Message):
                self.send(**data.to_dict())
            elif isinstance(data, dict):
                self.send(**data)
            elif isinstance(data, bytes):
                self.__send(data)
            else:
                warning(f"Invalid message {data}")
        except Empty:
            try:
                data = self.read(True)
                if data is not None:
                    self.rcv_queue.put(data)
            except ssl.SSLWantReadError as e:
                pass
            except ssl.SSLError as e:
                error(e)
            except socket.error as e:
                self.stop()
                error(e)
