from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable, cast
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_session


class DbSessionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        
        async for session in get_session():
            data["session"] = cast(AsyncSession, session)
            return await handler(event, data)
