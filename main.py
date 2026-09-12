from fastapi import FastAPI
from models import Base
import os
from sqlalchemy import create_engine
from tasks.tasks import *
from tasks.authorize import*
from tasks.profile import*
from tasks.mainpage import*
from tasks.messaging import*

app=FastAPI()
DATABASE_URL=os.getenv('DATABASE_URL', 'sqlite:///tutor.db')
if '+asyncpg' in DATABASE_URL:
    DATABASE_URL=DATABASE_URL.replace('+asyncpg','')

engine=create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

app.include_router(router)
app.include_router(authrouter)
app.include_router(profilerouter)
app.include_router(mainpagerouter)
app.include_router(messagerouter)