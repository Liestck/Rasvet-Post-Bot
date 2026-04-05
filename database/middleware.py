from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from app.database.db import SessionFactory


class DbSessionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:

        async with SessionFactory() as session:
            data["session"] = session
            return await handler(event, data)