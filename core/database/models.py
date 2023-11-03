from sqlalchemy import Column, BigInteger, Boolean, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()
METADATA = Base.metadata


class Chat(Base):
    __tablename__ = "chats"
    id = Column(BigInteger, primary_key=True)

    is_group = Column(Boolean, default=False)
    language = Column(String(length=3), default="en")

    warns_limit = Column(Integer, default=5)
    # What bot will do with participants when his warns reached the limit
    warns_action = Column(String, default="mute")
    warns_action_time = Column(BigInteger, default=0)

    # If time is 0 - bot mutes user from group permanently
    default_mute_time = Column(BigInteger, default=1200)
    # If time is 0 - bot removes user from group permanently
    default_ban_time = Column(BigInteger, default=0)

    new_participant_greeting = Column(String(length=500))

    def to_dict(self):
        return {
            "id": self.id,
            "is_group": self.is_group,
            "language": self.language,
            "warns_limit": self.warns_limit,
            "warns_action": self.warns_action,
            "warns_action_time": self.warns_action_time,
            "default_mute_time": self.default_mute_time,
            "default_ban_time": self.default_ban_time,
            "new_participant_greeting": self.new_participant_greeting
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Member(Base):
    __tablename__ = "chat_members"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    chat_id = Column(BigInteger)
    warns = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "warns": self.warns,
            "chat_id": self.chat_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
