# utils.functions | Набор вспомогательных функций | Rasvet Post Bot
from aiogram.types import Message, MessageEntity
import html


class Converting:
    """ Конвертация форматов """

    # Markdown -> HTML | Conveting.markdown_html(message)
    # =============================================
    @staticmethod
    def strip_command(text: str, entities: list[MessageEntity] | None):
        if not text or not entities:
            return text, entities

        for e in entities:
            if e.type == "bot_command":
                cut = e.offset + e.length

                # убираем команду + пробелы после неё
                new_text = text[cut:].lstrip()
                shift = len(text) - len(new_text)

                new_entities = []
                for ent in entities:
                    if ent.offset >= cut:
                        ent.offset -= shift
                        new_entities.append(ent)

                return new_text, new_entities

        return text, entities

    @staticmethod
    def entities_to_html(text: str, entities: list[MessageEntity] | None) -> str:
        if not text:
            return ""

        if not entities:
            return html.escape(text)

        entities = sorted(entities, key=lambda e: (e.offset, -e.length))

        result = []
        stack = []
        i = 0

        def open_tag(e: MessageEntity):
            if e.type == "bold":
                return "<b>"
            if e.type == "italic":
                return "<i>"
            if e.type == "underline":
                return "<u>"
            if e.type == "strikethrough":
                return "<s>"
            if e.type == "spoiler":
                return "<tg-spoiler>"
            if e.type == "code":
                return "<code>"
            if e.type == "pre":
                lang = getattr(e, "language", None)
                if lang:
                    return f'<pre><code class="language-{lang}">'
                return "<pre>"
            if e.type == "text_link":
                return f'<a href="{html.escape(e.url)}">'
            if e.type == "url":
                return f'<a href="{text[e.offset:e.offset + e.length]}">'
            if e.type == "mention":
                username = text[e.offset + 1:e.offset + e.length]
                return f'<a href="https://t.me/{username}">'
            if e.type == "text_mention":
                return f'<a href="tg://user?id={e.user.id}">'
            if e.type == "blockquote":
                return "<blockquote>"
            return ""

        def close_tag(e: MessageEntity):
            if e.type == "bold":
                return "</b>"
            if e.type == "italic":
                return "</i>"
            if e.type == "underline":
                return "</u>"
            if e.type == "strikethrough":
                return "</s>"
            if e.type == "spoiler":
                return "</tg-spoiler>"
            if e.type == "code":
                return "</code>"
            if e.type == "pre":
                return "</code></pre>" if getattr(e, "language", None) else "</pre>"
            if e.type in ["text_link", "url", "mention", "text_mention"]:
                return "</a>"
            if e.type == "blockquote":
                return "</blockquote>"
            return ""

        while i < len(text):
            # открытие
            for e in entities:
                if e.offset == i:
                    result.append(open_tag(e))
                    stack.append((e, e.offset + e.length))

            # закрытие
            for e, end in stack[::-1]:
                if end == i:
                    result.append(close_tag(e))
                    stack.remove((e, end))

            result.append(html.escape(text[i]))
            i += 1

        for e, _ in reversed(stack):
            result.append(close_tag(e))

        return "".join(result)

    @staticmethod
    def markdown_html(message: Message, view: bool) -> str:
        ''' view: True - чистый текст | False - чистые теги '''
        if not message.text:
            return ""

        text, entities = Converting.strip_command(message.text, message.entities)
        
        if view: 
            return Converting.entities_to_html(text, entities).replace('\\n', '\n')
        else:
            return Converting.entities_to_html(text, entities)
    # =============================================