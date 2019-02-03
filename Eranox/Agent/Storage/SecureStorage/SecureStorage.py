import uuid
from logging import warning
from typing import Tuple
from typing import Union, Optional
import os
from ruamel.yaml import YAML

from Eranox.Agent.Storage import Storage
from Eranox.Agent.Storage.SecureStorage.SecureFile import SecureFile
from Eranox.constants import SECURE_STORAGE_MASTERTABLE_PATH

yaml = YAML()


class SecureStorage(Storage):
    def __init__(self, masterkey, mastertable_path: str = SECURE_STORAGE_MASTERTABLE_PATH):
        if len(masterkey) != 32:
            warning(f"masterkew should have a lengh of 32")
            if len(masterkey) < 32:
                masterkey += "0" * (32 - len(masterkey))
        self.masterpath = mastertable_path
        self.masterkey = masterkey

    def __get_keys(self, path) -> (Tuple[str, str], None):
        mastertable = SecureFile(self.masterkey[0:16], self.masterkey[16:32], self.masterpath, "r")
        data = yaml.load(mastertable.file)
        if path in data:
            return data[path]

    def __add_key(self, path):
        if self.exist(self.masterpath):
            mastertable = SecureFile(self.masterkey[0:16], self.masterkey[16:32], self.masterpath, "r")
            data = yaml.load(mastertable.file)
            if data is None:
                data={}
        else:
            data = {}
        data[path] = (str(uuid.uuid4())[0:16], str(uuid.uuid4())[0:16])
        mastertable = SecureFile(self.masterkey[0:16], self.masterkey[16:32], self.masterpath, "w")
        yaml.dump(data, mastertable.file)
        return data[path]

    def open(self, file, mode: str = "r", *args, **kwargs):
        if "r" in mode:
            data = self.__get_keys(file)
            if data is None:
                raise FileNotFoundError(file)
            else:
                return SecureFile(data[0], data[1], file, mode)
        else:
            data = self.__add_key(file)
            return SecureFile(data[0], data[1], file, mode)



if __name__ == '__main__':
    storage = SecureStorage("/home")
    a = storage.open("../../banana", "w")
    a.write("tomate")
    b= storage.open("../../banana", "r")
    print(b.read())
