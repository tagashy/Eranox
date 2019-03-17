from sqlalchemy import Column, Integer, String, ForeignKey

from EranoxAuth.Classobject.Base import Base


class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    target = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    def __repr__(self):
        return f"<Permission(name='{self.target}')>"

    def to_dict(self) -> dict:
        return {"id": self.id, "target": self.target, "group_id": self.group_id, "user_id": self.user_id}