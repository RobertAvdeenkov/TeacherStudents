from jose import jwt
import os
from datetime import datetime,timedelta
from fastapi import HTTPException

SECRET=os.getenv('SECRET','arv')
ALGORITHM=os.getenv('ALGORITHM','HS256')

def create_token(user:str):
    payload={
        'sub':user,
        'exp':datetime.now()+timedelta(hours=1)
    }
    return jwt.encode(payload,SECRET,ALGORITHM)

def get_by_token(token:str):
    try:
        data=jwt.decode(token,SECRET,ALGORITHM)
        return data['sub']
    except:
        raise HTTPException(401, 'Проблема с токеном! Зарегистрируйтесь или зайдите в аккаунт')