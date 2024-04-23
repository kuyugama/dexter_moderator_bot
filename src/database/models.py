import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()
METADATA = Base.metadata


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(sa.BIGINT, primary_key=True)

    is_group: Mapped[bool] = mapped_column(default=False)
    language: Mapped[str] = mapped_column(sa.String(length=3), default="en")

    warns_limit: Mapped[int] = mapped_column(default=5)
    # What bot will do with participants when his warns reached the limit
    warns_action: Mapped[str] = mapped_column(sa.String, default="mute")
    warns_action_time: Mapped[int] = mapped_column(sa.BIGINT, default=0)

    # If time is 0 - bot mutes user from group permanently
    default_mute_time: Mapped[int] = mapped_column(sa.BIGINT, default=1200)
    # If time is 0 - bot removes user from group permanently
    default_ban_time: Mapped[int] = mapped_column(sa.BIGINT, default=0)

    new_participant_greeting: Mapped[str] = mapped_column(sa.String(length=500))

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
            "new_participant_greeting": self.new_participant_greeting,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Member(Base):
    __tablename__ = "chat_members"
    id: Mapped[int] = mapped_column(sa.BIGINT, primary_key=True)
    user_id: Mapped[int] = mapped_column(sa.BIGINT)
    chat_id: Mapped[int] = mapped_column(sa.BIGINT)
    warns: Mapped[int] = mapped_column(default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "warns": self.warns,
            "chat_id": self.chat_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
