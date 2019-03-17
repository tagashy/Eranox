from sqlalchemy import Column, Integer, String, Enum

from EranoxAuth.Classobject.Base import Base
from EranoxAuth.Classobject.Role import Role


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_hash = Column(String, nullable=False)
    server_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)

    def __repr__(self) -> str:
        return f"<User(name='{self.name}')>"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "user_hash": self.user_hash, "server_hash": self.server_hash,
                "role": self.role}