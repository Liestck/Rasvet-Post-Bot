# config | Формирование конфига из .env | Rasvet Post Bot
import os
from dotenv import load_dotenv


load_dotenv()


class Config:

    # Получение данных
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    OWNER_TGID: int = int(os.getenv("OWNER_TGID", 0))
    BOT_URL: str = os.getenv("BOT_URL")

    # Валидация
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не найден в .env")

    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL не найден в .env")

    if OWNER_TGID == 0:
        raise ValueError("❌ OWNER_TGID не найден в .env или задан неверно")

    if not BOT_URL:
        raise ValueError("❌ BOT_URL не найден в .env")