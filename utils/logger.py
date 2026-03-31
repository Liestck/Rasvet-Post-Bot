# utils.logger | Rasvet Post Bot
from datetime import datetime
from colorama import Fore, Style, init


init(autoreset=True)


class Logger:
    """ Вывод информации в консоль """

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _time() -> str:
        return f"{Style.DIM}[{Logger._now()}]{Style.RESET_ALL}"


    class Channel:
        """ Логирование действий с каналами """

        @staticmethod
        def delete(channel, callback) -> None:
            return print(
                f"{Fore.RED}[CHANNEL DELETED]{Style.RESET_ALL} "
                f"id={channel.channel_id}, user={callback.from_user.id}"
            )
        
    class User:
        """ Логирование действий с пользователями """

        @staticmethod
        def new(tg_id: int, username: str | None) -> None:

            username_part = f"@{username}" if username else "no username"

            print(
                f"{Logger._time()} "
                f"{Fore.CYAN}NEW USER{Style.RESET_ALL} "
                f"{Fore.WHITE}→ "
                f"id={Fore.YELLOW}{tg_id}{Fore.WHITE}, "
                f"user={Fore.MAGENTA}{username_part}"
            )

        @staticmethod
        def exists(tg_user) -> None:
            return print(f"{Fore.YELLOW}[USER EXISTS]{Style.RESET_ALL} tg_id={tg_user.id}, username={tg_user.username}")

    class Bot:
        """ Логгирование действий бота """

        @staticmethod
        def bot_start() -> None:
            
            print(
                f"{Logger._time()} "
                f"{Fore.GREEN}BOT{Style.BRIGHT} STARTED{Style.RESET_ALL} "
                f"{Fore.WHITE}→ polling started"
            )

        @staticmethod
        def bot_stop() -> None:

            print(
                f"{Logger._time()} "
                f"{Fore.RED}BOT{Style.BRIGHT} STOPPED{Style.RESET_ALL} "
                f"{Fore.WHITE}→ polling stopped"
            )