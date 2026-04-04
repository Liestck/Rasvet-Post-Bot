import enum
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PermEnum(str, enum.Enum):
    """ Права пользователей """

    DEFAULT = "default"
    PREMIUM = "premium"
    OWNER = "owner"


class User(Base):
    """ Данные пользователей """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    perm: Mapped[PermEnum] = mapped_column(
        sa.Enum(PermEnum, name="perm_enum"),
        nullable=False,
        default=PermEnum.DEFAULT
    )


class Channel(Base):
    """Данные каналов"""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True)
    can_post: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    up_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    down_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)