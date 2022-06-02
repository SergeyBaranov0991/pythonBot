import telebot
from telebot import TeleBot
import sqlite3 as sl
import connect


# Connection to telegram bot section
bot: TeleBot = telebot.TeleBot(connect.token, parse_mode=None)


@bot.message_handler(commands=['start'])
def start_and_send_welcome(message):
    mess = f'Привет, <b>{message.from_user.first_name}</b> <b>{message.from_user.last_name}</b>!\nЯ умею:\n/start - что бы начать работать со мной\n/add - что бы добавить новое напоминание (В РАЗРАБОТКЕ)\n/get - что бы получить все напоминания\n/del - что бы удалить все напоминания'  # Пимер использования данных из объекта message
    bot.send_message(message.chat.id, mess, parse_mode='html')


# Fixed_БАГ - при "get" данных в терминале видна ошбика: Error code: 400. Description: Bad Request: message text is empty. UPD: пофиксалось строчкой bot.send_message(message.chat.id, '\n'.join(row))
@bot.message_handler(commands=['get'])
def get_all_reminders(message):
    user_id = message.chat.id
    db_con = sl.connect('database1.db')
    with db_con:
        data = db_con.execute(f"SELECT REMINDER_TEXT FROM REMINDERS WHERE USER_ID = {user_id}")
        for row in data:
            bot.send_message(message.chat.id, '\n'.join(row))


@bot.message_handler(commands=['del'])
def delete_all_reminders_menu(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Да', callback_data="Да"))
    markup.add(telebot.types.InlineKeyboardButton(text='Нет', callback_data='Нет'))
    bot.send_message(message.chat.id, 'Вы уверены?', reply_markup=markup)


# Метод для вывода кнопок подтверждения удаления и последующего удаления информации
@bot.callback_query_handler(func=lambda call: True)
def callbacks_for_reminder_actions(call):

    if call.data == 'Да':
        delete_all_reminders()
        bot.send_message(call.message.chat.id, 'Все напоминания удалены')
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

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
# Fixed_БАГ - Сейчас при вводе данных, отличных от текста, странное поведение - пишет что добавлено новое напоминание none, но на /get ничего не возвращает. UPD - пофикшено путём добавления проверки на тип вводимых данных
def add_new_reminder_step3(message):
    # Проверка на то, что вводимые данные - строка.
    if isinstance(message.text, str):
        ids = message.chat.id
        text = message.text
        sqllite_connection = ''
        try:
            # Объявляем коннекшен к БД на уровне метода. Можно объявлять один раз после импорта билиботек, но тогда нужно указывать дополнительный параметр
            sqllite_connection = sl.connect('database1.db')
            # Для работы с напоминаниями нужен курсор, объявляем его
            cursor = sqllite_connection.cursor()
            # В этой строке сам скрипт вставки. В Values знаки вопроса - значения, которые будем вставлять.
            data = """INSERT INTO REMINDERS (REMINDER_TEXT, USER_ID) VALUES (?, ?);"""
            # Здесь мы указываем, из каких переменных мы будем брать данные для вставки в строке выше, в таблицу REMINDERS. Соотношение определяется порядковым расположением
            data_tuple = (text, ids)
            # Теперь передаем курсору два параметра - строчку вставки на SQL и переменные с параметрами
            cursor.execute(data, data_tuple)
            # Закрываем курсор
            cursor.close()
            # Без этой строчки вставка невозможна, как и любое изменение данных в БД. НЕ ЗАБЫВАТЬ ДОБАВЛЯТЬ при изменении / добавлении / удалении данных в БД
            sqllite_connection.commit()
            bot.send_message(ids, f'Ваше напоминание: --// {text} //-- добавлено в список.\nЧто бы увидеть все напоминания - /get')
        except sqllite_connection.Error as error:
            print('ошибка', error)
    else:
        bot.send_message(message.chat.id, 'Непонятные данные, не смогу запомнить :(')


@bot.message_handler(content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker', 'animation'])
def process_any_message(message):
    if isinstance(message.text, str):
        if message.text in ['Привет', 'привет', 'хай', 'Хай', 'Ку', 'Прив', 'прив']:
            bot.send_message(message.chat.id, 'И тебе привет!')
        elif message.text in ['Hello', 'hello', 'hi', 'Hi', 'hey', 'Hey']:
            bot.send_message(message.chat.id, 'What`s up?')
        elif message.text in ['Э', 'э', 'ээ', 'ЭЭ', 'Ээ', 'эЭ']:
            bot.send_message(message.chat.id, 'Сидело на трубЭ')
        else:
            bot.send_message(message.chat.id, 'Я тебя не понимаю :) Перейди к /start и я напомню, что умею ;)')
    else:
        bot.send_message(message.chat.id, 'Непонятные данные, я не знаю что с этим делать :(')


# Функция для удаления данных из таблицы REMINDERS
def delete_all_reminders():
    sqllite_connection = ''
    try:
        # Объявляем коннекшен к БД на уровне метода. Можно объявлять один раз после импорта билиботек, но тогда нужно указывать дополнительный параметр
        sqllite_connection = sl.connect('database1.db')
        # Для работы с напоминаниями нужен курсор, объявляем его
        cursor = sqllite_connection.cursor()
        # В этой строке сам скрипт удаления на SQL
        data = """DELETE FROM REMINDERS;"""
        # Теперь передаем курсору два параметра - строчку вставки на SQL и переменные с параметрами
        cursor.execute(data)
        # Закрываем курсор
        cursor.close()
        # Без этой строчки вставка невозможна, как и любое изменение данных в БД. НЕ ЗАБЫВАТЬ ДОБАВЛЯТЬ при изменении / добавлении / удалении данных в БД
        sqllite_connection.commit()
    except sqllite_connection.Error as error:
        print('ошибка', error)


# @bot.message_handler(commands=['calendar'])
# def start(message):
#     calendar, step = DetailedTelegramCalendar().build()
#     bot.send_message(message.chat.id, f'Select {LSTEP[step]}', reply_markup=calendar)
#
#
# @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
# def cal(c):
#     result, key, step = DetailedTelegramCalendar().process(c.data)
#     if not result and key:
#         bot.edit_message_text(f"Select {LSTEP[step]}", c.message.chat.id, c.message.message_id, reply_markup=key)
#     elif result:
#         bot.edit_message_text(f"You selected {result}", c.message.chat.id, c.message.message_id)


bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()
bot.polling(none_stop=True)
