"""
FindTeam Pydantic schemas
"""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel


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


class OAuth2AccessTokenModel(BaseModel):
    access_token: str
    token_type: str = 'Bearer'

    class Config:
        schema_extra = {
            'example': {
                'access_token': 'Sw65wUqGwyP5fDUKNY4UDg==',
                'token_type': 'Bearer'
            }
        }


class TagModel(BaseModel):
    text: str
    category: str

    class Config:
        schema_extra = {
            'example': {
                'text': 'Houston',
                'category': 'City'
            }
        }

class UserResultModel(BaseModel):
    uid: int
    first_name: str
    middle_name: str | None
    last_name: str
    picture: str
    email: str
    urls: list[str]
    tags: list[TagModel]

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'uid': 21,
                'first_name': 'Rory',
                'middle_name': '',
                'last_name': 'E',
                'picture': '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4.png',
                'email': 'user@site.com',
                'urls': [
                    'https://github.com/roryeckel'
                ]
            }
        }


class UserRequestModel(BaseModel):
    first_name: str
    middle_name: str | None
    last_name: str
    email: str
    urls: list[str]
    tags: list[TagModel]

    class Config:
        schema_extra = {
            'example': {
                'first_name': 'Rory',
                'middle_name': '',
                'last_name': 'E',
                'email': 'user@site.com',
                'urls': [
                    'https://github.com/roryeckel'
                ]
            }
        }


class ProjectModel(BaseModel):
    pid: int
    title: str
    status: Status
    description: str
    pictures: list[str]
    members: set[UserResultModel]
    owner: UserResultModel
    tags: list[TagModel]

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'pid': 21,
                'title': 'A Very Cool Project',
                'status': Status.AWAITING_TEAM,
                'description': 'This project is very cool. Please join.',
                'pictures': [
                    '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4.png'
                ]
            }
        }


class MessageModel(BaseModel):
    id: int
    is_read: bool
    date: datetime
    text: str
    from_user: UserResultModel
    to: UserResultModel | ProjectModel

    class Config:
        orm_mode = True
