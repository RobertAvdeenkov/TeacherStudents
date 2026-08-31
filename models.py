from sqlalchemy import Column,String,Integer,Float,DateTime,func,ForeignKey
from sqlalchemy.orm import DeclarativeBase,relationship

class Base(DeclarativeBase):pass

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String)
    password=Column(String)
    role=Column(String)

    ads=relationship('Ad',back_populates='user')
    bookings=relationship('Booking',back_populates='user')
    reviews=relationship('Review',back_populates='user')

class Ad(Base):
    __tablename__='ads'
    id=Column(Integer,primary_key=True)
    subject=Column(String)
    expirience=Column(Integer,default=0)
    price=Column(Integer)
    info=Column(String)
    rating=Column(Float,default=0)
    contact=Column(String)
    location=Column(String)

    user_id=Column(Integer,ForeignKey('users.id'))
    user=relationship('User', back_populates='ads')
    bookings=relationship('Booking', back_populates='ad')
    reviews=relationship('Review', back_populates='ad')

class Booking(Base):
    __tablename__='bookings'
    id=Column(Integer,primary_key=True)
    time=Column(DateTime,default=func.now())
    status=Column(String)
    contact=Column(String)

    user_id=Column(Integer,ForeignKey('users.id'))
    adr_id=Column(Integer,ForeignKey('ads.id'))
    user=relationship('User', back_populates='bookings')
    ad=relationship('Ad', back_populates='bookings')

class Review(Base):
    __tablename__='reviews'
    id=Column(Integer,primary_key=True)
    title=Column(String)
    stars=Column(Integer,default=5)

    user_id=Column(Integer,ForeignKey('users.id'))
    ad_id=Column(Integer,ForeignKey('ads.id'))
    user=relationship('User', back_populates='reviews')
    ad=relationship('Ad', back_populates='reviews')