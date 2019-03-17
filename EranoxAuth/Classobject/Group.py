from sqlalchemy import Column, Integer, String

from EranoxAuth.Classobject.Base import Base


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f"<Group(name='{self.name}')>"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}