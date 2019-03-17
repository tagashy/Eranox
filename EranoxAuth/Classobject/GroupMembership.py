from sqlalchemy import Column, Integer, ForeignKey

from EranoxAuth.Classobject.Base import Base


class GroupMembership(Base):
    __tablename__ = 'group_membership'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<GroupMembership(group_id='{self.group_id}',user_id='{self.user_id}')>"

    def to_dict(self) -> dict:
        return {"id": self.id, "group_id": self.group_id, "user_id": self.user_id}