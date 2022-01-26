from sqlalchemy import Column, Integer
from .db import Base

class Test(Base):
    __tablename__ = 'TEST'
    col = Column(Integer(), primary_key=True)