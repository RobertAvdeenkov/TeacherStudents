from fastapi import APIRouter,Query,Body,Depends,HTTPException,Cookie,Form
from fastapi.responses import * #type:ignore
from database import get_db,AsyncSession
from sqlalchemy import select,desc,text,func
from models import*
from auth import*
from sqlalchemy.orm import selectinload

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
    if user.indicator>=100 and user.warned==False:
        mm=Message(to=user.id, txt='Вы загружены на 100%!', type='system', info='Вы загружены на 100%!')
        db.add(mm)
        user.warned=True
    txt='<a href="/create" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Создать объявление</a><p></p><a href="/adlist" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Мои объявления</a><p></p>' if user.role=='tutor' else '<a href="/saves" style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;">Избранные объявления</a><p></p>'
    ads=(await db.execute(select(Ad).options(selectinload(Ad.reviews)).filter(Ad.subject.ilike(f'%{data['subject']}%'), Ad.price<=int(data['price'] if data['price'] else  2147483647), Ad.location.ilike(f'%{data['location']}%')).order_by(desc(Ad.counter)))).all()
    allstudents=(await db.scalar(select(func.count(User.id)).filter(User.role=='student')))
    alltutors=(await db.scalar(select(func.count(User.id)).filter(User.role=='tutor')))
    allbookings=(await db.scalar(select(func.count(Booking.id))))
    txt+=f'''
    <h3>Всего учеников: {allstudents}</h3>
    <h3>Всего репетиторов: {alltutors}</h3>
    <h3>Всего активных броней: {allbookings}</h3>
    <p></p>
    '''
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
                {f'''<button onclick="book({i[0].id})">Записаться</button>
                {f'<button onclick="feedback({i[0].id})">Оставить отзыв</button>' if user.status==True else ''}
                <button onclick="like({i[0].id})">Добавить в избранные</button>''' if user.role=='student' else ''}
                <button class="secondary" onclick="viewProfile({i[0].id})">Подробнее</button>
            </div>
        </div>
        '''
    await db.commit()
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
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.views), selectinload(User.given)))).first()
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
    recommendations=(await db.execute(select(Recommend).filter(Recommend.to_user_id==user.id).options(selectinload(Recommend.user)).order_by(desc(Recommend.created_at)).limit(5))).all()
    recomendation_txt='<h2>'
    for i in recommendations:
        recomendator=i[0].user
        recomendation_txt+=f'{recomendator.name}<br>'
    recomendation_txt+='</h2>'
    been=set()
    for i in userd.views:
        been.add(i.ad_id)
    if ad.id not in been:
        view=View(ad_id=ad.id, user_id=userd.id)
        ad.counter+=1
        db.add(view)
        await db.commit()
    given=False
    for i in userd.given:
        if i.to_user_id==user.id:
            given=True
            break
        given=False
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
    <h1>{user.name}{'<br>⭐Доверенный пользователь⭐' if user.status==True else ''}</h1>
    <h2>Последний раз в сети: {user.last_seen.strftime('%d.%m.%Y %H:%M') if user.last_seen else 'Скрыт'}</h2>
    <h2>{ad.counter} просмотров</h2>
    {f'<button style="color: #000000; background-color: #ffcc08; text-decoration:none; padding: 5px; border-radius: 5px;font-weight: bold;" onclick="recommend({user.id})">{'Порекомендовать' if not(given) else 'Убрать рекомендацию'} учителя</button>' if userd.role=='tutor' and userd.id!=ad.user_id and userd.status==True else ''}
    <h2>{ad.subject}, стаж {ad.expirience} лет</h2>
    <h2>Цена: {ad.price} руб за час</h2>
    <h2>{ad.location}</h2>
    <h3>{INFO}</h3>
    <p></p>
    <h3>Контактная информация: {ad.contact}</h3>
    <hr>
    <h2>Рекомендуют</h2>
    {recomendation_txt if recomendation_txt!='<h2></h2>' else '<h2>Рекомендаций пока нет ¯\\_(ツ)_/¯</h2>'}
    <hr>
    <h2>Отзывы</h2>
    {reviewTXT if reviewTXT else '<h2>Отзывов пока нет ¯\\_(ツ)_/¯</h2>'}
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

@mainpagerouter.get('/logout')
async def logout(token=Cookie()):
    response=RedirectResponse('/',status_code=303)
    response.delete_cookie('token', path='/')
    return response

@mainpagerouter.post('/recommend')
async def recommend(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    res=(await db.execute(select(User).filter(User.name==get_by_token(token)).options(selectinload(User.given)))).first()
    if not res:
        return RedirectResponse('/',status_code=303)
    user=res[0]
    if user.role=='student':
        raise HTTPException(400, 'Вы не можете рекомендовать репетиторов')
    for i in user.given:
        if i.to_user_id==int(data['id']):
            await db.delete(i)
            await db.commit()
            return {'status':'ok'}
    target=Recommend(user_id=user.id, to_user_id=int(data['id']))
    message=Message(to=int(data['id']),txt=f'{user.name} рекомендует вас!', info=f'{user.name} рекомендует вас', type='system')
    db.add_all([target,message])
    await db.commit()

@mainpagerouter.get('/tops')
async def tops(token=Cookie()):
    get_by_token(token)
    return FileResponse('templates/tops.html')

@mainpagerouter.post('/topsSHOW')
async def topsSHOW(token=Cookie(), db:AsyncSession=Depends(get_db), data=Body()):
    ex=text(f'''
        select users.name as name, AVG(reviews.stars) as star, COUNT(ads.counter) as views, users.role as role
        from users
        INNER JOIN ads on users.id=ads.user_id
        INNER JOIN reviews on ads.id=reviews.ad_id
        GROUP BY users.name, users.role, ads.subject
        HAVING ads.subject ilike '%{data['data']}%'
        ORDER by AVG(reviews.stars), COUNT(ads.counter) DESC
        LIMIT 10
    ''' if data['data'] else '''
    select users.name as name, AVG(reviews.stars) as star, COUNT(ads.counter) as views, users.role as role
    from users
    INNER JOIN ads on users.id=ads.user_id
    INNER JOIN reviews on ads.id=reviews.ad_id
    GROUP BY users.name, users.role
    HAVING users.role='tutor'
    ORDER by AVG(reviews.stars), COUNT(ads.counter) DESC
    LIMIT 10
    ''')
    result=(await db.execute(ex)).all()
    if not result:
        return {'message':'<div class="tutor"><h2>Лидеров пока нет ¯\\_(ツ)_/</h2></div>'}
    txt=f''
    for index,i in enumerate(result):
        txt+=f'''
        <div class="tutor">
            <h2>{'🏆' if index+1==1 else ''}{'🥈' if index+1==2 else ''}{'🥉' if index+1==3 else ''}№{index+1} {i[0]}</h2>
            <h3>Рейтинг: {round(float(i[1]),2)}</h3>
            <h3>Всего просмотров: {i[2]}</h3>
        </div>
        '''
    return {'message':txt}