import base64
import hashlib
import json
import os
from logging import error
from typing import List, Union

import bcrypt
import sqlalchemy
from Crypto.Cipher import AES
from sqlalchemy.orm import sessionmaker

from EranoxAuth.Classobject import User, Base, Role, GroupMembership, Group, Permission
from EranoxAuth.Engine import DefaultEngine, Engine
from EranoxAuth.Utils.create_db import create_database

BLOCK_SIZE = 16


def get_random_number():
    return os.urandom(BLOCK_SIZE)


def encrypt(message, password):
    hash = get_hash(password)
    password = hash[:32]
    IV = hash[32:48]
    if not isinstance(password, bytes):
        password = password.encode("utf-8")
    aes = AES.new(password, AES.MODE_CFB, IV)
    return base64.b64encode(aes.encrypt(message))


def decrypt(encrypted, password):
    hash = get_hash(password)
    password = hash[:32]
    IV = hash[32:48]
    if not isinstance(password, bytes):
        password = password.encode("utf-8")
    aes = AES.new(password, AES.MODE_CFB, IV)
    try:
        return aes.decrypt(base64.b64decode(encrypted))
    except Exception as e:
        print(f"encrypted: {encrypted}")
        error(e)

def get_hash(password: str) -> str:
    m = hashlib.sha3_512()
    if not isinstance(password, bytes):
        password = password.encode("utf-8")
    m.update(password)
    b64_hash = base64.b64encode(m.digest())
    return b64_hash


class AuthenticationError(Exception):
    msg: str = "Unknown authentication exception"

    def __str__(self):
        return f"<AuthenticationError({self.msg})>"


class InvalidUsername(AuthenticationError):
    msg: str = "Invalid Username"


class InvalidPassword(AuthenticationError):
    msg: str = "Invalid Password"


class GroupNameError(NameError):
    msg: str = "Invalid group name"

    def __str__(self):
        return f"<GroupNameError({self.msg})>"


class MissingParameter(Exception):
    pass


class Authenticator(object):
    def __init__(self, engine: Engine = DefaultEngine()):
        create_database(engine.engine, Base)
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine.engine)

    def get_session(self):
        self.Session = sessionmaker(bind=self.engine.engine)
        session = self.Session()
        return session

    def authenticate_challenge(self, stage: int = 0, **kwargs):
        def stage0(server_hash):
            rnd = get_random_number()
            return encrypt(rnd, server_hash), rnd

        def stage1(authenticator, username: str, challenge: str):
            session = authenticator.get_session()
            try:
                user = session.query(User).filter_by(name=username).first()
            except sqlalchemy.exc.OperationalError as e:
                error(f"authenticate_user exception {e}")
                raise InvalidUsername()
            key = decrypt(challenge, user.server_hash)
            rnd = get_random_number()
            return encrypt(rnd, key), rnd

        def stage2(decryption_key, password: str, challenge: str, keep_encrypt: bool = False):
            key = decrypt(challenge, decryption_key)
            if keep_encrypt:
                enc_key=get_random_number()
                enc_key=base64.b64encode(enc_key)
                return encrypt(json.dumps({"key": enc_key.decode("utf-8"), "password": password}), key), enc_key
            else:
                return encrypt(password, key)

        def stage3(authenticator, username: str, challenge: str, key: str, crypted_password: bool = False,
                   keep_encrypt: bool = False):
            datas = decrypt(challenge, key)
            if keep_encrypt:
                datas = json.loads(datas)
                password = datas.get("password")
                key = datas.get("key")
                return authenticator.authenticate_user(username, password, crypted_password), key
            else:
                return authenticator.authenticate_user(username, datas, crypted_password)

        def has_parameter(parameter: Union[str, List[str]], kwargs: dict):
            if isinstance(parameter, str):
                if parameter in kwargs:
                    return True
                else:
                    return False
            elif isinstance(parameter, list):
                for param in parameter:
                    if not has_parameter(param, kwargs):
                        return False
                else:
                    return True
            else:
                raise NotImplementedError()

        if stage == 0:
            if has_parameter("server_hash", kwargs):
                return stage0(server_hash=kwargs.get("server_hash"))
            else:
                raise MissingParameter("server_hash")
        elif stage == 1:
            if has_parameter(["username", "challenge"], kwargs):
                return stage1(authenticator=self, username=kwargs.get("username"),
                              challenge=kwargs.get("challenge"))
            else:
                raise MissingParameter(["username", "challenge"])
        elif stage == 2:
            if has_parameter(["decryption_key", "password", "challenge", "keep_encrypt"], kwargs):
                return stage2(decryption_key=kwargs.get("decryption_key"), password=kwargs.get("password"),
                              challenge=kwargs.get("challenge"),
                              keep_encrypt=kwargs.get("keep_encrypt"))
            else:
                raise MissingParameter(["decryption_key", "password", "challenge", "keep_encrypt"])
        elif stage == 3:
            if has_parameter(["username", "key", "challenge", "crypted_password", "keep_encrypt"], kwargs):
                return stage3(authenticator=self, username=kwargs.get("username"),
                              crypted_password=kwargs.get("crypted_password", False),
                              challenge=kwargs.get("challenge"), key=kwargs.get("key"),
                              keep_encrypt=kwargs.get("keep_encrypt"))
            else:
                raise MissingParameter(["username", "key", "challenge", "crypted_password", "keep_encrypt"])
        else:
            raise NotImplementedError()

    def authenticate_user(self, username: str, password: str, crypted_password: bool = True) -> User:
        session = self.get_session()
        try:
            user = session.query(User).filter_by(name=username).first()
        except sqlalchemy.exc.OperationalError as e:
            error(f"authenticate_user exception {e}")
            raise InvalidUsername()
        if user is None:
            raise InvalidUsername()
        password = get_hash(password) if not crypted_password else get_hash(decrypt(password, user.server_hash))
        if bcrypt.checkpw(password, user.user_hash):
            user.hash = None
            return user
        else:
            user.hash = None
            raise InvalidPassword()

    def create_user(self, username: str, password: str, role: Role = Role.USER) -> dict:
        """
        create a user in db
        :param username: the username of the user
        :param password: the password of the user (will be hashed)
        :param role: the role of the user
        :return:
        """
        session = self.get_session()
        try:
            user = session.query(User).filter_by(name=username).first()
        except sqlalchemy.exc.OperationalError as e:
            error(f"create_user exception {e}")
            raise InvalidUsername()
        user_hash = bcrypt.hashpw(get_hash(password), bcrypt.gensalt())
        server_hash = bcrypt.hashpw(user_hash, bcrypt.gensalt())
        user = User(name=username, user_hash=user_hash, server_hash=server_hash, role=role)
        session.add(user)
        session.commit()
        return user.to_dict()

    def get_user(self, user: (User, str, int, dict)) -> User:
        """
        get a user in db
        :param user: the name of the user
        :return: the user
        """
        if not isinstance(user, User):
            if isinstance(user, str):
                session = self.get_session()
                try:
                    return session.query(User).filter_by(name=user).first()
                except sqlalchemy.exc.OperationalError as e:
                    error(f"get_user exception {e}")
                    raise NameError(user)
            elif isinstance(user, dict):
                user = User(**user)
            elif isinstance(user, int):
                session = self.get_session()
                try:
                    return session.query(User).filter_by(id=user).first()
                except sqlalchemy.exc.OperationalError as e:
                    error(f"get_user exception {e}")
                    raise ValueError(user)
            else:
                raise TypeError(user)
        return user

    def get_user_id(self, user: (User, str, int, dict)) -> int:
        """
        get the user id from User object string or int
        :param user: an int, a string or a User object
        :return: the user id (an int)
        """
        return self.get_user(user).id

    def create_group(self, group_name: str) -> dict:
        """
        create a group
        :param group_name: the name of the group
        :return: the group
        """
        session = self.get_session()
        try:
            group = session.query(User).filter_by(name=group_name).first()
        except sqlalchemy.exc.OperationalError as e:
            error(f"create_group exception {e}")
            raise GroupNameError()
        group = Group(name=group_name)
        session.add(group)
        session.commit()
        return group.to_dict()

    def get_group(self, group: (Group, str, int, dict)) -> Group:
        """
        get a group in db
        :param group: the name of the group
        :return: the group
        """

        if not isinstance(group, Group):
            if isinstance(group, str):
                session = self.get_session()
                try:
                    return session.query(Group).filter_by(name=group).first()
                except sqlalchemy.exc.OperationalError as e:
                    error(f"get_group exception {e}")
                    raise NameError(group)
            elif isinstance(group, dict):
                group = Group(**group)
            elif isinstance(group, int):
                session = self.get_session()
                try:
                    return session.query(Group).filter_by(id=group).first()
                except sqlalchemy.exc.OperationalError as e:
                    error(f"get_group exception {e}")
                    raise ValueError(group)
            else:
                raise TypeError(group)
        return group

    def get_group_id(self, group: (Group, str, int, dict)) -> int:
        """
        get the group id from Group object string or int
        :param group: an int, a string, a dict or a Group object
        :return: the group id (an int)
        """
        return self.get_group(group).id

    def add_user_to_group(self, user: (User, str, int, dict), group: (Group, str, int, dict)) -> dict:
        """
        create a group membership in db
        :param user: the name of the user, its id, or the User object
        :param group: the name of the group, its id, or the Group object
        :return: a GroupMenbership object
        """
        return self.create_group_membership(user, group)

    def create_group_membership(self, user: (User, str, int, dict), group: (Group, str, int, dict)) -> dict:
        """
        create a group membership in db
        :param user: the name of the user, its id, or the User object
        :param group: the name of the group, its id, or the Group object
        :return: a GroupMenbership object
        """
        session = self.get_session()
        user_id = self.get_user_id(user)
        group_id = self.get_group_id(group)
        group_membership = GroupMembership(user_id=user_id, group_id=group_id)
        try:
            session.add(group_membership)
            session.commit()
        except sqlalchemy.exc.OperationalError as e:
            error(f"create_group_membership exception {e}")
        return group_membership.to_dict()

    def create_permission(self, target: str, user: (User, str, int, dict, None) = None,
                          group: (Group, str, int, dict, None) = None) -> dict:
        """
        create a permission
        :param target:
        :param user: the name of the user, its id, or the User object
        :param group: the name of the group, its id, a dict, the Group object or None
        :return: a Permission object converted to dict
        """
        session = self.get_session()
        if user is not None and group is not None:
            raise ValueError("Permission must be on a group or a user cannot be none")
        elif user is None:
            group_id = self.get_group_id(group)
            permission = Permission(target=target, group_id=group_id)
        elif group is None:
            user_id = self.get_user_id(user)
            permission = Permission(target=target, user_id=user_id)
        else:
            user_id = self.get_user_id(user)
            group_id = self.get_group_id(group)
            permission = Permission(target=target, user_id=user_id, group_id=group_id)
        try:
            session.add(permission)
            session.commit()
        except sqlalchemy.exc.OperationalError as e:
            error(f"create_permission exception {e}")
        return permission.to_dict()

    def can_user_do(self, action: str, user: (User, str, int, dict)) -> bool:
        """
        check if an user can do an action (have a permission set in db), it check also for its groups
        :param action: the action to search for
        :param group: the group to search for (can be a group object or its id)
        :return: True if a permission exist False otherwise
        """
        user = self.get_user(user)
        session = self.get_session()
        groups = self.get_groups_of_user(user)
        try:
            permission = session.query(Permission).filter_by(target=action, user_id=user.id).first()
            if permission is not None:
                return True
            else:
                for group in groups:
                    if self.can_group_do(action, group):
                        return True
                return False
        except sqlalchemy.exc.OperationalError as e:
            for group in groups:
                if self.can_group_do(action, group):
                    return True
            error(f"can_user_do exception {e}")
            return False

    def can_group_do(self, action: str, group: (Group, int, str, dict)) -> bool:
        """
        check if a group can do an action (have a permission set in db)
        :param action: the action to search for
        :param group: the group to search for (can be a group object or its id)
        :return: True if a permission exist False otherwise
        """
        group = self.get_group(group)
        session = self.get_session()
        try:
            permission = session.query(Permission).filter_by(target=action,
                                                             group_id=group.id).first()
            if permission is not None:
                return True
            else:
                return False
        except sqlalchemy.exc.OperationalError as e:
            error(f"can_user_do exception {e}")
            return False

    def get_group_membership_of_user(self, user: (User, str, int, dict)) -> List[GroupMembership]:
        """
        return the group id of each group the user is in
        :param user: user to search groups for
        :return: a list of int
        """
        user = self.get_user(user)
        session = self.get_session()
        try:

            return session.query(GroupMembership).filter_by(user_id=user.id)
        except sqlalchemy.exc.OperationalError as e:
            error(e)
            return []

    def get_groups_of_user(self, user: (User, str, int, dict)) -> List[Group]:
        """
        return the Group object of each group the user is in
        :param user: user to search groups for
        :return: a list of Group object
        """
        user = self.get_user(user)
        group_membership_of_user = self.get_group_membership_of_user(user)
        res = []
        session = self.get_session()
        for group_membership in group_membership_of_user:
            try:
                res.append(session.query(Group).filter_by(id=group_membership.group_id).first())
            except sqlalchemy.exc.OperationalError as e:
                error(f"get_groups_of_user exception {e}")
        return res


if __name__ == '__main__':
    crypt = encrypt("toto", "titi")
    decrypted = decrypt(crypt, "titi")
    pass
