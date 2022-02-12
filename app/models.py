from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                        String)

from .db import Base
from .schemas import Permission

# https://variable-scope.com/posts/storing-and-verifying-passwords-with-sqlalchemy


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
        nullable=False)
    password = None  # Todo
    picture = Column(
        String(length=32+4),
        nullable=True)
    # 32 characters in sha-256 hash + 4 for .png (320x320)

    # def verify_password(self, password):
    #    return password == hashpw(password, self.password)


class UserUrl(Base):
    __tablename__ = 'USER_URL'
    uid = Column(
        Integer(),
        ForeignKey('USER.uid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    url = Column(
        String(2000),
        primary_key=True)


class Tag(Base):
    __tablename__ = 'TAG'
    text = Column(
        String(128),
        primary_key=True)
    category = Column(
        String(64),
        nullable=False)


class UserTagged(Base):
    __tablename__ = 'USER_TAGGED'
    uid = Column(
        Integer(),
        primary_key=True)
    tag_text = Column(
        String(128),
        ForeignKey('TAG.text', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)


class Project(Base):
    __tablename__ = 'PROJECT'
    pid = Column(
        Integer(),
        primary_key=True,
        autoincrement=True)
    owner_uid = Column(
        Integer(),
        ForeignKey('USER.uid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    title = Column(
        String(128),
        unique=True,
        nullable=False)
    description = Column(
        String(4096),
        nullable=False)
    status = Column(
        Integer(),
        nullable=False,
        default=0)


class ProjectPicture(Base):
    pid = Column(
        Integer(),
        ForeignKey('PROJECT.pid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    picture = Column(
        String(length=32+4),
        primary_key=True)  # 32 characters in sha-256 hash + 4 for .png (1080x1080)


class ProjectTagged(Base):
    pid = Column(
        Integer(),
        ForeignKey('PROJECT.pid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    tag_text = Column(
        String(128),
        ForeignKey('TAG.text', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    is_user_requirement = Column(
        Boolean(),
        nullable=False)


class ProjectMembership(Base):
    pid = Column(
        Integer(),
        ForeignKey('PROJECT.pid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    uid = Column(
        Integer(),
        ForeignKey('USER.uid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    permission = Column(
        Enum(Permission()),
        nullable=False)


class Message(Base):
    id = Column(
        Integer(),
        primary_key=True,
        autoincrement=True)
    from_uid = Column(
        Integer(),
        ForeignKey('USER.uid', onupdate='CASCADE', ondelete='CASCADE'))
    to_uid = Column(
        Integer(),
        ForeignKey('USER.uid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True)
    to_pid = Column(
        Integer(),
        ForeignKey('PROJECT.pid', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True)
    date = Column(
        DateTime(),
        nullable=False,
        default=datetime.utcnow)
    text = Column(
        String(128),
        nullable=False)
