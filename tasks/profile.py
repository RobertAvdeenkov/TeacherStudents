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

profilerouter=APIRouter()

@profilerouter.get('/profile')
async def profile(token=Cookie(), db:AsyncSession=Depends(get_db)):
   get_by_token(token)
   return FileResponse('templates/profile.html')

@profilerouter.post('/profileSHOW')
async def profileSHOW(token=Cookie(),db:AsyncSession=Depends(get_db)):
    res=(await db.execute(select(User).options(selectinload(User.bookings)).filter(User.name==get_by_token(token)))).first()
    if not(res):
        raise HTTPException(401, 'Вы не зарегистрированы!')
    user=res[0]
    booking=''
    counter=0
    overall=0
    if user.role=='student':
        res=(await db.execute(select(Booking).filter(Booking.user_id==user.id).options(selectinload(Booking.ad)))).all()
        for i in res:
            if i[0].accepted==True:
                ad=i[0].ad
                booking+=f'''
                <h3>{ad.subject}, {ad.contact}</h3>
                <h4>{i[0].time}<h4>
                <button onclick="send({i[0].id})" style="background-color: red;">Отменить</button>
                <hr>
                '''
    else:
        ads=(await db.execute(select(Ad).filter(Ad.user_id==user.id).options(selectinload(Ad.bookings)))).all()
        for i in ads:
            overall+=i[0].counter
            for book in i[0].bookings:
                if book.accepted==True:
                    counter+=1
                    booking+=f'''
                    <h3>{i[0].subject}, {book.contact}</h3>
                    <h4>{book.time}<h4>
                    <button onclick="send({book.id})" style="background-color: red;">Отменить</button>
                    <hr>
                    '''
    txt=f'''
    <div class="tutor">
        <h2>{user.name}</h2>
        <h3 style="color: #888;">{f'Репетитор<br>Лимит {user.limit}' if user.role=='tutor' else 'Ученик'}</h3>
    </div>
    <hr>
    {f'''
    <h2>Установить лимит бронирований</h2>
    <select onchange="setLimit()" id="limitset">
        <option value="0">Отключить лимит</option>
        <option value="5">5</option>
        <option value="10" selected>10</option>
        <option value="15">15</option>
        <option value="20">20</option>
    </select>
    <hr>
    <h2>Статистика объявлений</h2>
    <div class="tutor">
        <h3>Всего просмотров: {overall}</h3>
        <h3>Всего подтвержденных бронирований: {counter}</h3>
        <h3>Вы загружены на {round(counter / user.limit * 100) if user.limit else 0}%</h3>
    </div>''' if user.role=='tutor' else ''}
    <hr>
    <h2>Ваши бронирования</h2>
    <div class="tutor">
        {booking if booking else '<h3>У вас нет бронирований ¯\\_(ツ)_/¯</h3>'}
    </div>
    '''
    return {'message':txt}

@profilerouter.post('/deleteBOOKING')
async def deletebooking(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        raise HTTPException(401, 'Вы не зарегистрированы')
    user=res[0]
    adres=(await db.execute(select(Booking).filter(Booking.id==data['id']).options(selectinload(Booking.ad)))).first()
    if not adres:
        return RedirectResponse('/mainpage',status_code=303)
    target=adres[0]
    ad=adres[0].ad
    if user.id==ad.user_id or user.id==target.user_id:
        await db.delete(target)
        await db.commit()
        return {'status':'ok'}
    else:
        raise HTTPException(404, 'Такой брони нет')

@profilerouter.post('/setlimit')
async def set_limit(db:AsyncSession=Depends(get_db), token=Cookie(), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.messages)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    if data['data']==0:
        user.limit=None
        await db.commit()
        return {'status':'ok'}
    else:
        user.limit=data['data']
        await db.commit()
        return {'status':'ok'}