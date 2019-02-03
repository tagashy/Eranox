import os
from typing import Union, Optional


class Storage(object):
    def open(self, file, mode: str = "r", *args, **kwargs):
        return open(file, mode, *args, **kwargs)

    def remove(self, path: Union[bytes, str]):
        return os.remove(path)

    def listdir(self, path: Union[bytes, str]):
        return os.listdir(path)

    def rmdir(self, path: Union[bytes, str]):
        return os.rmdir(path)

    def stats(self, path: Union[bytes, str, int], dir_fd: Optional[int] = None, follow_symlinks: Optional[bool] = True):
        return os.stat(path=path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    def exist(self,path):
        return os.path.exists(path)