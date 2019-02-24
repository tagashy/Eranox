import os
from logging import debug

from Eranox.Core.Command import CommandReplyMessage, CommandFactory
from EranoxAuth.authenticate import encrypt


class Controller(object):
    def __init__(self, username: str, password: str, encryption_key: str = None):
        self.__username = username
        self.__password = password
        self.__encryption_key = encryption_key

    def write(self, s: (dict, str)):
        debug(f"Base controller write called from {self}")
        print(s)

    def read(self) -> (dict, str):
        debug(f"Base controller read called from {self}")
        return input()

    def authenticate(self, uuid, username, password):
        pwd = encrypt(password, self.__encryption_key) if self.__encryption_key else password
        self.write(CommandReplyMessage(uuid=uuid, result={"username": username, "password": pwd}))

    def login(self, uuid):
        self.authenticate(uuid, self.__username, self.__password)

    def register(self):
        user = f"automated_account_{os.urandom(16)}"
        password = os.urandom(32)
        self.__username = user
        self.__password = password
        self.write(CommandFactory.create_command(f"REGISTER -u {user} -p {password}", ))

    def register_stage2(self, msg: CommandReplyMessage):
        self.__encryption_key = msg.message.get("server_hash")

    def get_credentials(self):
        return {"username": self.__username, "password": self.__password, "encryption_key": self.__encryption_key}
