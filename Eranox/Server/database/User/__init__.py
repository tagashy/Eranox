from sqlalchemy import Column, Integer, String

from Eranox.Server.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    hash = Column(String)
    role = Column(String)

    def __repr__(self):
        return f"<User(name='{self.name}', role='{self.role}')>"
