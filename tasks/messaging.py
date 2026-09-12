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

messagerouter=APIRouter()

@messagerouter.get('/message')
async def message(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/message.html')

@messagerouter.post('/messageSHOW')
async def messageSHOW(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.messages)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    txt=''
    if data['data']=='others':
        rees=(await db.execute(select(Message).filter(Message.to==user.id).order_by(desc(Message.created_at)))).all()
        for j in rees:
            i=j[0]
            if i.type=='info':
                txt+=f'''
                <div class="tutor">
                    <h2>От {i.fro}</h2>
                    <h3>{i.txt}</h3>
                    <h4>{i.type}</h4>
                    <h4>Отправлено {i.created_at}</h4>
                </div>
                '''
            elif i.type=="accept":
                txt+=f'''
                <div class="tutor">
                    <h2>{i.fro} хочет учиться у вас!</h2>
                    <button onclick="accept({i.user_id}, {i.booking_id}, {i.id}, 'yes')">Принять</button>
                    <button onclick="accept({i.user_id}, {i.booking_id}, {i.id}, 'no')">Отклонить</button>
                    <h3>Отправлено {i.created_at}</h3>
                </div>
                '''
            elif i.type=='system':
                txt+=f'''
                    <div class="tutor">
                        <h2>Уведомление системы</h2>
                        <h3>{i.info}</h3>
                        <h3>Отправлено {i.created_at}</h3>
                    </div>

                '''
    elif data['data']=='mine':
        for i in user.messages:
            txt+=f'''
            <div class="tutor">
                <h3>Текст: {i.txt}</h3>
                <h3>{i.created_at}</h3>
                <button onclick="send({i.id})">Удалить сообщение</button>
            </div>

            '''
    if txt:
        return {'message':txt}
    else:
        return {'message':'''
                <div class="tutor">
                    <h2>У вас нет уведомлений ¯\\_(ツ)_/¯</h2>
                </div>
                '''}

@messagerouter.get('/sending')
async def send_menu(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/send.html')

@messagerouter.post('/sendMESSAGE')
async def send_message(token=Cookie(), db:AsyncSession=Depends(get_db), to=Form(), txt=Form()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    nam=(await db.execute(select(User).filter(User.name==to))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    if not nam:
        raise HTTPException(400, 'Такого пользователя нет!')
    target=nam[0]
    message=Message(user_id=user.id, to=target.id, txt=txt, fro=user.name)
    db.add(message)
    await db.commit()
    return RedirectResponse('/mainpage',status_code=303)

@messagerouter.post('/deleteMESSAGE')
async def delete_message(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.messages)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    for i in user.messages:
        if i.id==int(data['id']):
            await db.delete(i)
            await db.commit()
            return RedirectResponse('/mainpage',status_code=303)
    raise HTTPException(400, 'У вас нет такого сообщения')

@messagerouter.post('/accept')
async def accept(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.messages)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    mess=(await db.execute(select(Message).filter(Message.id==data['mes']))).first()
    if not mess:
        raise HTTPException(400, 'Такого сообщения нет')
    mes=mess[0]
    if data['ver']=='no':
        book=(await db.execute(select(Booking).filter(Booking.id==data['id'], Booking.user_id==data['user_id']))).first()
        if not book:
            raise HTTPException(400, 'Такой брони нет')
        target=Message(to=int(data['user_id']), txt=f'{user.name} отклонил ваше предложение', info=f'{user.name} отклонил ваше предложение', type='system')
        db.add(target)
        await db.delete(book[0])
        await db.delete(mes)
        await db.commit()
        return RedirectResponse('/mainpage',status_code=303)
    elif data['ver']=="yes":
        book=(await db.execute(select(Booking).filter(Booking.id==data['id'], Booking.user_id==data['user_id']))).first()
        if not book:
            raise HTTPException(400, 'Такой брони нет')
        book[0].accepted=True
        target=Message(to=int(data['user_id']), txt=f'{user.name} одобрил ваше предложение', info=f'{user.name} одобрил ваше предложение', type='system')
        db.add(target)
        await db.delete(mes)
        await db.commit()
        return RedirectResponse('/mainpage',status_code=303)
