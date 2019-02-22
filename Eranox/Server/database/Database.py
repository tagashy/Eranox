from logging import error
from typing import List, Tuple, Dict

from Eranox.Server.database import Base
from Eranox.Server.database.User import User


class DB(object):
    engine = None
    Session = None

    def create_database(self):
        Base.metadata.create_all(self.engine)

    def add_user(self, user: User = None, name: str = None, hash: str = None, role: str = None, commit: bool = True,
                 session=None):
        if session is None: session = self.Session()
        if user is None and (name and hash and role):
            session.add(User(name=name, hash=hash, role=role))
            if commit: session.commit()
        elif user:
            session.add(user)
            if commit: session.commit()
        else:
            error("add_user called with every parameter None")

    def add_users(self, users: List[(User, Tuple[str, str, str], Dict[str, str])]):
        session = self.Session()
        for user in users:
            if isinstance(user, User):
                self.add_user(user, session=session, commit=False)
            elif (isinstance(user, tuple) or isinstance(user, list)) and len(user) == 3:
                self.add_user(name=user[0], hash=user[1], role=user[2], session=session, commit=False)
            elif isinstance(user, dict) and "name" in user and "hash" in user and "role" in user:
                self.add_user(name=user.get("name"), hash=user.get("hash"), role=user.get("role"), session=session,
                              commit=False)
            else:
                error(f"invalid user {user}")
        session.commit()
