"""
FindTeam Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .models import MembershipType, Status, Tag, User, UserUrl


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
                'password': 'hunter2'
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
        orm_mode = True
        schema_extra = {
            'example': {
                'text': 'Houston',
                'category': 'City'
            }
        }


class UrlModel(BaseModel):
    domain: str
    path: str

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'domain': 'github.com',
                'path': '/roryeckel'
            }
        }


class UserResultModel(BaseModel):
    uid: int
    first_name: str
    middle_name: str | None
    last_name: str
    picture: str | None
    email: str
    urls: list[UrlModel]
    tags: list[TagModel]

    @classmethod
    async def from_orm(cls, user: User, async_session: AsyncSession) -> 'UserResultModel':
        return cls(
            urls=[UrlModel.from_orm(url) for url in await UserUrl.get_user_urls(user.uid, async_session)],
            tags=[TagModel.from_orm(tag) for tag in await Tag.get_user_tags(user.uid, async_session)],
            **dict(user))

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
                    {
                        'domain': 'github.com',
                        'path': '/roryeckel'
                    }
                ],
                'tags': [
                    {
                        'text': 'Houston',
                        'category': 'Location'
                    }
                ]
            }
        }


class UserRequestModel(BaseModel):
    first_name: str
    middle_name: str | None
    last_name: str
    email: str
    password: str | None
    urls: list[UrlModel]
    tags: list[TagModel]

    class Config:
        schema_extra = {
            'example': {
                'first_name': 'Rory',
                'middle_name': '',
                'last_name': 'E',
                'email': 'user@site.com',
                'password': 'hunter2',
                'urls': [
                    {
                        'domain': 'github.com',
                        'path': '/roryeckel'
                    }
                ],
                'tags': [
                    {
                        'text': 'Houston',
                        'category': 'Location'
                    }
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
