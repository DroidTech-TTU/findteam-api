"""
FindTeam Pydantic schemas
"""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel


class Permission(IntEnum):
    """User-project membership permission level"""
    READ = 0
    READ_WRITE = 1
    READ_WRITE_EDIT = 2


class Status(IntEnum):
    """Project completion status"""
    AWAITING_TEAM = 0
    IN_PROGRESS = 1
    COMPLETE = 2


class CredentialModel(BaseModel):
    email: str
    password: str


class StatusModel(BaseModel):
    success: bool
    message: str


class User(BaseModel):
    uid: int
    first_name: str
    middle_name: str
    last_name: str
    picture_url: str
    urls: list[str]

    class Config:
        orm_mode = True


class Project(BaseModel):
    pid: int
    title: str
    status: Status
    description: str
    picture_urls: list[str]
    members: set[User]
    owner: User

    class Config:
        orm_mode = True


class Message(BaseModel):
    id: int
    is_read: bool
    date: datetime
    text: str
    from_user: User
    to: User | Project

    class Config:
        orm_mode = True
