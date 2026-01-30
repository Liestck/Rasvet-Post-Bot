from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _time():
    return f"{Style.DIM}[{_now()}]{Style.RESET_ALL}"


def bot_start():
    print(
        f"{_time()} "
        f"{Fore.GREEN}BOT{Style.BRIGHT} STARTED{Style.RESET_ALL} "
        f"{Fore.WHITE}→ polling started"
    )


def bot_stop():
    print(
        f"{_time()} "
        f"{Fore.RED}BOT{Style.BRIGHT} STOPPED{Style.RESET_ALL} "
        f"{Fore.WHITE}→ polling stopped"
    )


def new_user(tg_id: int, username: str | None):
    username_part = f"@{username}" if username else "no username"

    print(
        f"{_time()} "
        f"{Fore.CYAN}NEW USER{Style.RESET_ALL} "
        f"{Fore.WHITE}→ "
        f"id={Fore.YELLOW}{tg_id}{Fore.WHITE}, "
        f"user={Fore.MAGENTA}{username_part}"
    )
