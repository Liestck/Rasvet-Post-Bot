# utils.logger | Rasvet Post Bot
from datetime import datetime
import json
from colorama import Fore, Style, init


init(autoreset=True)


class Logger:
    """Вывод информации в консоль + JSON файл"""

    LOG_FILE = "bot.logs.jsonl"

    @staticmethod
    def _now() -> str:
        # дата + время
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _write(data: dict) -> None:
        with open(Logger.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    @staticmethod
    def _log(data: dict, console_message: str) -> None:
        print(console_message)
        Logger._write(data)


    class Channel:
        """Логирование действий с каналами"""

        @staticmethod
        def delete(channel, callback) -> None:
            data = {
                "time": Logger._now(),
                "event": "channel_delete",
                "channel_id": channel.channel_id,
                "user_id": callback.from_user.id
            }

            msg = (
                f"{Logger._now()} "
                f"{Fore.RED}[CHANNEL DELETED]{Style.RESET_ALL} "
                f"id={channel.channel_id}, user={callback.from_user.id}"
            )

            Logger._log(data, msg)


    class User:
        """Логирование действий с пользователями"""

        @staticmethod
        def new(tg_id: int, username: str | None) -> None:
            data = {
                "time": Logger._now(),
                "event": "user_new",
                "tg_id": tg_id,
                "username": username
            }

            username_part = f"@{username}" if username else "no username"

            msg = (
                f"{Logger._now()} "
                f"{Fore.CYAN}NEW USER{Style.RESET_ALL} "
                f"→ id={Fore.YELLOW}{tg_id}{Style.RESET_ALL}, "
                f"user={Fore.MAGENTA}{username_part}"
            )

            Logger._log(data, msg)

        @staticmethod
        def exists(tg_user) -> None:
            data = {
                "time": Logger._now(),
                "event": "user_exists",
                "tg_id": tg_user.id,
                "username": tg_user.username
            }

            msg = (
                f"{Logger._now()} "
                f"{Fore.YELLOW}[USER EXISTS]{Style.RESET_ALL} "
                f"tg_id={tg_user.id}, username={tg_user.username}"
            )

            Logger._log(data, msg)


    class Bot:
        """Логгирование действий бота"""

        @staticmethod
        def bot_start() -> None:
            data = {
                "time": Logger._now(),
                "event": "bot_start"
            }

            msg = (
                f"{Logger._now()} "
                f"{Fore.GREEN}BOT{Style.BRIGHT} STARTED{Style.RESET_ALL} "
                f"→ polling started"
            )

            Logger._log(data, msg)

        @staticmethod
        def bot_stop() -> None:
            data = {
                "time": Logger._now(),
                "event": "bot_stop"
            }

            msg = (
                f"{Logger._now()} "
                f"{Fore.RED}BOT{Style.BRIGHT} STOPPED{Style.RESET_ALL} "
                f"→ polling stopped"
            )

            Logger._log(data, msg)


    class Suggest:
        """Логгирование suggest-ботов"""

        @staticmethod
        def bot_start(channel_id: int) -> None:
            data = {
                "time": Logger._now(),
                "event": "suggest_bot_start",
                "channel_id": channel_id
            }

            msg = (
                f"{Logger._now()} "
                f"{Fore.GREEN}SUGGEST BOT{Style.BRIGHT} STARTED{Style.RESET_ALL} "
                f"→ channel {channel_id}"
            )

            Logger._log(data, msg)

        @staticmethod
        def bot_error(channel_id: int, error: Exception) -> None:
            data = {
                "time": Logger._now(),
                "event": "suggest_bot_error",
                "channel_id": channel_id,
                "error": str(error)
            }

            msg = (
                f"{Logger._now()} "
                f"{Fore.RED}SUGGEST BOT{Style.BRIGHT} ERROR{Style.RESET_ALL} "
                f"→ channel {channel_id} | {error}"
            )

            Logger._log(data, msg)