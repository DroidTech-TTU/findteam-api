from sqlalchemy import Column, Integer, String, ForeignKey
from bcrypt import hashpw
from .db import Base

# https://variable-scope.com/posts/storing-and-verifying-passwords-with-sqlalchemy

class User(Base):
    __tablename__ = 'USER'
    uid = Column(
        Integer(),
        primary_key=True,
        autoincrement=True)
    first_name = Column(String(length=32))
    middle_name = Column(String(length=32))
    last_name = Column(String(length=32))
    email = Column(String(length=254))
    password = None # Todo
    location = Column(String(length=254))
    profile_picture = Column(String(length=32)) # 320x320 png
    
    def verify_password(self, password): # Todo
        return password == hashpw(password, self.password)

class UserSkill(Base):
    __tablename__ = 'USER_SKILL'
    uid = Column(
        Integer(),
        ForeignKey('user.uid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    skill = Column(String(length=32))

class UserUrl(Base):
    __tablename__ = 'USER_URL'
    uid = Column(
        Integer(),
        ForeignKey('user.uid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    url = Column(String(2000))

class UserInterest(Base):
    __tablename__ = 'USER_INTEREST'
    uid = Column(
        Integer(),
        ForeignKey('user.uid', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True)
    interest = Column(String(32))