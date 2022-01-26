"""
CS Spin FastAPI app
"""

import asyncio
from fastapi import FastAPI
from .db import init_models, get_session

asyncio.run(init_models())

app = FastAPI()

@app.get('/')
async def index():
    return {'Hello': 'World'}