from enum import Enum


class Role(Enum):
    ANONYMOUS = "anonymous"
    USER = "user"
    SERVER = "server"
    ADMIN = "admin"
    ROOT = "root"