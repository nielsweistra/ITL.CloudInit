from fastapi import FastAPI
from routers import router
from models import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

app = FastAPI()

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost/tpmbootstrap"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base.metadata.create_all(bind=engine)

app.include_router(router)