from colorama import Fore, Style

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, Channel, PermEnum
from app.utils.logger import Logger
from app.config import Config


class Users:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, tg_user) -> User:
        """Получить пользователя по tg_id или создать нового"""

        stmt = select(User).where(User.tg_id == tg_user.id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            Logger.User.exists(tg_user)
            return user

        # Если пользователь владелец бота
        perm = PermEnum.OWNER if tg_user.id == Config.OWNER_TGID else PermEnum.DEFAULT

        user = User(
            tg_id=tg_user.id,
            username=tg_user.username,
            perm=perm
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        Logger.User.new(tg_user.id, tg_user.username)

        return user

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        """Получить пользователя по tg_id"""
        stmt = select(User).where(User.tg_id == tg_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def is_owner(self, user: User) -> bool:
        """Проверка, является ли пользователь владельцем бота"""
        return user.perm == PermEnum.OWNER

    def is_premium(self, user: User) -> bool:
        """Проверка, является ли пользователь премиум"""
        return user.perm in {PermEnum.PREMIUM, PermEnum.OWNER}


class Channels:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_channels(self, owner_tg_id: int) -> list[Channel]:
        """Получить список каналов пользователя по tg_id"""
        stmt = select(Channel).where(
            Channel.owner_id == owner_tg_id,
            Channel.enabled.is_(True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_channel(
        self,
        owner_tg_id: int,
        channel_id: int
    ) -> Channel | None:
        """Получить конкретный канал пользователя"""
        
        stmt = select(Channel).where(
            Channel.owner_id == owner_tg_id,
            Channel.channel_id == channel_id,
            Channel.enabled.is_(True)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def can_add(self, owner_tg_id: int, user_perm: PermEnum) -> bool:
        """
        Проверка, может ли пользователь добавить канал.
        - DEFAULT: 1 канал
        - PREMIUM: 3 канала
        """
        if user_perm == PermEnum.OWNER:
            return True

        channels = await self.get_user_channels(owner_tg_id)
        
        if user_perm == PermEnum.PREMIUM:
            return len(channels) < 3
        
        # DEFAULT
        return len(channels) < 1

    async def add(
        self,
        channel_id: int,
        title: str,
        owner_tg_id: int,
        can_post: bool,
        channelname: str | None = None
    ) -> tuple[Channel, bool]:
        """
        Добавить канал.
        Возвращает (channel, exists)
        exists=True  -> канал уже был активен
        exists=False -> канал добавлен ИЛИ восстановлен
        """

        stmt = select(Channel).where(Channel.channel_id == channel_id)
        result = await self.session.execute(stmt)
        channel = result.scalar_one_or_none()

        # 🔁 Канал уже есть в БД
        if channel:
            # ♻️ Был удалён → восстанавливаем
            if not channel.enabled:
                channel.enabled = True
                channel.title = title
                channel.owner_id = owner_tg_id
                channel.can_post = can_post
                channel.channelname = channelname

                await self.session.commit()

                print(
                    f"{Fore.CYAN}[CHANNEL RESTORED]{Style.RESET_ALL} "
                    f"id={channel.channel_id}, title={title}"
                )
                return channel, False

            # 🚫 Уже активен
            print(
                f"{Fore.YELLOW}[CHANNEL EXISTS]{Style.RESET_ALL} "
                f"id={channel.channel_id}, title={channel.title}"
            )
            return channel, True

        # ➕ Канала нет → создаём
        new_channel = Channel(
            channel_id=channel_id,
            title=title,
            owner_id=owner_tg_id,
            can_post=can_post,
            enabled=True,
            channelname=channelname  # ✅ НОВАЯ СТРОКА
        )
        self.session.add(new_channel)
        await self.session.commit()
        await self.session.refresh(new_channel)

        print(
            f"{Fore.GREEN}[CHANNEL ADDED]{Style.RESET_ALL} "
            f"id={new_channel.channel_id}, title={title}, owner={owner_tg_id}"
        )
        return new_channel, False

    async def replace(
        self,
        owner_tg_id: int,
        channel_id: int,
        title: str,
        can_post: bool,
        channelname: str | None = None
    ) -> tuple[bool, bool]:
        """
        Заменить канал пользователя.
        Возвращает (replaced: bool, same_channel: bool)
        """
        # Получаем пользователя
        user = await self.session.scalar(select(User).where(User.tg_id == owner_tg_id))
        if not user:
            return False, False

        # Проверяем, есть ли уже канал с таким channel_id у пользователя
        existing_channel = await self.session.scalar(
            select(Channel).where(Channel.owner_id == user.id, Channel.channel_id == channel_id)
        )
        if existing_channel:
            # Этот канал уже подключён
            return False, True

        # Текущий канал
        current_channel = await self.session.scalar(select(Channel).where(Channel.owner_id == user.id))

        # Удаляем старый канал
        if current_channel:
            await self.session.delete(current_channel)
            await self.session.flush()

        # Добавляем новый
        new_channel = Channel(
            channel_id=channel_id,
            title=title,
            owner_id=user.id,
            can_post=can_post,
            channelname=channelname
        )
        self.session.add(new_channel)
        await self.session.commit()
        await self.session.refresh(new_channel)
        return True, False
    

class Format:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_texts(
        self,
        owner_tg_id: int,
        channel_id: int
    ) -> tuple[str | None, str | None]:
        """
        Получить оба текста (up, down)
        """

        stmt = select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == owner_tg_id,
            Channel.enabled.is_(True)
        )

        result = await self.session.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            return None, None

        return channel.up_text, channel.down_text

    async def update_text(
        self,
        owner_tg_id: int,
        channel_id: int,
        text_pos: str,
        text: str | None
    ) -> bool:
        """
        Обновление текста блока (up/down)
        Возвращает True если обновлено, False если канал не найден
        """

        stmt = select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == owner_tg_id,
            Channel.enabled.is_(True)
        )

        result = await self.session.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            return False

        if text_pos == "up":
            channel.up_text = text
        elif text_pos == "down":
            channel.down_text = text
        else:
            raise ValueError(f"Invalid text_pos: {text_pos}")

        await self.session.commit()
        return True