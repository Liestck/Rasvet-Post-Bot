from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import Config


engine = create_async_engine(
    Config.DATABASE_URL,
    echo=False,
    future=True
)

SessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:

    async with SessionFactory() as session:
        yield session
