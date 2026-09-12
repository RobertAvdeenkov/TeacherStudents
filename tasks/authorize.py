from fastapi import APIRouter,Query,Body,Depends,HTTPException,Cookie,Form
from fastapi.responses import * #type:ignore
from database import get_db,AsyncSession
from sqlalchemy import select, or_,desc
from models import*
import bcrypt
from auth import*
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime

authrouter=APIRouter()

@authrouter.get('/')
async def log_in():
    return FileResponse('templates/login.html')

@authrouter.get('/register')
async def reg_in():
    return FileResponse('templates/register.html')

@authrouter.post('/reg')
async def register(data=Body(),db:AsyncSession=Depends(get_db)):
    result=(await db.execute(select(User).filter(User.name==data['name']))).first()
    if result:
        raise HTTPException(400, 'Пользователь с таким логин уже есть!')
    target=User(name=data['name'], password=bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode(), role=data['role'])
    db.add(target)
    await db.commit()
    return {'status':'ok', 'redirect_url':'/'}

@authrouter.post('/login')
async def login(data=Body(), db:AsyncSession=Depends(get_db)):
    result=(await db.execute(select(User).filter(User.name==data['name']))).first()
    if not result:
        raise HTTPException(400, 'Такого пользователя еще нет!')
    user=result[0]
    if not(bcrypt.checkpw(data['password'].encode(), user.password.encode())):
        raise HTTPException(400, 'Неправильный логин или пароль')
    token=create_token(user.name)
    return {'status':'ok','redirect_url':f'/mainpageRED?token={token}'}

@authrouter.get('/mainpageRED')
async def mainpageRED(token=Query()):
    get_by_token(token)
    response=RedirectResponse('/mainpage')
    response.set_cookie(key='token',value=token, max_age=3600, path='/')
    return response