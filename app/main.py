"""
FindTeam FastAPI app
"""
__author__ = 'DroidTech'
__version__ = '0.2.12.22'

import asyncio
from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import schemas
from .db import get_db, init_models

asyncio.run(init_models())

app = FastAPI()


@app.get('/')
async def index():
    return {'findteam-api': __version__}


@app.get('/users', response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db)):
    return db.query().all()
