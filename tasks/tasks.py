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

router=APIRouter()

@router.get('/review')
async def review(id=Query()):
    return FileResponse('templates/review.html')

@router.post('/feedback')
async def feedback(tutor_id:int=Form(), category=Form(),text:str=Form(), token=Cookie(), db:AsyncSession=Depends(get_db)):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        raise HTTPException(401, 'Вы не зарегистрированы')
    user=res[0]
    target=(await db.execute(select(Review).filter(Review.user_id==user.id, Review.ad_id==int(tutor_id)))).first()
    if target:
        return RedirectResponse('/mainpage',status_code=303)
    target=Review(title=text,stars=int(category),ad_id=int(tutor_id), user_id=user.id)
    db.add(target)
    await db.commit()
    return RedirectResponse('/mainpage',status_code=303)

@router.get('/booking')
async def booking(id=Query()):
    return FileResponse('templates/booking.html')

@router.post('/book')
async def book(token=Cookie(), db:AsyncSession=Depends(get_db), tutor_id:int=Form(), date=Form(),contact:str=Form()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        raise HTTPException(401, 'Вы не зарегистрированы')
    user=res[0]
    if user.role=='tutor':
        return RedirectResponse('/mainpage',status_code=303)
    ress=(await db.execute(select(Ad).filter(Ad.id==tutor_id))).first()
    if not ress:
        return RedirectResponse('/mainpage',status_code=303)
    ad=ress[0]
    date=date.replace('T',' ') #мы получаем дату в формате день:месяц:год часы:минуты
    date=date.split(' ')
    date[0]=date[0].split('-')
    date[1]=date[1].split(':')
    now=datetime.now()
    data=datetime(year=int(date[0][0]) if int(date[0][0])<9999 else now.year, month=int(date[0][1]),day=int(date[0][2]), hour=int(date[1][0]), minute=int(date[1][1]))
    if data<now or data.year-now.year>100:
        raise HTTPException(400, 'Введите корректную дату!')
    target=Booking(time=data, status='ok',user_id=user.id, adr_id=tutor_id,contact=contact)
    db.add(target)
    await db.commit()
    await db.refresh(target)
    message=Message(fro=user.name, user_id=user.id, type='accept', to=ad.user_id, booking_id=target.id, txt='Заявка на обучение')
    db.add(message)
    await db.commit()
    return RedirectResponse('/mainpage',status_code=303)

@router.get('/create')
async def createROOT(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/create.html')

@router.post('/createAD')
async def create(token=Cookie(), db:AsyncSession=Depends(get_db), subject=Form(), exp=Form(),price=Form(),info=Form(),contact=Form(),location=Form()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        return HTTPException(401, 'вы не зарегистрированы')
    user=res[0]
    if user.role=='student':
        return RedirectResponse('/mainpage',status_code=303)
    if not(str(exp).isdigit()) or not(str(price).isdigit()):
        raise HTTPException(400, 'Введите корректные данные')
    if  int(exp)<-1: exp=0
    if int(price)<-1:price=0

    target=Ad(subject=subject, expirience=int(exp), price=int(price), info=info,contact=contact,location=location, user_id=user.id)
    db.add(target)
    await db.commit()
    return RedirectResponse('/mainpage',status_code=303)

@router.get('/adlist')
async def adlist(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/infos.html')

@router.post('/adlistSHOW')
async def adlistSHOW(token=Cookie(), db:AsyncSession=Depends(get_db)):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.ads)))).first()
    if not res:
        return HTTPException(401, 'вы не зарегистрированы')
    user=res[0]
    if user.role=='student':
        return RedirectResponse('/mainpage',status_code=303)
    txt=''
    for i in user.ads:
        txt+=f'''
        <div class="tutor">
            <h2>{i.subject}, {i.location}</h2>
            <h3>{i.price}</h3>
            <h3>{i.counter} просмотров</h3>
            <a href="/ad?id={i.id}" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Посмотреть объявление</a>
            <button onclick="delet({i.id})" style="background-color: red; color: white">Удалить объявление</button>
        </div>
        '''
    if txt:
        return {'message':txt}
    else: return {'message':'<h2>У вас нет объявлений ¯\\_(ツ)_/¯</h2>'}

@router.post('/removeBOOKING')
async def remove(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.ads)))).first()
    if not res:
        raise HTTPException(401, 'вы не зарегистрированы')
    user=res[0]
    result=(await db.execute(select(Ad).filter(Ad.id==int(data['id'])))).first()
    if not result:
        raise HTTPException(400, 'Такого объявления нет')
    ad=result[0]
    if user.id!=ad.user_id:
        raise HTTPException(400, 'Недостаточно прав!')
    await db.delete(ad)
    await db.commit()
    return {'status':'ok'}

@router.get('/saves')
async def savesList(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/saved.html')

@router.post('/saveSHOW')
async def saveSHOW(token=Cookie(), db:AsyncSession=Depends(get_db)):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not(res):
        return RedirectResponse('/',status_code=303)
    user=res[0]
    result=(await db.execute(select(Save).filter(Save.user_id==user.id).options(selectinload(Save.ad)))).all()
    txt='<h2>Список</h2><p></p>'
    for i in result:
        ad=i[0].ad
        txt+=f'''
        <div class="tutor">
            <h3>Предмет: {ad.subject}</h3>
            <h3>Место: {ad.location}</h3>
            <h3>Контактная информация: {ad.contact}</h3>
            <a href="/ad?id={ad.id}" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Посмотреть объявление</a>
            <button style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;" onclick="send({i[0].id})">Убрать объявление</button>
        </div>
        '''
    if txt!='<h2>Список</h2><p></p>':
        return {'message':txt}
    else:
        return {'message':'<div class="tutor"><h2>У вас нет избранных объявлений¯\\_(ツ)_/¯</h2></div>'}

@router.post('/deleteSAVE')
async def deleteSAVE(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.saves)))).first()
    if not(res):
        return RedirectResponse('/', status_code=303)
    user=res[0]
    for i in user.saves:
        if i.id==int(data['id']):
            target=i
    if not i:
        raise HTTPException(400, 'Объявления нет в избранных!')
    await db.delete(target)
    await db.commit()