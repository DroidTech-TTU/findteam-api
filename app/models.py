"""
FindTeam SQLAlchemy ORM models and Enums
"""

from base64 import b64decode, b64encode
from datetime import datetime
from enum import IntEnum
from random import randbytes
from typing import Optional

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy import Column, ForeignKey, delete, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import join, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.types import (Boolean, DateTime, Enum, Integer, LargeBinary,
                              String)

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
    """USER sqlalchemy orm"""
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
        # 672ce0696eb32fa4665231f0867254ac672abadf354d9330a075c9432a30352a.png
        String(length=68),
        nullable=True)
    access_token = Column(
        LargeBinary(length=16),
        nullable=False,
        default=lambda: randbytes(16))
    # urls = relationship('UserUrl')
    # tags = relationship('UserTagged')
    # "Relationship" is bugged due to asyncio

    def __str__(self):
        return f'#{self.uid} {self.first_name} {self.last_name}'

    @property
    def b64_access_token(self) -> bytes:
        """Return self.access_token as base64 encoded string"""
        return b64encode(self.access_token)

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
    async def from_b64_access_token(
            cls,
            b64_access_token: str,
            async_session: AsyncSession) -> Optional['User']:
        """Return the User by OAuth2 access_token"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(
                    select(cls).
                    where(cls.access_token == b64decode(b64_access_token)))
                result = stmt.one()
                return result[0]
            except NoResultFound:
                return None

    @staticmethod
    def hash_password(password: str) -> bytes:
        """Return bcrypt hashed password"""
        return hashpw(password.encode(), gensalt())


class UserUrl(Base):
    """USER_URL sqlalchemy orm"""
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
            stmt = await async_session.execute(
                select(join(User, cls)).
                where(User.uid == uid, cls.uid == uid))
            return stmt.all()

    @classmethod
    async def set_user_urls(cls, uid: int, urls: list[dict], async_session: AsyncSession):
        """Update the UserUrls associated with a User ID"""
        async with async_session.begin():
            await async_session.execute(delete(cls).where(cls.uid == uid))
        await async_session.commit()
        async_session.add_all(cls(
            uid=uid,
            **url) for url in urls)
        await async_session.commit()


class Tag(Base):
    """TAG sqlalchemy orm"""
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
    async def get_tags(cls, async_session: AsyncSession, uid: int = None, pid: int = None):
        """Return the Tags associated with a User or Project ID"""
        assert (uid or pid) and not (uid and pid)  # uid XOR pid
        async with async_session.begin():
            stmt = select(join(join(User, UserTagged)
                               if uid else join(Project, ProjectTagged), Tag))
            if uid:
                stmt = stmt.where(User.uid == uid, UserTagged.uid == uid)
            else:
                stmt = stmt.where(Project.pid == pid, ProjectTagged.pid == pid)
            result = await async_session.execute(stmt.where(Tag.text == UserTagged.tag_text))
            return result.all()

    @staticmethod
    async def set_tags(uid: int, tags: list[dict], async_session: AsyncSession):
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
    """USER_TAGGED sqlalchemy orm"""
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
    """PROJECT sqlalchemy orm"""
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
    #pictures = relationship('ProjectPicture')
    #tags = relationship('ProjectTagged')
    members = relationship(
        'ProjectMembership',
        backref='project')

    def __str__(self):
        """pid title"""
        return f'#{self.pid} {self.title}'

    @classmethod
    async def from_pid(cls, pid: int, async_session: AsyncSession) -> Optional['Project']:
        """Return the Project by the project id"""
        async with async_session.begin():
            try:
                stmt = await async_session.execute(select(cls).where(cls.pid == pid))
                result = stmt.one()
                return result[0]
            except NoResultFound:
                return None


class ProjectPicture(Base):
    """PROJECT_PICTURE sqlalchemy orm"""
    __tablename__ = 'PROJECT_PICTURE'
    pid = Column(
        Integer(),
        ForeignKey(
            'PROJECT.pid',
            onupdate='CASCADE',
            ondelete='CASCADE'),
        primary_key=True)
    picture = Column(
        # 672ce0696eb32fa4665231f0867254ac672abadf354d9330a075c9432a30352a.png
        String(length=68),
        primary_key=True)

    @classmethod
    async def get_project_pictures(cls, pid: int, async_session: AsyncSession) -> list[str]:
        async with async_session.begin():
            stmt = await async_session.execute(
                select(join(Project, cls)).
                where(Project.pid == pid, cls.pid == pid))
            return [item.picture for item in stmt.all()]

    @classmethod
    async def set_project_pictures(cls, pid: int, pictures: list[str], async_session: AsyncSession):
        """Update the UserUrls associated with a User ID"""
        async with async_session.begin():
            await async_session.execute(delete(cls).where(cls.pid == pid))
        await async_session.commit()
        async_session.add_all(cls(
            pid=pid,
            picture=picture) for picture in pictures)
        await async_session.commit()


class ProjectTagged(Base):
    """PROJECT_TAGGED sqlalchemy orm"""
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
    """PROJECT_MEMBERSHIP sqlalchemy orm"""
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

    @classmethod
    async def get_project_memberships(cls, pid: int, async_session: AsyncSession) -> list['ProjectMembership']:
        async with async_session.begin():
            stmt = await async_session.execute(
                select(join(User, cls)).
                where(cls.pid == pid, cls.uid == User.uid))
            return stmt.all()


class Message(Base):
    """MESSAGE sqlalchemy orm"""
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

    @classmethod
    async def delete_chat_history(cls, to_uid: int, from_uid: int, async_session: AsyncSession):
        """Delete all chat history between"""
        async with async_session.begin():
            await async_session.execute(
                delete(cls).
                where(or_(and_(cls.to_uid == to_uid, cls.from_uid == from_uid),
                          and_(cls.to_uid == from_uid, cls.from_uid == to_uid))))

    @classmethod
    async def get_chat_list(cls, uid: int, async_session: AsyncSession) -> list[int]:
        """Return uids of active dms sent between uid by any user"""
        async with async_session.begin():
            stmt = await async_session.execute(
                select(cls).
                where(or_(cls.from_uid == uid, cls.to_uid == uid)).
                order_by(cls.date))
            result = set()
            for message in stmt.all():
                result.add(message[0].to_uid)
                result.add(message[0].from_uid)
            result.remove(uid)
            return result

    @classmethod
    async def get_user_chat_history(
            cls,
            from_uid: int,
            to_uid: int,
            async_session: AsyncSession) -> list['Message']:
        """Return all Messages to and from uid"""
        async with async_session.begin():
            result = await async_session.execute(
                select(cls).
                where(or_(and_(cls.to_uid == to_uid, cls.from_uid == from_uid),
                          and_(cls.to_uid == from_uid, cls.from_uid == to_uid))).
                order_by(cls.date))
            return [item[0] for item in result.all()]

    @classmethod
    async def get_project_chat_history(
            cls,
            pid: int,
            async_session: AsyncSession) -> list['Message']:
        """Return all Messages to and from uid"""
        async with async_session.begin():
            result = await async_session.execute(
                select(cls).
                where(cls.to_pid == pid).
                order_by(cls.date))
            return [item[0] for item in result.all()]
