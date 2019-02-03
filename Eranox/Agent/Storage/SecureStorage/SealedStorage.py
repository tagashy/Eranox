import os
from typing import Union, Optional
from Eranox.constants import SECURE_STORAGE_MASTERTABLE_PATH
from Eranox.Agent.Storage.SecureStorage.SecureStorage import SecureStorage as Storage


class SealedStorage(Storage):
    def __init__(self, path,masterkey, mastertable_path: str = SECURE_STORAGE_MASTERTABLE_PATH):
        self.path = path
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        super().__init__(masterkey, mastertable_path)


    def __get_path(self, path) -> str:
        r_file = os.path.normpath(os.path.join(self.path, path))
        if not r_file.startswith(self.path):
            file = os.path.normpath(path)
            file = file.replace("../", "").replace("..\\", "")
            if file == "..":
                file = ""
            r_file = os.path.join(self.path, file)
            r_file = os.path.normpath(r_file)
        return r_file

    def open(self, file, mode: str = "r", *args, **kwargs):
        return super().open(self.__get_path(file), mode, *args, **kwargs)

    def remove(self, path: Union[bytes, str]):
        return super().remove(self.__get_path(path))

    def listdir(self, path: Union[bytes, str]):
        return super().listdir(self.__get_path(path))

    def rmdir(self, path: Union[bytes, str]):
        return super().rmdir(self.__get_path(path))

    def stats(self, path: Union[bytes, str, int], dir_fd: Optional[int] = None, follow_symlinks: Optional[bool] = True):
        return super().stats(self.__get_path(path), dir_fd, follow_symlinks)


if __name__ == '__main__':
    storage = SealedStorage("test","bonobo")
    banana=storage.open("../../banana","w")
    banana.write('tomat 123 atack')
    b=storage.open("banana")
    print(b.read())