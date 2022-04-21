"""
Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (MembershipType, Project, ProjectMembership,
                     ProjectPicture, Status, Tag, User, UserUrl)
from . import logger


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


class UserTagModel(BaseModel):
    """User Tag schema"""
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


class ProjectTagModel(UserTagModel):
    """Project Tag schema"""
    is_user_requirement: bool

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'text': 'Houston',
                'category': 'City',
                'is_user_requirement': False
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
    tags: list[UserTagModel]

    @classmethod
    async def from_orm(cls, user: User, async_session: AsyncSession) -> 'UserResultModel':
        """Fetch User data into schema"""
        return cls(
            urls=[UrlModel.from_orm(url) for url in
                  await UserUrl.get_user_urls(user.uid, async_session)],
            tags=[UserTagModel.from_orm(tag) for tag in
                  await Tag.get_tags(
                      async_session,
                      uid=user.uid)],
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
    tags: list[UserTagModel]

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


class ProjectMembershipRequestModel(BaseModel):
    """User project membership result schema"""
    uid: int
    membership_type: MembershipType

    class Config:
        schema_extra = {
            'example': {
                'uid': 22,
                'membership_type': MembershipType.ADMIN
            }
        }


class ProjectMembershipResultModel(ProjectMembershipRequestModel):
    """User project membership schema"""
    pid: int | None

    class Config:
        schema_extra = {
            'example': {
                'uid': 22,
                'pid': 21,
                'membership_type': MembershipType.ADMIN
            }
        }


class ProjectRequestModel(BaseModel):
    """Project update schema"""
    title: str
    status: Status
    description: str
    members: list[ProjectMembershipRequestModel]
    tags: list[ProjectTagModel]

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                'title': 'A Very Cool Project',
                'status': Status.AWAITING_TEAM,
                'description': 'I am editing the description.',
                'members': [ProjectMembershipRequestModel(
                    uid=22,
                    pid=21,
                    membership_type=MembershipType.ADMIN)],
                'tags': [ProjectTagModel(
                    text='Houston',
                    category='Location',
                    is_user_requirement=False)]
            }
        }


class ProjectResultModel(BaseModel):
    """Project retrieval schema"""
    pid: int
    title: str
    status: Status
    description: str
    pictures: list[str]
    members: list[ProjectMembershipResultModel]
    owner_uid: int
    tags: list[ProjectTagModel]

    @classmethod
    async def from_orm(cls, project: Project, async_session: AsyncSession) -> 'ProjectResultModel':
        """Fetch Project data into schema"""
        tags = await Tag.get_tags(
                      async_session,
                      pid=project.pid)
        logger.debug(tags)
        return cls(
            pictures=await ProjectPicture.get_project_pictures(project.pid, async_session),
            members=await ProjectMembership.get_project_memberships(project.pid, async_session),
            tags=[ProjectTagModel.from_orm(tag) for tag in
                  tags],
            **dict(project))

    class Config:
        schema_extra = {
            'example': {
                'pid': 21,
                'title': 'A Very Cool Project',
                'status': Status.AWAITING_TEAM,
                'description': 'This project is very cool. Please join.',
                'pictures': [
                    '8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4.png'
                ],
                'members': [ProjectMembershipResultModel(
                    uid=22,
                    pid=21,
                    membership_type=MembershipType.ADMIN)],
                'owner_uid': 21,
                'tags': [ProjectTagModel(
                    text='Lubbock',
                    category='Location',
                    is_user_requirement=False)]
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
                'from_uid': 1,
                'to_uid': 2
            }
        }

class MessageListModel(BaseModel):
    """User to User message list schema"""
    to_uid: int
    text: str

    class Config:
        schema_extra = {
            'example': {
                'to_uid': 2,
                'text': 'Hi John'
            }
        }
