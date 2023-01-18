
users_entrance = (
    '{mention}, добро пожаловать в чат!\nНажми на {subject} чтобы получить доступ к сообщениям',
    'А, {mention}, это снова ты? А, извините, обозналась. Нажми на {subject} и можете пройти',
    'Братишь, {mention}, я тебя так долго ждал. Жми на {subject} и пробегай',
    'Разве это не тот {mention}? Тыкай на {subject} и проходи, пожалуйста, мы ждали',
    'Даже не верится, что это ты, {mention}. Мне сказали не пускать ботов, поэтому нажми на {subject}',

    '{mention}, это правда ты? Мы тебя ждали. Или не ты? Настоящий {mention} сможет нажать на {subject}. ' +
    'Докажи, что ты не бот!',
    'Кого я вижу? Это же {mention}! Тыкай на {subject} и можешь идти',
    'Идёт проверка {mention}.\nПроверка почти завершена. Чтобы продолжить, {mention}, пожалуйста нажмите на {subject}',
    'О, {mention}, мы тебя ждали. Докажи что ты не бот и проходи. Для этого нажми на {subject}',
    'Да {mention}, ты меня уже бесишь! А, прошу прощения, обознался. Чтобы я могла вас впустить, нажмите на {subject}'
)

throttled_answers = (
    'Вот чё ты спамишь? Ну всё, я обиделась на {limit} секунд',
    'Админы, я бы забанила этого спамера... Спамершу... В общем ЭТО! А я игнорю это {limit} секунд',
    'Ты сейчас серьёзно? Ну это бан на {limit} с. И даже не пытайся меня отговорить',
    'Да ты шутишь?! А если я буду спамить, приятно тебе будет? Игнор на {limit} секунд.',
    'Да пошёл ты. Пошла. Всё в общем, это конец, {limit} секунд пошло',

    'Да ты можешь меня хоть {limit} секунд не трогать? Задолбали \U0001F620',
    'Опять ты? Не не не. Подожди {limit} секунд хотя бы, потом поговорим \U0001F612',
    'Ещё одно сообщение и меня вырвет! Дай мне отойти {limit} секунд \U0001F922',
    'Опять? Блин... Дай мне {limit} секунд \U0001F635',
    'А ты уже спрашивал. Вот не отвечу! \U0001F92A'
)


class Lang:
    strings = {
        "en": {
            "error_no_reply": "This command must be sent as a reply to one's message!",
            "error_report_admin": "Whoa! Don't report admins 😈",
            "error_restrict_admin": "You cannot restrict an admin.",
            "error_cannot_restrict": "You are not allowed to restrict users",
            "error_cannot_report_linked": "You cannot report messages from linked channel",

            "report_date_format": "%d.%m.%Y at %H:%M",
            "report_message": '👆 Sent {time} (server time)\n'
                              '<a href="{msg_url}">Go to message</a>',
            "report_note": "\n\nNote: {note}",
            "report_sent": "<i>Report sent</i>",

            "action_del_msg": "Delete message",
            "action_del_and_ban": "Delete and ban",

            "action_deleted": "\n\n🗑 <b>Deleted</b>",
            "action_deleted_banned": "\n\n🗑❌ <b>Deleted, user or chat banned</b>",
            "action_deleted_partially": "Some messages couldn't be found or deleted. "
                                        "Perhaps they were deleted by another admin.",

            "readonly_forever": "🙊 <i>User set to read-only mode forever</i>",
            "readonly_temporary": "🙊 <i>User set to read-only mode until {time} (server time)</i>",
            "nomedia_forever": "🖼 <i>User set to text-only mode forever</i>",
            "nomedia_temporary": "🖼 <i>User set to text-only mode until {time} (server time)</i>",
            "channel_banned_forever": "📛 <i>Channel banned forever</i>",

            "need_admins_attention": 'Dear admins, your presence in chat is needed!\n\n'
                                     '<a href="{msg_url}">Go to chat</a>',

            "channels_not_allowed": "Sending messages on behalf of channels is not allowed in this group. Channel "
                                    "banned."
        },
        "ru": {
            "error_no_reply": "Эта команда должна быть ответом на какое-либо сообщение!",
            "error_report_admin": "Адмиа репортишь? Ай-ай-ай 😈",
            "error_restrict_admin": "Невозможно ограничить администратора.",
            "error_cannot_restrict": "У вас нет права ограничивать пользователей",
            "error_cannot_report_linked": "Нельзя жаловаться на сообщения из привязанного канала",
            "error_timeout": "Какие-то проблемы с коннектом админ увидит их в логе не переживай",
            "error_key": "Вероятно ты использовал 'плохое' слово и поэтому моя и подруги ChatGPT/DaLLE обиделись и не "
                         "отвечают",

            "report_date_format": "%d.%m.%Y в %H:%M",
            "report_message": '👆 Отправлено {time} (время серверное)\n'
                              '<a href="{msg_url}">Перейти к сообщению</a>',
            "report_note": "\n\nПримечание: {note}",
            "report_sent": "<i>Жалоба отправлена администраторам</i>",

            "action_del_msg": "Удалить сообщение",
            "action_del_and_ban": "Удалить и забанить",

            "action_deleted": "\n\n🗑 <b>Удалено</b>",
            "action_deleted_banned": "\n\n🗑❌ <b>Удалено, юзер или чат забанен</b>",
            "action_deleted_partially": "Не удалось найти или удалить некоторые сообщения. "
                                        "Возможно, они уже были удалены другим админом.",

            "readonly_forever": "🙊 <i>Пользователь переведён в режим «только чтение» навсегда</i>",
            "readonly_temporary": "🙊 <i>Пользователь переведён в режим «только чтение» до {time} (время серверное)</i>",
            "nomedia_forever": "🖼 <i>Пользователю запрещено отправлять медиафайлы навсегда</i>",
            "nomedia_temporary": "🖼 <i>Пользователю запрещено отправлять медиафайлы до {time} (время серверное)</i>",
            "channel_banned_forever": "📛 <i>Канал забанен навсегда</i>",

            "need_admins_attention": 'Уважаемые админы, в чате нужно ваше присутствие!\n\n'
                                     '<a href="{msg_url}">Перейти к чату</a>',

            "channels_not_allowed": "В этой группе запрещено отправлять сообщения от имени канала. Сам канал забанен."
        },
    }

    def __init__(self, language_key: str):
        if language_key in self.strings.keys():
            self.chosen_lang = language_key
        else:
            raise ValueError(f"No such language: {language_key}")

    def get(self, key):
        return self.strings.get(self.chosen_lang, {}).get(key, "%MISSING STRING%")
