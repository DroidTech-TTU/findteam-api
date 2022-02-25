"""
FindTeam Pydantic schemas
"""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel


class Permission(IntEnum):
    """User-project membership permission level"""
    NOTHING = 0
    READ = 1
    READ_WRITE = 2
    READ_WRITE_EDIT = 3


class Status(IntEnum):
    """Project completion status"""
    AWAITING_TEAM = 0
    IN_PROGRESS = 1
    COMPLETE = 2


class LoginRequestModel(BaseModel):
    email: str
    password: str

    class Config:
        schema_extra = {
            'example': {
                'email': 'user@site.com',
                'password': 'hunter2'
            }
        }


class LoginResultModel(BaseModel):
    success: bool
    uid: int | None
    login_token: str | None

    class Config:
        schema_extra = {
            'example': {
                'success': True,
                'uid': 21,
                'login_token': 'Sw65wUqGwyP5fDUKNY4UDg=='
            }
        }


class RegisterRequestModel(BaseModel):
    first_name: str
    middle_name: str | None
    last_name: str
    email: str
    password: str

    class Config:
        schema_extra = {
            'example': {
                'first_name': 'Rory',
                'middle_name': '',
                'last_name': 'E',
                'email': 'user@site.com',
                'password': '$2b$12$IxPcWcNHYo1flBRosFU5/eFJzuPs3kvLVrQXx.Uubxhs4DvHsRpba'
            }
        }


class LoginTokenModel(BaseModel):
    uid: int
    login_token: str

    class Config:
        schema_extra = {
            'example': {
                'uid': 21,
                'login_token': 'Sw65wUqGwyP5fDUKNY4UDg=='
            }
        }


class UserModel(BaseModel):
    uid: int
    first_name: str
    middle_name: str
    last_name: str
    picture_url: str
    email: str
    urls: list[str]

    class Config:
        orm_mode = True


class ProjectModel(BaseModel):
    pid: int
    title: str
    status: Status
    description: str
    picture_urls: list[str]
    members: set[UserModel]
    owner: UserModel

    class Config:
        orm_mode = True


class MessageModel(BaseModel):
    id: int
    is_read: bool
    date: datetime
    text: str
    from_user: UserModel
    to: UserModel | ProjectModel

    class Config:
        orm_mode = True
