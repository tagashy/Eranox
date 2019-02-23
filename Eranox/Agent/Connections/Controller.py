from logging import debug


class Controller(object):
    def __init__(self,username:str,password:str):
        self.__username = username
        self.__password = password

    def write(self, s: (dict, str)):
        debug(f"Base controller write called from {self}")
        print(s)

    def read(self) -> (dict, str):
        debug(f"Base controller read called from {self}")
        return input()

    def authenticate(self, username, password):
        self.write({"username": username, "password": password})

    def login(self):
        self.authenticate(self.__username, self.__password)
