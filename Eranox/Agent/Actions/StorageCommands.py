from typing import Union, Dict

from Eranox.Agent.Actions.commands import Action
from Eranox.Agent.Connections.Controller import Controller
from Eranox.Agent.Storage import Storage, SealedStorage, SecureStorage, SecureSealedStorage
from Eranox.Core.Command import CommandMessage, CommandReplyMessage

STANDARD = "standard"
CHROOT = "chroot"
ENCRYPTED = "aes"
ENCRYPTED_CHROOT = "aes-chroot"


class InvalidMountPoint(Exception):
    pass


class StorageManager(object):
    __mounted: Dict[str, Storage] = {}

    @staticmethod
    def mount(mount_point: str, storage_type: str, path: str, master_key: str,
              master_table_path: Union[str, bool]) -> None:
        if storage_type == STANDARD:
            storage = Storage()
        elif storage_type == CHROOT:
            storage = SealedStorage(path)
        elif storage_type == ENCRYPTED:
            if master_table_path is not False:
                storage = SecureStorage(master_key, master_table_path)
            else:
                storage = SecureStorage(master_key)
        elif storage_type == ENCRYPTED_CHROOT:
            if master_table_path is not False:
                storage = SecureSealedStorage(path, master_key, master_table_path)
            else:
                storage = SecureStorage(path, master_key)
        else:
            raise NotImplementedError()
        StorageManager.__mounted[mount_point] = storage

    @staticmethod
    def unmount(mount_point: str):
        del StorageManager.__mounted[mount_point]

    @staticmethod
    def get_storage(mount_point: str) -> Union[Storage, None]:
        return StorageManager.__mounted[mount_point] if mount_point in StorageManager.__mounted else None

    @staticmethod
    def ls() -> Dict[str, Storage]:
        return StorageManager.__mounted


class Mount(Action):
    subparser_data = {"args": ["mount"], "kwargs": {"help": "execute system on a program"}}
    arguments = [
        {"args": ["storage_type"],
         "kwargs": {"help": "the storage type to use", "choices": ["standard", "chroot", "aes", "aes-chroot"]}},
        {"args": ["mount_point"], "kwargs": {"help": "the mount point of the storage", "type": str}},
        {"args": ["-mk", "--master-key"], "kwargs": {"help": "the masterkey to use for storage", "type": str}},
        {"args": ["-mp", "--master-table-path"],
         "kwargs": {"help": "the masterkey to use for storage", "type": str, "default": False}},
        {"args": ["-p", "--path"],
         "kwargs": {"help": "the storage type to use", "choices": [STANDARD, CHROOT, ENCRYPTED, ENCRYPTED_CHROOT]}}
    ]

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        mount a storage
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """

        res = None
        errors = []
        try:
            StorageManager.mount(args.mount_point, args.storage_type, args.path, args.master_key,
                                 args.master_table_path)
        except BaseException as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class GetFile(Action):
    subparser_data = {"args": ["get_file"], "kwargs": {"help": "get a file content from a storage"}}
    arguments = [
        {"args": ["mount_point"], "kwargs": {"help": "the mount point of the storage", "type": str}},
        {"args": ["path"], "kwargs": {"help": "the path of the file", "type": str}},

    ]

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        read a file from a Storage
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """
        res = None
        errors = []
        try:
            storage = StorageManager.get_storage(args.mount_point)
            if storage is None:
                raise InvalidMountPoint(args.mount_point)
            else:
                file = storage.open(args.path, "rb")
                res = file.read()
                file.close()
        except BaseException as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)
        import base64


class WriteFile(Action):
    subparser_data = {"args": ["write_file"], "kwargs": {"help": "write a file content to a storage"}}
    arguments = [
        {"args": ["mount_point"], "kwargs": {"help": "the mount point of the storage", "type": str}},
        {"args": ["path"], "kwargs": {"help": "the path of the file", "type": str}},
        {"args": ["content"], "kwargs": {"help": "the path of the file", "type": str}},

    ]

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        write a file to a Storage
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """
        res = None
        errors = []
        try:
            storage = StorageManager.get_storage(args.mount_point)
            if storage is None:
                raise InvalidMountPoint(args.mount_point)
            else:
                file = storage.open(args.path, "w")
                res = file.write(args.content)
                file.close()
        except BaseException as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class ListFile(Action):
    subparser_data = {"args": ["list_files"], "kwargs": {"help": "list the files from a storage"}}
    arguments = [
        {"args": ["mount_point"], "kwargs": {"help": "the mount point of the storage", "type": str}},
        {"args": ["path"], "kwargs": {"help": "the path of the file", "type": str}},

    ]

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        write a file to a Storage
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """
        res = None
        errors = []
        try:
            storage = StorageManager.get_storage(args.mount_point)
            if storage is None:
                raise InvalidMountPoint(args.mount_point)
            else:
                res = storage.listdir(args.path)
        except BaseException as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)


class ListStorage(Action):
    subparser_data = {"args": ["list_storage"], "kwargs": {"help": "list the storage available"}}

    def run(self, args, message: CommandMessage, controller: Controller):
        """
        write a file to a Storage
        :param args: the args object returned by parse_args
        :param controller: the controller object who called the function (unused)
        :return: None
        """
        res = None
        errors = []
        try:
            res = [(mount_point, str(storage.__class__)) for mount_point, storage in StorageManager.ls().items()]
        except BaseException as e:
            errors = [e]
        msg = CommandReplyMessage(message.message.get("uuid"), res, errors=errors)
        controller.write(msg)
