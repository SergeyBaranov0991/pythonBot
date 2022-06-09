import telebot
from telebot import TeleBot
from telebot import types
import sqlite3 as sl
import connect
import requests


# Connection to telegram bot section
bot: TeleBot = telebot.TeleBot(connect.token, parse_mode=None)


# Class for work with Database sqllite. This is overhead but I wanted to try
class Database:
    def __init__(self):
        self.db_con = sl.connect('database1.db')

# It might be useful to change the way how methods work...
# TODO: Maybe it will be better to keep only work with database inside the class
    def delete_all_reminders(self, user_id, text):
        if isinstance(text, int) or isinstance(text, str):
            # TODO: Тут, видимо, будет нужен еще "get", что бы получить все записи...
            #  ...Возможно стоит выводить их в виде кнопок?
            #  Либо четче понять, что sqllite3 возвращает в ответе, и анализировать это.
            #  Сейчас даже если ввести ID, которого нету - произойдет попытка удаления
            # TODO: Кроме того, сама логика анализа введенного значения пользаком - так себе. не очень юзер-френдли
            if text == 'Вы уверены, что хотите удалить ВСЕ напоминания?':
                try:
                    # Для работы с напоминаниями нужен курсор, объявляем его
                    cursor = self.db_con.cursor()
                    # В этой строке сам скрипт удаления на SQL
                    data = """DELETE FROM REMINDERS WHERE USER_ID=?;"""
                    # Теперь передаем курсору два параметра - строчку вставки на SQL и переменные с параметрами
                    cursor.execute(data, (user_id,))
                    # Закрываем курсор
                    cursor.close()
                    # Без этой строчки вставка невозможна, как и любое изменение данных в БД.
                    # НЕ ЗАБЫВАТЬ ДОБАВЛЯТЬ при изменении / добавлении / удалении данных в БД
                    self.db_con.commit()
                except self.db_con.Error as error:
                    return 'ошибка', error
                # TODO: Не по феншую. По-сути, это зависимость на другую логику вообще, надо переделать
                bot.send_message(user_id, f'Все напоминания удалены')
            elif text.isdigit():
                id_t = text
                try:
                    # Для работы с напоминаниями нужен курсор, объявляем его
                    cursor = self.db_con.cursor()
                    # В этой строке сам скрипт удаления на SQL
                    data = """DELETE FROM REMINDERS WHERE USER_ID=? AND ID=?;"""
                    # Теперь передаем курсору два параметра - строчку вставки на SQL и переменные с параметрами
                    cursor.execute(data, (user_id, id_t,))
                    # Закрываем курсор
                    cursor.close()
                    # Без этой строчки вставка невозможна, как и любое изменение данных в БД.
                    # НЕ ЗАБЫВАТЬ ДОБАВЛЯТЬ при изменении / добавлении / удалении данных в БД
                    self.db_con.commit()
                except self.db_con.Error as error:
                    return 'ошибка', error
                # TODO: Не по феншую. По-сути, это зависимость на другую логику вообще, надо адо отдавать только текст,
                #  а не слать месседж
                bot.send_message(user_id, f'Сообщение с №: {text} удалено')
            else:
                # TODO: Не по феншую. По-сути, это зависимость на другую логику вообще, надо отдавать только текст,
                #  а не слать месседж
                bot.send_message(user_id, 'Введено некорректное значение :( попробуйте заново')
        else:
            # TODO: Не по феншую. По-сути, это зависимость на другую логику вообще, надо отдавать только текст,
            #  а не слать месседж.
            bot.send_message(user_id, 'Введено некорректное значение :( попробуйте заново')

    def get_all_reminders_for_user(self, user_id):
        # Берём из объекта message id чата
        with self.db_con:
            data = self.db_con.execute(f"SELECT * FROM REMINDERS WHERE USER_ID = {user_id}")
            for row in data:
                id_r = row[0]
                text_r = row[1]
                # TODO: Придумать, как проверять то, что в ответе этого цикла ничего не пришло, что бы отправлять разные
                #  сообщения. Код ниже - не работает
                length = (id_r, text_r)
                i = len(length)
                if i == 0:
                    bot.send_message(user_id, 'У вас нет напоминаний')
                else:
                    bot.send_message(user_id, f'{id_r}: {text_r}')


@bot.message_handler(commands=['start'])
def start_and_send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn0 = types.KeyboardButton('/start')
    btn1 = types.KeyboardButton('/get')
    btn2 = types.KeyboardButton('/del')
    btn3 = types.KeyboardButton('/add')
    btn4 = types.KeyboardButton('/weather')
    markup.add(btn0, btn1, btn2, btn3, btn4)
    mess = f'Привет, <b>{message.from_user.first_name}</b> <b>{message.from_user.last_name}</b>!' \
           f'\nМоя задача - напоминать тебе о том, что ты можешь забыть ;)\n' \
           f'Все основные команды для работы со мной представлены в меню.\n' \
           f'Я умею:\n' \
           f'- Рассказать о себе - /start\n' \
           f'- Рассказать о погоде - /weather\n' \
           f'- Сохранить, показать и удалить по твоему запросу какое-либо текстовое напоминание - /add, /get, /del'
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['get'])
def get_all_reminders(message):
    d = Database()
    user_id = message.chat.id
    d.get_all_reminders_for_user(user_id=user_id)


@bot.message_handler(commands=['weather'])
def input_your_city(message):
    msg = bot.send_message(message.chat.id, 'Введи город, в котором нужно определить погоду (по-русски) или "нет", что бы получить прогноз по автоматически определенной локации')
    bot.register_next_step_handler(msg, what_weather)


def what_weather(message):
    chat_id = message.chat.id
    if isinstance(message.text, str):
        if message.text in ['нет', 'Нет']:
            city = ''
            text_to_show = 'У вас сегодня'
            find_weather(city, chat_id, text_to_show)
        else:
            city = message.text
            text_to_show = 'Погода в'
            find_weather(city, chat_id, text_to_show)
    else:
        bot.send_message(chat_id, 'Хватит вводить бабуйню!')


def find_weather(city, chat_id, text_to_show):

    if not chat_id:
        return 'Непонятно, куда отсылать сообщение'

    elif not text_to_show:
        text_to_show = ''

    elif not city:
        city = ''

    url = f'http://wttr.in/{city}?0Qm'
    weather_parameters = {
            'format': 4
        }

    try:
        response = requests.get(url, params=weather_parameters)
    except requests.ConnectionError:
        bot.send_message(chat_id, '<внутренняя ошибка бота>')
    if response.status_code == 200:
        bot.send_message(chat_id, f'{text_to_show}: {response.text}')
    else:
        bot.send_message(chat_id, '<ошибка на сервере погоды>')


# TODO: Сейчас выглядит очень не логично, потому что вопрос задается ДО того, как пользователь сделал выбор - удалить
#  всё или только одну строчку. Нужно поменять местами этапы выбора и этапы подтверждения
@bot.message_handler(commands=['del'])
def delete_all_reminders_menu(message):
    msg = bot.send_message(message.chat.id, 'Укажите № удаляемого напоминания или русскую "А" для удаления всех '
                                            'напоминаний')
    bot.register_next_step_handler(msg, delete_pre_step)


def delete_pre_step(message):
    if message.text in ['А', 'а', 'a', 'A', 'Ф', 'ф', 'F', 'f']:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text='Да', callback_data="Да"))
        markup.add(telebot.types.InlineKeyboardButton(text='Нет', callback_data='Нет'))
        bot.send_message(message.chat.id, 'Вы уверены, что хотите удалить ВСЕ напоминания?', reply_markup=markup)
    elif isinstance(message.text, int) or isinstance(message.text, str):
        what_delete = message.text
        d = Database()
        d.delete_all_reminders(user_id=message.chat.id, text=what_delete)
    else:
        bot.send_message(message.chat.id, 'Бабуйня')


# Метод для вывода различных кнопок в зависимости от того, что возвращается в callback
@bot.callback_query_handler(func=lambda call: True)
def callbacks_for_reminder_actions(call):
    if call.data == 'Да':
        text: str = call.message.text
        user_id: int = call.message.chat.id
        d = Database()
        d.delete_all_reminders(user_id=user_id, text=text)

    elif call.data == 'Нет':
        bot.send_message(call.message.chat.id, 'Отмена удаления. Попробуйте снова /del или вернитесь к меню /start')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    elif call.data == 'Не добавлять':
        bot.send_message(call.message.chat.id, 'Вы отменили ввод напоминания.\nМожете попробовать еще раз - /add')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    elif call.data == 'Добавить':
        add_new_reminder_step2(call.message)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    else:
        bot.send_message(call.message.chat.id, 'Error: something goes wrong in callbacks_for_reminder_actions')


@bot.message_handler(commands=['add'])
def add_new_reminder_step1(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Добавить', callback_data="Добавить"))
    markup.add(telebot.types.InlineKeyboardButton(text='Не добавлять', callback_data='Не добавлять'))
    bot.send_message(message.chat.id, f'Добавить новое напоминание, {message.from_user.first_name}?', reply_markup=markup)


def add_new_reminder_step2(message):
    msg = bot.send_message(message.chat.id, 'Вводите:')
    bot.register_next_step_handler(msg, add_new_reminder_step3)


# Метод для вставки данных по конкретному пользователю в таблицу REMINDERS
# Fixed_БАГ - Сейчас при вводе данных, отличных от текста, странное поведение - пишет что добавлено новое напоминание
# none, но на /get ничего не возвращает. UPD - пофикшено путём добавления проверки на тип вводимых данных
# TODO: нужно перекинуть этот метод внутрь класса Database, при этом вынести логику отправки каких то сообщений за класс
#  в функцию
def add_new_reminder_step3(message):
    # Проверка на то, что вводимые данные - строка.
    if isinstance(message.text, str):
        ids = message.chat.id
        text = message.text
        d = Database()
        try:
            # Объявляем коннекшен к БД на уровне метода. Можно объявлять один раз после импорта билиботек, но тогда
            # нужно указывать дополнительный параметр
            # Для работы с напоминаниями нужен курсор, объявляем его
            cursor = d.db_con.cursor()
            # В этой строке сам скрипт вставки. В Values знаки вопроса - значения, которые будем вставлять.
            data = """INSERT INTO REMINDERS (REMINDER_TEXT, USER_ID) VALUES (?, ?);"""
            # Здесь мы указываем, из каких переменных мы будем брать данные для вставки в строке выше,
            # в таблицу REMINDERS. Соотношение определяется порядковым расположением
            data_tuple = (text, ids)
            # Теперь передаем курсору два параметра - строчку вставки на SQL и переменные с параметрами
            cursor.execute(data, data_tuple)
            # Закрываем курсор
            cursor.close()
            # Без этой строчки вставка невозможна, как и любое изменение данных в БД. НЕ ЗАБЫВАТЬ ДОБАВЛЯТЬ при
            # изменении / добавлении / удалении данных в БД
            d.db_con.commit()
            bot.send_message(ids, f'Ваше напоминание: --// {text} //-- добавлено в список.\nЧто бы увидеть все напоминания - /get')
        except d.db_con.Error as error:
            print('ошибка', error)
    else:
        bot.send_message(message.chat.id, 'Непонятные данные, не смогу запомнить :(')


@bot.message_handler(content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker', 'animation'])
def process_any_message(message):
    data = []
    if isinstance(message.text, str):
        if message.text in ['Привет', 'привет', 'хай', 'Хай', 'Ку', 'Прив', 'прив']:
            bot.send_message(message.chat.id, 'И тебе привет!')
        elif message.text in ['Hello', 'hello', 'hi', 'Hi', 'hey', 'Hey']:
            bot.send_message(message.chat.id, 'What`s up?')
        elif message.text in ['Э', 'э', 'ээ', 'ЭЭ', 'Ээ', 'эЭ']:
            bot.send_message(message.chat.id, 'Сидело на трубЭ')
        # TODO: Это пока не особо работает, надо подумать
        elif message.text in ['Погода', 'дождь', 'ветренно', 'ветер', 'cнег', 'туман', 'жара', 'жарко', 'погода']:
            input_your_city(message)
        else:
            bot.send_message(message.chat.id, 'Я тебя не понимаю :) Перейди к /start и я напомню, что умею ;)')
    else:
        bot.send_message(message.chat.id, 'Непонятные данные, я не знаю что с этим делать :(')


bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()
bot.polling(none_stop=True)


