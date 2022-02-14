"""
FindTeam Pydantic schemas
"""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel


class Permission(IntEnum):
    READ = 0
    READ_WRITE = 1
    READ_WRITE_EDIT = 2


class User(BaseModel):
    uid: int

    class Config:
        orm_mode = True
