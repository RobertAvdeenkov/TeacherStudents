from sqlalchemy import Column,String,Integer,Float,DateTime,func,ForeignKey,Boolean
from sqlalchemy.orm import DeclarativeBase,relationship

class Base(DeclarativeBase):pass

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String)
    password=Column(String)
    role=Column(String)
    limit=Column(Integer, default=0)

    ads=relationship('Ad',back_populates='user')
    bookings=relationship('Booking',back_populates='user')
    reviews=relationship('Review',back_populates='user')
    saves=relationship('Save', back_populates='user')
    messages=relationship('Message', back_populates='user')
    views=relationship('View', back_populates='user')


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
    counter=Column(Integer, default=0, nullable=False)

    user_id=Column(Integer,ForeignKey('users.id'))
    user=relationship('User', back_populates='ads')

    bookings=relationship('Booking', back_populates='ad', cascade="all, delete")
    reviews=relationship('Review', back_populates='ad', cascade="all, delete")
    saves=relationship('Save', back_populates='ad', cascade="all, delete")
    views=relationship('View', back_populates='ad', cascade="all, delete")

class Booking(Base):
    __tablename__='bookings'
    id=Column(Integer,primary_key=True)
    time=Column(DateTime,default=func.now())
    status=Column(String)
    contact=Column(String)

    user_id=Column(Integer,ForeignKey('users.id'))
    adr_id=Column(Integer,ForeignKey('ads.id'))
    accepted=Column(Boolean,default=False)
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

class Save(Base):
    __tablename__='saved'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    ad_id=Column(Integer,ForeignKey('ads.id'))
    user=relationship('User', back_populates='saves')
    ad=relationship('Ad', back_populates='saves')

class Message(Base):
    __tablename__='messages'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    to=Column(Integer)
    fro=Column(String, default='')
    txt=Column(String, default='')
    type=Column(String, default='info')
    created_at=Column(DateTime, default=func.now())
    booking_id=Column(Integer,default=None, nullable=True)

    info=Column(String, default='')

    status=Column(Boolean, default=False)
    user=relationship('User', back_populates='messages')

class View(Base):
    __tablename__='views'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'))
    ad_id=Column(Integer, ForeignKey('ads.id'))

    user=relationship('User', back_populates='views')
    ad=relationship('Ad', back_populates='views')