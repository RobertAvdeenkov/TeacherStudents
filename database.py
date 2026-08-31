from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
import os
from sqlalchemy.orm import sessionmaker

DATABASE_URL=os.getenv('DATABASE_URL','sqlite+aiosqlite:///tutor.db')
engine=create_async_engine(DATABASE_URL)
SessionLocal=sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) #type:ignore

async def get_db():
    async with SessionLocal() as db: #type:ignore
        try:
            yield db
        finally:
            await db.close()