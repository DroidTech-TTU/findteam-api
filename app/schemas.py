"""
FindTeam Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .models import MembershipType, Status, Tag, User, UserUrl


class RegisterRequestModel(BaseModel):
    """User registration schema"""
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
    """OAuth2 access token schema"""
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
    """User or Project Tag schema"""
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
    """User linked profile schema"""
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
    """User profile data retrieval schema"""
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
        """Fetch User data into schema"""
        return cls(
            urls=[UrlModel.from_orm(url) for url in
                  await UserUrl.get_user_urls(user.uid, async_session)],
            tags=[TagModel.from_orm(tag) for tag in
                  await Tag.get_user_tags(user.uid, async_session)],
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
    """User profile data update schema"""
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


class ProjectMember(BaseModel):
    """User project membership schema"""
    uid: int
    pid: int
    membership_type: MembershipType

    class Config:
        schema_extra = {
            'example': {
                'uid': 22,
                'pid': 21,
                'membership_type': MembershipType.ADMIN
            }
        }


class ProjectModel(BaseModel):
    """Project schema"""
    pid: int
    title: str
    status: Status
    description: str
    pictures: list[str]
    members: list[ProjectMember]
    owner_uid: int
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
                ],
                'members': [ProjectMember(
                    uid=22,
                    pid=21,
                    membership_type=MembershipType.ADMIN)],
                'owner_uid': 21,
                'tags': [TagModel(
                    text='Lubbock',
                    category='Location')]
            }
        }


class MessageRequestModel(BaseModel):
    """User to User or Project message send schema"""
    text: str
    to_uid: int | None
    to_pid: int | None

    class Config:
        schema_extra = {
            'example': {
                'text': 'Hi John',
                'to_uid': 22,
                'to_pid': None
            }
        }


class MessageResultModel(BaseModel):
    """User to User or Project message retrieval schema"""
    id: int
    is_read: bool
    date: datetime
    text: str
    from_uid: int
    to_uid: int | None
    to_pid: int | None

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'id': 123,
                'is_read': True,
                'date': datetime(year=1969, month=4, day=20),
                'text': 'Hi John',
                'from_uid': 21,
                'to_uid': 22
            }
        }
