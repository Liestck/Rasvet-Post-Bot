# messages | Помодульные неймспейсы текстового контента | Rasvet Post Bot
from app.config import Config

class BotMsg:
    """ Текстовый контент бота """
    
    class Channel:
        """ Текста связанные с каналами """
        
        @staticmethod
        def menu(channel) -> str:
            return (
                f'<b><blockquote><a href="https://t.me/{channel.channelname}">{channel.title}</a></blockquote></b>\n\n'
                f"<b>ID канала: </b><code>{channel.channel_id}</code>\n"
                f"<b>Права на публикацию: </b>"
                f"{'✅' if channel.can_post else '❌'}\n"
            )
        
        @staticmethod
        def confirm_delete(channel) -> str:
            return f'<b>Вы уверены, что хотите удалить канал:</b> <a href="https://t.me/{channel.channelname}">{channel.title}</a>?'
        
        @staticmethod
        def successfully_add(channel) -> str:
            return f'<b>✅ Канал успешно добавлен!</b>\n\n<blockquote><a href="https://t.me/{channel.username}/">➕ {channel.title}</a></blockquote>'

        _list = "<b>Ваши каналы 👇</b>"

        incorrect_data = "⚠️ Неверные данные"
        not_found = "⚠️ Канал не найден"
        delete = "🗑 Канал удалён"

        add_1 = '<b>1️⃣ Добавьте бота в канал</b>\n\n<blockquote>❕<b>Нажмите кнопку ниже</b>, выберите нужный канал, дайте право <b>"Управление сообщениями"</b></blockquote>'
        add_2 = "<b>2️⃣ Введите @channel_name канала</b>\n\n<blockquote>Например @mychannel</blockquote>"
        cancel_add = "<b>❌ Отмена добавления канала</b>\n\n<i>Это сообщение скоро исчезнет</i>"
        incorrect_channel_name = "<b>⚠️ Ошибка!</b>\n\n<blockquote>Введите @channel_name канала</blockquote>"
        not_found_channel_name = "<b>⚠️ Такого канала не существует</b>\n\n<blockquote>Введите @channel_name канала</blockquote>"
        no_rights = (
            "<b>⚠️ У бота нет прав на публикацию в этом канале!</b>\n\n"
            '<blockquote><b>Добавьте бота в администраторы</b> с правом <b>"Управление сообщениями"</b> и попробуйте снова /channels</blockquote>'
        )
        limitation = "<b>🚫 Вы достигли лимита каналов</b>"
        duplicate = "<b>⚠️ Этот канал уже подключён в вашем списке!</b>\n\n<blockquote>Введите @channel_name канала</blockquote>"
        cancel_replace = "<b>❌ Отмена замены канала</b>\n\n<i>Это сообщение скоро исчезнет</i>"

        edit_new = "<b>Введите @channel_name нового канала:</b>\n\n<blockquote>Например @mychannel</blockquote>"


    class Post:
        """ Текста связанные с модулем << Публикация >> """

        @staticmethod
        def successfully_send(post_link, channel) -> str:
            return f'✅ <b><a href="{post_link}">Пост</a> опубликован в <a href="https://t.me/{channel.channelname}">{channel.title}</a>!</b>'
        
        no_rights = '<b>❌ Нет прав на публикацию!</b>\n\n<blockquote>❕<b>Нажмите кнопку ниже</b>, выберите нужный канал, дайте право <b>"Управление сообщениями"</b></blockquote>'
        send = "<b>Отправьте пост 👇</b>"
        cancel = "<b>⚠️ Отправка поста отменена!</b>\n\n<i>Это сообщение скоро исчезнет</i>"
        pad = "Опубликовать?"


    class Format:
        ''' Текста связанные с модулем << Форматирование постов >>'''

        manual_full = "<b>⚙️ Настройки визуального оформления постов</b>\n<blockquote><i>Заготовки, закрепляемые к каждому посту опубликованному через бота!</i></blockquote>\n\nДля редактирования используйте кнопки в меню!\n\n<b>👇 Ваш актуальный формат постов:</b>"

        manual_short = "<b>⚙️ Настройки визуального оформления постов</b>\n<blockquote><i>Заготовки, закрепляемые к каждому посту опубликованному через бота!</i></blockquote>\n\n"

        successfully_edit = "<b>✅ Текст обновлён</b>\n\n<i>Это сообщение скоро исчезнет</i>"


    class Suggest:
        """ Текста связанные с модулем << Предложка >> """

        @staticmethod
        def menu(channel, has_token: bool) -> str:
            if has_token and channel.suggest_username:
                status = f'<a href="https://t.me/{channel.suggest_username}">✅ Бот подключен</a>'
            else:
                status = "⚠️ Бот не подключен"

            return (
                "<b>📪 Управление предложкой</b>\n\n"
                f"<blockquote>{status}</blockquote>"
            )
        
        @staticmethod
        def success_connected(bot_username: str, bot_first_name: str) -> str:
            return (
                f'<a href="{Config.BOT_URL}">Rasvet Post</a> 🤝 '
                f'<a href="t.me/{bot_username}">{bot_first_name}</a>\n\n'
                "✅ Бот предложки подключен успешно!"
            )

        bind_prompt = (
            "<b>Отправь токен бота</b>\n\n"
            "<i>🔐 Он будет храниться в зашифрованном виде</i>"
        )

        bind_prompt_with_error = bind_prompt

        invalid_format = "<b>⚠️ Ошибка!</b>\n<blockquote>Введите верный токен</blockquote>"

        invalid_token = "<b>⚠️ Ошибка!</b>\n<blockquote>Введите существующий токен</blockquote>"

        send_fail = (
            "<b>⚠️ Ошибка!</b>\n<blockquote>"
            "Не удалось отправить сообщение\n"
            "Пропишите /start в боте и попробуйте снова"
            "</blockquote>"
        )

        step_format = "Проверяю формат..."
        step_api = "Проверяю Telegram API..."
        step_send = "Отправляю тестовое сообщение..."


    class User:
        """ Текста связанные с пользователем """

        not_found = "❌ Пользователь не найден!"


    class Bot:
        """ Глобальные текста """

        welcome = (
            f'<b><a href="{Config.BOT_URL}">👋 Привет!</a></b>\n\n'
            "<b>Я помогу тебе вести Telegram-канал:</b>\n"
            "<blockquote>• Создать предложку\n"
            "• Публиковать посты\n• Отложенная публикация</blockquote>\n\n"
            "Начнём с подключения канала 👇"
        )