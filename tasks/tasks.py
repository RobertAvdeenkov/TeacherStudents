from fastapi import APIRouter,Query,Body,Depends,HTTPException,Cookie,Form
from fastapi.responses import * #type:ignore
from database import get_db,AsyncSession
from sqlalchemy import select, or_
from models import*
import bcrypt
from auth import*
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime

router=APIRouter()

@router.get('/')
async def log_in():
    return FileResponse('templates/login.html')

@router.get('/register')
async def reg_in():
    return FileResponse('templates/register.html')

@router.post('/reg')
async def register(data=Body(),db:AsyncSession=Depends(get_db)):
    result=(await db.execute(select(User).filter(User.name==data['name']))).first()
    if result:
        raise HTTPException(400, 'Пользователь с таким логин уже есть!')
    target=User(name=data['name'], password=bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode(), role=data['role'])
    db.add(target)
    await db.commit()
    return {'status':'ok', 'redirect_url':'/'}

@router.post('/login')
async def login(data=Body(), db:AsyncSession=Depends(get_db)):
    result=(await db.execute(select(User).filter(User.name==data['name']))).first()
    if not result:
        raise HTTPException(400, 'Такого пользователя еще нет!')
    user=result[0]
    if not(bcrypt.checkpw(data['password'].encode(), user.password.encode())):
        raise HTTPException(400, 'Неправильный логин или пароль')
    token=create_token(user.name)
    return {'status':'ok','redirect_url':f'/mainpageRED?token={token}'}

@router.get('/mainpageRED')
async def mainpageRED(token=Query()):
    get_by_token(token)
    response=RedirectResponse('/mainpage')
    response.set_cookie(key='token',value=token, max_age=3600, path='/')
    return response

@router.get('/mainpage')
async def mainpage(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/mainpag.html')

@router.post('/mainpageSHOW')
async def mainpageSHOW(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    print(data)
    txt='<a href="/create" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Создать объявление</a><p></p><a href="/adlist" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Мои объявления</a><p></p>' if user.role=='tutor' else ''
    ads=(await db.execute(select(Ad).options(selectinload(Ad.reviews)).filter(Ad.subject.ilike(f'%{data['subject']}%'), Ad.price<=int(data['price'] if data['price'] else  2147483647), Ad.location.ilike(f'%{data['location']}%')))).all()
    for i in ads:
        rating=0
        counter=0
        for j in i[0].reviews:
            rating+=j.stars
            counter+=1
        overall=round(rating/counter,1) if counter>0 else 0
        txt+=f'''
        <div class="tutor">
            <h2>Учитель {i[0].subject}</h2>
            <div class="info">{i[0].expirience} года опыта</div>
            <div class="info">⭐ {overall} ({counter} отзывов)</div>
            <div class="price">{i[0].price} ₽ / час</div>
            <div class="actions">
                <button onclick="book({i[0].id})">Записаться</button>
                <button onclick="feedback({i[0].id})">Оставить отзыв</button>
                <button class="secondary" onclick="viewProfile({i[0].id})">Подробнее</button>
            </div>
        </div>
        '''
    if txt:
        return {'message':txt}
    else:
        return {'message':'<h2>Пока ничего нет ¯\\_(ツ)_/¯</h2>'}


@router.get('/ad')
def ad(id:int=Query()):
    print(id)
    return FileResponse('templates/adINFO.html')


@router.post('/adSHOW')
async def adSHOW(data=Body(), db:AsyncSession=Depends(get_db)):
    id=int(data['id'])
    result=(await db.execute(select(Ad).filter(Ad.id==int(id)))).first()
    if not result:
        raise HTTPException(400, 'Такого объявления еще нет!')
    ad=result[0]
    resultUSER=(await db.execute(select(User).filter(User.id==ad.user_id))).first()
    reviews=(await db.execute(select(Review).filter(Review.ad_id==ad.id))).all()
    user=resultUSER[0] #type:ignore
    INFO=''
    reviewTXT=''
    for index,i in enumerate(ad.info):
        if index%60==0 and index!=0:
            INFO+=i+'<br>'
        else:
            INFO+=i

    for i in reviews:
        reviewTXT+=f'''
        <div class="tutor">
            <h3>{i[0].stars} звезд</h3>
            <h4>{i[0].title}</h4>
        </div>
        '''
    txt=f'''
    <h1>{user.name}</h1>
    <h2>{ad.subject}, стаж {ad.expirience} лет</h2>
    <h2>Цена: {ad.price} руб за час</h2>
    <h2>{ad.location}</h2>
    <h3>{INFO}</h3>
    <p></p>
    <h3>Контактная информация: {ad.contact}</h3>
    <hr>
    <h2>Отзывы</h2>
    {reviewTXT}
    '''
    return {'message':txt}
    
@router.get('/profile')
async def profile(token=Cookie(), db:AsyncSession=Depends(get_db)):
   get_by_token(token)
   return FileResponse('templates/profile.html')

@router.post('/profileSHOW')
async def profileSHOW(token=Cookie(),db:AsyncSession=Depends(get_db)):
    res=(await db.execute(select(User).options(selectinload(User.bookings)).filter(User.name==get_by_token(token)))).first()
    if not(res):
        raise HTTPException(401, 'Вы не зарегистрированы!')
    user=res[0]
    booking=''
    print(user.role)
    if user.role=='student':
        res=(await db.execute(select(Booking).filter(Booking.user_id==user.id).options(selectinload(Booking.ad)))).all()
        for i in res:
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
            for book in i[0].bookings:
                booking+=f'''
                <h3>{i[0].subject}, {book.contact}</h3>
                <h4>{book.time}<h4>
                <button onclick="send({i[0].id})" style="background-color: red;">Отменить</button>
                <hr>
                '''
    txt=f'''
    <div class="tutor">
        <h2>{user.name}</h2>
        <h3 style="color: #888;">{'Репетитор' if user.role=='tutor' else 'Ученик'}</h3>
    </div>
    <hr>
    <h2>Ваши бронирования</h2>
    <div class="tutor">
        {booking if booking else '<h3>У вас нет бронирований ¯\\_(ツ)_/¯</h3>'}
    </div>
    '''
    return {'message':txt}

@router.post('/deleteBOOKING')
async def deletebooking(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    print(data)
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        raise HTTPException(401, 'Вы не зарегистрированы')
    adres=(await db.execute(select(Ad).filter(Ad.id==int(data['id'])))).first()
    if not adres:
        print(adres)
        return RedirectResponse('/mainpage',status_code=303)
    ad=adres[0]
    user=res[0]
    if ad.user_id!=user.id:
        target=(await db.execute(select(Booking).filter(Booking.id==int(data['id']), Booking.user_id==user.id))).first()
    else:
        print('dddd')
        target= (await db.execute(select(Booking).filter(Booking.id==int(data['id'])))).first()
    print(target,'target')
    if not target:
        raise HTTPException(400, 'Такого бронирования нет!')
    await db.delete(target[0])
    await db.commit()

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
def booking(id=Query()):
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
    date=date.replace('T',' ')
    date=date.split(' ')
    date[0]=date[0].split('-')
    date[1]=date[1].split(':')
    print(date)
    data=datetime(year=int(date[0][0]), month=int(date[0][1]),day=int(date[0][2]), hour=int(date[1][0]), minute=int(date[1][1]))
    target=Booking(time=data, status='ok',user_id=user.id, adr_id=tutor_id,contact=contact)
    db.add(target)
    await db.commit()
    return RedirectResponse('/mainpage',status_code=303)

@router.get('/create')
async def createROOT(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/create.html')

@router.post('/createAD')
async def create(token=Cookie(), db:AsyncSession=Depends(get_db), subject=Form(), exp:int=Form(),price:int=Form(),info=Form(),contact=Form(),location=Form()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        return HTTPException(401, 'вы не зарегистрированы')
    user=res[0]
    if user.role=='student':
        return RedirectResponse('/mainpage',status_code=303)
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
    print(user.ads)
    for i in user.ads:
        txt+=f'''
        <div class="tutor">
            <h2>{i.subject}, {i.location}</h2>
            <h3>{i.price}</h3>
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