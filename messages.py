# messages | Помодульные неймспейсы текстового контента | Rasvet Post Bot

class BotMsg:
    """ Текстовый контент бота """
    
    class Channel:
        """ Текста связанные с каналами """
        
        @staticmethod
        def menu(channel) -> str:
            return (
                f"<b><blockquote>{channel.title}</blockquote></b>\n\n"
                f"<b>ID канала: </b><code>{channel.channel_id}</code>\n"
                f"<b>Права на публикацию: </b>"
                f"{'✅' if channel.can_post else '❌'}\n"
            )
        
        @staticmethod
        def confirm_delete(channel) -> str:
            return f'<b>Вы уверены, что хотите удалить канал:</b> <a href="https://t.me/c/{str(channel.id).replace("-100", "")}/">{channel.title}</a>?'
        
        @staticmethod
        def successfully_add(channel) -> str:
            return f'<b>✅ Канал успешно добавлен!</b>\n\n<blockquote><a href="https://t.me/c/{str(channel.id).replace("-100", "")}/">➕ {channel.title}</a></blockquote>'

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

        edit_new = "<b>Введите @channel_name нового канала:</b>\n\n<blockquote>Например @mychannel</blockquote>"


    class Post:
        """ Текста связанные с модулем << Публикация >> """

        @staticmethod
        def successfully_send(post_link, channel) -> str:
            return f'✅ <b><a href="{post_link}">Пост</a> опубликован в <a href="https://t.me/c/{str(channel.id).replace("-100", "")}/">{channel.title}</a>!</b>'
        
        no_rights = '<b>❌ Нет прав на публикацию!</b>\n\n<blockquote>❕<b>Нажмите кнопку ниже</b>, выберите нужный канал, дайте право <b>"Управление сообщениями"</b></blockquote>'
        send = "<b>Отправьте пост 👇</b>"
        cancel = "<b>⚠️ Отправка поста отменена!</b>\n\n<i>Это сообщение скоро исчезнет</i>"
        pad = "Публикуем?"


    class Format:
        ''' Текста связанные с модулем << Форматирование постов >>'''

        manual_full = "<blockquote><b>⚙️ Настройки визуального оформления постов</b></blockquote>\n<i>Заготовки, закрепляемые к каждому посту опубликованному через бота!</i>\n\nДля редактирования используйте кнопки в меню!\n\n<b>👇 Ваш актуальный формат постов:</b>"

        manual_short = "<blockquote><b>⚙️ Настройки визуального оформления постов</b></blockquote>\n<i>Заготовки, закрепляемые к каждому посту опубликованному через бота!</i>\n\n"

        successfully_edit = "<b>✅ Текст обновлён</b>\n\n<i>Это сообщение скоро исчезнет</i>"

    class User:
        """ Текста связанные с пользователем """

        not_found = "❌ Пользователь не найден!"


    class Bot:
        """ Глобальные текста """

        welcome = (
            '<b><a href="t.me/RasvetPost_bot">👋 Привет!</a></b>\n\n'
            "<b>Я помогу тебе вести Telegram-канал:</b>\n"
            "<blockquote>• Создать предложку\n"
            "• Публиковать посты\n• Отложенная публикация</blockquote>\n\n"
            "Начнём с подключения канала 👇"
        )