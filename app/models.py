"""
FindTeam SQLAlchemy ORM models
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from bcrypt import checkpw
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy.types import (Boolean, DateTime, Enum, Integer, LargeBinary,
                              String)

from .db import Base
from .schemas import Permission, Status


class User(Base):
    __tablename__ = 'USER'
    uid = Column(
        Integer(),
        primary_key=True,
        autoincrement=True)
    first_name = Column(
        String(length=32),
        nullable=False)
    middle_name = Column(
        String(length=32),
        nullable=True)
    last_name = Column(
        String(length=32),
        nullable=True)
    email = Column(
        String(length=254),
        unique=True,
        nullable=False)
    password = Column(
        LargeBinary(length=60),
        nullable=False)
    picture = Column(
        # 32 characters in sha-256 hash + 4 for .png (320x320)
        String(length=32+4),
        nullable=True)
    urls = relationship('UserUrl')
    tags = relationship('UserTagged')

    def __str__(self):
        return f'#{self.uid} {self.first_name} {self.last_name}'

    def check_password(user, password: str) -> bool:
        """Return true if password matches self.password hash"""
        return checkpw(password.encode('utf8'), user.password)

    @classmethod
    async def from_email(cls, email: str, async_session: AsyncSession) -> Optional['User']:
        """Return the User by email address"""
        async with async_session.begin():
            return (await async_session.execute(select(cls).where(cls.email == email))).one_or_none()


class UserUrl(Base):
    __tablename__ = 'USER_URL'
    uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    url = Column(
        String(2000))


class Tag(Base):
    __tablename__ = 'TAG'
    text = Column(
        String(128),
        primary_key=True)
    category = Column(
        String(64),
        nullable=False)

    def __str__(self):
        return f'{self.text} ({self.category})'


class UserTagged(Base):
    __tablename__ = 'USER_TAGGED'
    uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    tag_text = Column(
        String(128),
        ForeignKey(
            'TAG.text',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)


class Project(Base):
    __tablename__ = 'PROJECT'
    pid = Column(
        Integer(),
        primary_key=True,
        autoincrement=True)
    owner_uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    title = Column(
        String(128),
        unique=True,
        nullable=False)
    description = Column(
        String(4096),
        nullable=False)
    status = Column(
        Enum(Status),
        nullable=False,
        default=0)
    pictures = relationship('ProjectPicture')
    tags = relationship('ProjectTagged')
    members = relationship('ProjectMembership')

    def __str__(self):
        return f'#{self.pid} {self.title}'


class ProjectPicture(Base):
    __tablename__ = 'PROJECT_PICTURE'
    pid = Column(
        Integer(),
        ForeignKey(
            'PROJECT.pid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    picture = Column(
        String(length=32+4),
        primary_key=True)  # 32 characters in sha-256 hash + 4 for .png (1080x1080)


class ProjectTagged(Base):
    __tablename__ = 'PROJECT_TAGGED'
    pid = Column(
        Integer(),
        ForeignKey(
            'PROJECT.pid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    tag_text = Column(
        String(128),
        ForeignKey(
            'TAG.text',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    is_user_requirement = Column(
        Boolean(),
        nullable=False)


class ProjectMembership(Base):
    __tablename__ = 'PROJECT_MEMBERSHIP'
    pid = Column(
        Integer(),
        ForeignKey(
            'PROJECT.pid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    permission = Column(
        Enum(Permission),
        nullable=False)


class Message(Base):
    __tablename__ = 'MESSAGE'
    id = Column(
        Integer(),
        primary_key=True,
        autoincrement=True)
    from_uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'))
    to_uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        nullable=True)
    to_pid = Column(
        Integer(),
        ForeignKey(
            'PROJECT.pid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        nullable=True)
    date = Column(
        DateTime(),
        nullable=False,
        default=datetime.utcnow)
    text = Column(
        String(128),
        nullable=False)
    is_read = Column(
        Boolean(),
        nullable=False,
        default=False)

    def __str__(self):
        return f'#{self.id}: {self.text}'
