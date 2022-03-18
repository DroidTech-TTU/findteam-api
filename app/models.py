"""
FindTeam SQLAlchemy ORM models
"""

from base64 import b64decode, b64encode
from datetime import datetime
from enum import IntEnum
from random import randbytes
from typing import Optional

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy import Column, ForeignKey, delete, insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import join, relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.types import (Boolean, DateTime, Enum, Integer, LargeBinary,
                              String)

from . import logger
from .db import Base


class MembershipType(IntEnum):
    """User-project membership permission level"""

    APPLICANT = 0
    """Read, chat"""

    MEMBER = 1
    """Write, read, chat"""

    ADMIN = 2
    """Accept applicants, write, read, chat"""


class Status(IntEnum):
    """Project completion status"""

    AWAITING_TEAM = 0
    """Before progress is made"""

    IN_PROGRESS = 1
    """While progress is being made"""

    COMPLETE = 2
    """Project complete"""


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
    access_token = Column(
        LargeBinary(length=16),
        nullable=False,
        default=lambda: randbytes(16))
    # urls = relationship('UserUrl')
    # tags = relationship('UserTagged')
    # Above line is bugged due to asyncio

    def __str__(self):
        return f'#{self.uid} {self.first_name} {self.last_name}'

    @property
    def b64_access_token(self) -> bytes:
        """Return self.access_token as base64 encoded string"""
        return b64encode(self.access_token)

    async def get_owned_projects(self, async_session: AsyncSession) -> list['Project']:
        async with async_session.begin():
            return (await async_session.execute(select(Project).where(Project.owner_uid == self.uid))).values()

    async def get_membership_projects(self, async_session: AsyncSession) -> list['Project']:
        async with async_session.begin():
            memberships = (await async_session.execute(select(ProjectMembership).where(ProjectMembership.uid == self.uid and ProjectMembership.permission > MembershipType.NOTHING))).values()
            return [membership.project for membership in memberships]

    def check_password(self, password: str) -> bool:
        """Return True if password matches self.password hash"""
        return checkpw(password.encode(), self.password)

    @classmethod
    async def from_uid(cls, uid: int, async_session: AsyncSession) -> Optional['User']:
        """Return the User by the user id"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(cls).where(cls.uid == uid))
                result = stmt.one()
                return result[0]
            except NoResultFound:
                return None

    @classmethod
    async def from_email(cls, email: str, async_session: AsyncSession) -> Optional['User']:
        """Return the User by email address"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(cls).where(cls.email == email))
                result = stmt.one()
                return result[0]
            except NoResultFound:
                return None

    @classmethod
    async def from_b64_access_token(cls, b64_access_token: str, async_session: AsyncSession) -> Optional['User']:
        """Return the User by OAuth2 access_token"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(cls).where(cls.access_token == b64decode(b64_access_token)))
                result = stmt.one()
                return result[0]
            except NoResultFound:
                return None

    @staticmethod
    def hash_password(password: str) -> bytes:
        """Return bcrypt hashed password"""
        return hashpw(password.encode(), gensalt())


class UserUrl(Base):
    __tablename__ = 'USER_URL'
    uid = Column(
        Integer(),
        ForeignKey(
            'USER.uid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    domain = Column(
        String(253),
        primary_key=True)
    path = Column(
        String(2000 - 253),
        nullable=False)  # Max 2000 characters per url including domain

    @classmethod
    async def get_user_urls(cls, uid: int, async_session: AsyncSession) -> list['UserUrl']:
        """Return the UserUrls associated with a User ID"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(join(User, UserUrl)).where(User.uid == uid and UserUrl.uid == uid))
                return stmt.all()
            except NoResultFound:
                return list()

    @classmethod
    async def set_user_urls(cls, uid: int, urls: list[dict], async_session: AsyncSession):
        """Update the UserUrls associated with a User ID"""
        async with async_session.begin():
            await async_session.execute(delete(UserUrl).where(UserUrl.uid == uid))
        await async_session.commit()
        async_session.add_all(cls(
            uid=uid,
            **url) for url in urls)
        await async_session.commit()


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

    @classmethod
    async def get_user_tags(cls, uid: int, async_session: AsyncSession):
        """Return the Tags associated with a User ID"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(join(join(User, UserTagged), Tag)).where(User.uid == uid and UserTagged.uid == uid and Tag.text == UserTagged.tag_text))
                return stmt.all()
            except NoResultFound:
                return list()

    @staticmethod
    async def set_user_tags(uid: int, tags: list[dict], async_session: AsyncSession):
        """Update the Tags associated with a User"""
        async with async_session.begin():
            await async_session.execute(delete(UserTagged).where(UserTagged.uid == uid))
        await async_session.commit()
        for tag_dict in tags:
            tag = Tag(**tag_dict)
            async_session.add(tag)
            try:
                await async_session.commit()
            except IntegrityError:  # Ignore duplicate Tags
                await async_session.rollback()
            async_session.add(UserTagged(
                uid=uid,
                tag_text=tag.text))
            await async_session.commit()


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

    async def get_tag(self, async_session: AsyncSession) -> Tag:
        """Return the Tags associated with a UserTagged"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(Tag).where(Tag.text == self.tag_text))
                result = stmt.one()
                return result[0]
            except NoResultFound:
                return None


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
    members = relationship(
        'ProjectMembership',
        backref='project')

    def __str__(self):
        """pid title"""
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
    membership_type = Column(
        Enum(MembershipType),
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
