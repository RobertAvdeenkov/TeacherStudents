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

mainpagerouter=APIRouter()

@mainpagerouter.get('/mainpage')
async def mainpage(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/mainpag.html')

@mainpagerouter.post('/mainpageSHOW')
async def mainpageSHOW(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    txt='<a href="/create" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Создать объявление</a><p></p><a href="/adlist" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Мои объявления</a><p></p>' if user.role=='tutor' else '<a href="/saves" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Избранные объявления</a><p></p>'
    ads=(await db.execute(select(Ad).options(selectinload(Ad.reviews)).filter(Ad.subject.ilike(f'%{data['subject']}%'), Ad.price<=int(data['price'] if data['price'] else  2147483647), Ad.location.ilike(f'%{data['location']}%')).order_by(desc(Ad.counter)))).all()
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
            <div class="info">{i[0].counter} просмотров</div>
            <div class="price">{i[0].price} ₽ / час</div>
            <div class="actions">
                <button onclick="book({i[0].id})">Записаться</button>
                <button onclick="feedback({i[0].id})">Оставить отзыв</button>
                <button onclick="like({i[0].id})">Добавить в избранные</button>
                <button class="secondary" onclick="viewProfile({i[0].id})">Подробнее</button>
            </div>
        </div>
        '''
    if txt:
        return {'message':txt}
    else:
        return {'message':'<h2>Пока ничего нет ¯\\_(ツ)_/¯</h2>'}


@mainpagerouter.get('/ad')
def ad(id:int=Query()):
    return FileResponse('templates/adINFO.html')

@mainpagerouter.post('/adSHOW')
async def adSHOW(data=Body(), db:AsyncSession=Depends(get_db), token=Cookie()):
    id=int(data['id'])
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.views)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    userd=res[0]
    result=(await db.execute(select(Ad).filter(Ad.id==int(id)))).first()
    if not result:
        raise HTTPException(400, 'Такого объявления еще нет!')
    ad=result[0]
    resultUSER=(await db.execute(select(User).filter(User.id==ad.user_id).options(selectinload(User.views)))).first()
    reviews=(await db.execute(select(Review).filter(Review.ad_id==ad.id))).all()
    if not resultUSER:
        return RedirectResponse('/', status_code=303)
    user=resultUSER[0] #type:ignore
    been=set()
    for i in userd.views:
        been.add(i.ad_id)
    if ad.id not in been:
        view=View(ad_id=ad.id, user_id=userd.id)
        ad.counter+=1
        db.add(view)
        await db.commit()
    INFO=''
    reviewTXT=''
    for index,i in enumerate(ad.info): #цикл для того, чтобы текст не был на одной строке
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
    <h2>{ad.counter} просмотров</h2>
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

@mainpagerouter.post('/save')
async def save(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    if user.role=='tutor':
        raise HTTPException(400, 'Недостаточно прав! Сохранять могут только ученики')
    result=(await db.execute(select(Save).filter(Save.ad_id==data['id'], Save.user_id==user.id))).first()
    if result:
        raise HTTPException(400, 'Объявление уже есть в избранных!')
    target=Save(user_id=user.id, ad_id=data['id'])
    db.add(target)
    await db.commit()