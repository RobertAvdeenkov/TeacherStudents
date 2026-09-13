import pytest_asyncio
import pytest
from fastapi.testclient import TestClient
from main import app,DATABASE_URL
from sqlalchemy import create_engine,delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from models import Base
from database import get_db
from models import *
from auth import create_token

client=TestClient(app)
engine=create_engine('sqlite:///test_tutor.db')
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)

def over_db():
    db=Session()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db]=over_db

@pytest.fixture
def db():
    db=Session()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_db(db):
    try:
        db.execute(delete(User))
        db.execute(delete(Ad))
        db.execute(delete(Booking))
        db.execute(delete(Review))
        db.execute(delete(Save))
        db.execute(delete(Message))
        db.execute(delete(View))
        db.commit()
    finally:
        db.close()

def create_user(db):
    user=User(name='test', password='123', role='tutor')
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_token(str(user.name))

def test_profile(db):
    token=create_user(db)
    response=client.get('/profile', cookies={'token':token})

    assert response.status_code==200
