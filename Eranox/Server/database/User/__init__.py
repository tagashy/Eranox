from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
Base = declarative_base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)
    hash = Column(String)
    role = Column(String)

    def __repr__(self):
        return f"<User(name='{self.name}', role='{self.role}', fullname='{self.fullname}', nickname='{self.nickname}')>"
