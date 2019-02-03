from typing import Optional

from Crypto.Cipher import AES


class SecureFile():

    def __init__(self, key, iv, path, mode):
        self.__key = key
        self.__iv = iv
        self.aes = AES.new(key, AES.MODE_CBC, iv)
        if "b" not in mode:
            mode += "b"
        self.path = path
        self.file = open(path, mode)
        self.origin_write = self.file.write
        self.origin_read = self.file.read

        self.file.write = self.write
        self.file.read = self.read

    def write(self, s: str):
        if isinstance(s, bytes):
            s = s.decode()
        if len(s) % 16 != 0:
            s += "\0" * (16 - len(s) % 16)
        res=self.origin_write(self.aes.encrypt(s))
        self.file.flush()
        return res

    def read(self, size: Optional[int] = None):
        if isinstance(size, int):
            data = self.aes.decrypt(self.origin_read(size))
        else:
            data = self.aes.decrypt(self.origin_read())

        while b"\0" in data:
            data = data[:data.index(b"\0")]+data[data.index(b"\0")+1:]
        return data

    def reload(self, mode):
        self.__init__(self.__key, self.__iv, self.path, mode)


if __name__ == '__main__':
    a = SecureFile(b"0123456789012345", "8901234567890123", "test.txt", "w")

    a.file.write("toto")
    a.file.write("toto1")
    a.file.write("toto2")
    a.file.write("toto3")
    a.file.write("toto4")
    a.file.write("toto4")
    a.file.write("toto4")
    a.file.close()
    a = SecureFile(b"0123456789012345", "8901234567890123", "test.txt", "r")
    #print(a.origin_read())
    print(a.read())
