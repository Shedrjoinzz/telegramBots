import telebot, sqlite3, time
import urllib.parse as urlparse
from telebot import types
from libs import config, menu

bot = telebot.TeleBot(config.TOKEN, parse_mode='html')

@bot.message_handler(commands=['start'])
def start(message):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        if message.chat.type == 'private':
            id = cursor.execute(f"SELECT id_user FROM users WHERE id_user = '{message.chat.id}'").fetchone()
            if id is None:
                if message.chat.id != config.id_admins:
                    cursor.execute("INSERT INTO users (`id_user`, `name`, `username`, `limits`, `warring`, `ban`) VALUES (?, ?, ?, ?, ?, ?)", (message.chat.id, message.from_user.first_name, message.from_user.username, 0, 0, False,))
                    bot.send_message(message.chat.id, text='<b>Добро пожаловать в бот обратной связи, отправьте ваш вопрос прямо в этот чат</b>')
                else:
                    pass
            else:
                if message.chat.id == config.id_admins:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    but1 = types.KeyboardButton('Админка 👑')
                    markup.add(but1)
                    bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)
                else:
                    bot.send_message(message.chat.id, text=f'<code>{message.from_user.first_name}</code> <b>отправьте ваш вопрос прямо в этот чат:</b>')

def repl_message(message, par1, par2, par3):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        try:
            bot.delete_message(config.id_admins, par1)
            select_user = cursor.execute(f"SELECT id_user FROM dialog WHERE id = '{par2[0]}'").fetchone()
            select_dialog = cursor.execute(f"SELECT id FROM dialog WHERE id_user = '{select_user[0]}'").fetchone()
            if select_dialog[0] is None:
                bot.send_message(config.id_admins, text=f'<b>Возможно ответ пользователю <code>{select_user[0]}</code> был уже дан!\nИли Вы дали ему бан/предупреждение</b>')
            else:
                cursor.execute(f"DELETE FROM dialog WHERE id_user = '{select_user[0]}'")
                cursor.execute(f"UPDATE users SET limits = 0 WHERE id_user = '{select_user[0]}'")
                bot.send_message(select_user[0], text=f'<b>👑 Ответ от Администрации на вопрос ID:</b> <code>#{par2[0]}</code>\n\n<b>Message Admins:</b> {message.text}')
                bot.send_message(par3, text=f'<b>Ответ пользователю <code>{select_user[0]}</code> отправлен!</b>')
        except:
            select_count_block = cursor.execute("SELECT count_block FROM admin").fetchone()
            one = int(1)
            two = int(select_count_block[0])
            cursor.execute(f"UPDATE admin SET count_block = {one + two}")
            bot.send_message(par3, text='<b>Пользователь заблокировал бота</b>')



def rassilka(message, par3):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        texts = message.text
        if message.text == '⬅️ Назад':
            bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)
            bot.delete_message(config.id_admins, message.message_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton('Админка 👑')
            markup.add(but1)
            bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)
        else:
            if len(texts) <= 4000:
                cursor.execute("INSERT INTO texts_for_rassilka (`texts_rassilka`) VALUES (?)", (texts,))
                next_button = types.ReplyKeyboardMarkup(resize_keyboard=True)
                but1 = types.KeyboardButton('Пропустить ➡️')
                but2 = types.KeyboardButton('⬅️ Назад')
                next_button.add(but1)
                next_button.add(but2)
                try:
                    msg = bot.send_message(config.id_admins, text=f'{texts}\n\n\n<b>Отправьте название url кнопки</b>', reply_markup=next_button)
                    bot.register_next_step_handler(msg, next_rassilka_names)
                except:
                    bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)
                    bot.send_message(config.id_admins, text='<b>Слишком большой текст, максимальное содержимое в сообщений символы телеграм 4096, рассылка отменена попробуйте заново</b>')

def next_rassilka_names(message):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        name = message.text
        if message.text == '⬅️ Назад':
            bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)
            cursor.execute("DELETE FROM texts_for_rassilka")
            bot.delete_message(config.id_admins, message.message_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton('Админка 👑')
            markup.add(but1)
            bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)

        elif message.text == 'Пропустить ➡️':
            test_rassilka = cursor.execute("SELECT texts_rassilka FROM texts_for_rassilka").fetchone()
            bot.send_message(config.id_admins, text=f'{test_rassilka[0]}')
            next = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton(text='Отправить ➡️')
            but2 = types.KeyboardButton(text= '⬅️ Назад')
            next.add(but1)
            next.add(but2)
            msg = bot.send_message(config.id_admins, text="<b>Посмотрите пост к рассылке, если всё хорошо то можете отправить на рассылку</b>", reply_markup=next)
            bot.register_next_step_handler(msg, rassilla_bez_knopok)
        else:
            if len(name) <= 32:
                cursor.execute(f"UPDATE texts_for_rassilka SET name_button =  '{name}'")
                msg = bot.send_message(config.id_admins, text='<b>Отправьте ссылку для кнопки</b>')
                bot.register_next_step_handler(msg, next_rassilka, name)
            else:
                msg = bot.send_message(config.id_admins, text='Слишком большое название для кнопки, попробуйте до 32 символов ввести название:')
                bot.register_next_step_handler(msg, next_rassilka_names)

def rassilla_bez_knopok(message):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        name = message.text
        if message.text == '⬅️ Назад':
            bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)
            cursor.execute("DELETE FROM texts_for_rassilka")
            bot.delete_message(config.id_admins, message.message_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton('Админка 👑')
            markup.add(but1)
            bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)
        else:
            select_text = cursor.execute("SELECT texts_rassilka FROM texts_for_rassilka").fetchone()
            select_all_users = cursor.execute("SELECT id_user FROM users").fetchall()
            for i in select_all_users:
                try:
                    bot.send_message(i[0], text=f'{select_text[0]}')
                except:
                    select_count_block = cursor.execute("SELECT count_block FROM admin").fetchone()
                    one = int(1)
                    two = int(select_count_block[0])
                    cursor.execute(f"UPDATE admin SET count_block = {one + two}")
            admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton(text='Админка 👑')
            admin.add(but1)
            bot.send_message(config.id_admins, text='<b>Готово</b>', reply_markup=admin)
            cursor.execute("DELETE FROM texts_for_rassilka")

def next_rassilka(message, name):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        my_link = message.text
        if message.text == '⬅️ Назад':
            bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)
            bot.delete_message(config.id_admins, message.message_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton('Админка 👑')
            markup.add(but1)
            bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)
        elif message.text == 'Пропустить ➡️':
            test_rassilka = cursor.execute("SELECT texts_rassilka FROM texts_for_rassilka").fetchone()
            bot.send_message(config.id_admins, text=f'{test_rassilka[0]}')
            next = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton(text='Отправить ➡️')
            but2 = types.KeyboardButton(text= '⬅️ Назад')
            next.add(but1)
            next.add(but2)
            msg = bot.send_message(config.id_admins, text="<b>Посмотрите пост к рассылке, если всё хорошо то можете отправить на рассылку</b>", reply_markup=next)
            bot.register_next_step_handler(msg, rassilla_bez_knopok)
        else:
            if urlparse.urlparse(my_link).scheme:
                success_button(message, my_link, name)
            else:
                msg = bot.send_message(config.id_admins, "<b>Я не вижу тут ссылки, попробуй ещё раз:</b>")
                bot.register_next_step_handler(msg, next_rassilka)

def success_button(message, my_link, name):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        if message.text == '⬅️ Назад':
            bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)
            bot.delete_message(config.id_admins, message.message_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton('Админка 👑')
            markup.add(but1)
            bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)
        else:
            select_text = cursor.execute("SELECT texts_rassilka FROM texts_for_rassilka").fetchone()
            inls = types.InlineKeyboardMarkup()
            in1 = types.InlineKeyboardButton(text=f'{name}', url=f"{my_link}")
            inls.add(in1)
            bot.send_message(config.id_admins, text=f"{select_text[0]}", reply_markup=inls)
            next = types.ReplyKeyboardMarkup(resize_keyboard=True)
            but1 = types.KeyboardButton(text='Отправить ➡️')
            but2 = types.KeyboardButton(text= '⬅️ Назад')
            next.add(but1)
            next.add(but2)
            msg = bot.send_message(config.id_admins, text="<b>Посмотрите пост к рассылке, если всё хорошо то можете отправить на рассылку</b>", reply_markup=next)
            bot.register_next_step_handler(msg, post_rassilka, my_link)

def post_rassilka(message, my_link):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        select_all_users = cursor.execute("SELECT id_user FROM users").fetchall()
        count = 0
        for i in select_all_users:
            select_text = cursor.execute("SELECT texts_rassilka FROM texts_for_rassilka").fetchone()
            select_name_button = cursor.execute("SELECT name_button FROM texts_for_rassilka").fetchone()
            select_link_button = cursor.execute("SELECT link_for_button FROM texts_for_rassilka").fetchone()
            inl = types.InlineKeyboardMarkup()
            in1 = types.InlineKeyboardButton(text=f'{select_name_button[0]}', url=f'{my_link}')
            inl.add(in1)
            try:
                bot.send_message(i[0], text=f"{select_text[0]}", reply_markup=inl)
                ++count
                bot.edit_message_text(config.id_admins, message_id=count.message.message_id, text=f'{count}')
            except:
                select_count_block = cursor.execute("SELECT count_block FROM admin").fetchone()
                one = int(1)
                two = int(select_count_block[0])
                cursor.execute(f"UPDATE admin SET count_block = {one + two}")
        admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
        but1 = types.KeyboardButton(text='Админка 👑')
        admin.add(but1)
        bot.send_message(config.id_admins, text='<b>Готово</b>', reply_markup=admin)
        cursor.execute("DELETE FROM texts_for_rassilka")


@bot.callback_query_handler(func=lambda call: True)
def call(call):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        select_all_id = cursor.execute("SELECT id FROM dialog").fetchall()
        for i in select_all_id:
            select_user = cursor.execute(f"SELECT id_user FROM dialog WHERE id = '{i[0]}'").fetchone()
            if call.data == f'{i[0]} repl':
                cancel = types.InlineKeyboardMarkup()
                select_user = cursor.execute(f"SELECT id_user FROM dialog WHERE id = '{i[0]}'").fetchone()
                in1  = types.InlineKeyboardButton(text='Отмена', callback_data='cancel')
                cancel.add(in1)
                msg = bot.send_message(chat_id=config.id_admins, text=f'<b>Отправьте ответ пользователю</b> <code>{select_user[0]}</code>:', reply_markup=cancel)
                par1 = msg.message_id
                par2 = i
                par3 = config.id_admins
                bot.register_next_step_handler(msg, repl_message, par1, par2, par3)

            if call.data == f'{i[0]} war':
                select_user = cursor.execute(f"SELECT id_user FROM dialog WHERE id = '{i[0]}'").fetchone()
                select_status_war = cursor.execute(f"SELECT warring FROM users WHERE id_user = '{select_user[0]}'").fetchone()
                one = int(1)
                two = int(select_status_war[0])
                cursor.execute(f"UPDATE users SET warring = {one+two} WHERE id_user = '{select_user[0]}'")
                cursor.execute(f"UPDATE users SET limits = 0 WHERE id_user = '{select_user[0]}'")
                bot.send_message(config.id_admins, text=f'<b>Пользователю {select_user[0]} выдано предупреждение, Максимальное количество предупреждений 3 и пользователь получит авто.бан</b>')
                cursor.execute(f"DELETE FROM dialog WHERE id_user = '{select_user[0]}'")
                try:
                    bot.send_message(select_user[0], text=f'<b>Вам выдано предупреждение! Максимальное количество предупреждений 3 и получите авто.бан</b>')
                except:
                    select_count_block = cursor.execute("SELECT count_block FROM admin").fetchone()
                    one = int(1)
                    two = int(select_count_block[0])
                    cursor.execute(f"UPDATE admin SET count_block = {one + two}")

            if call.data == f'{i[0]} ban':
                select_ban_list = cursor.execute("SELECT count_ban FROM admin").fetchone()
                select_status_war = cursor.execute(f"SELECT warring FROM users WHERE id_user = '{select_user[0]}'").fetchone()
                select_status_ban = cursor.execute(f"SELECT ban FROM users WHERE id_user = '{select_user[0]}'").fetchone()
                if select_status_ban[0] == True or int(select_status_war[0]) >= 3:
                    bot.send_message(chat_id=config.id_admins, text='<b>Пользователь и так заблокирован</b>')
                else:
                    cursor.execute(f"UPDATE users SET ban = True WHERE id_user = '{select_user[0]}'")
                    cursor.execute(f"DELETE FROM dialog WHERE id_user = '{select_user[0]}'")
                    cursor.execute(f"UPDATE users SET limits = 0 WHERE id_user = '{select_user[0]}'")
                    bot.delete_message(config.id_admins, call.message.message_id)
                    select_all_id_in_unban  = cursor.execute(f"SELECT id_user_in_ban FROM all_ban_users WHERE id_user_in_ban = '{select_user[0]}'").fetchone()
                    if select_all_id_in_unban is None:
                        cursor.execute("INSERT INTO all_ban_users (`id_user_in_ban`) VALUES (?)", (select_user[0],))
                        bot.send_message(chat_id=config.id_admins, text=f'<b>Пользователь <code>{select_user[0]}</code> заблокирован!</b>')
                        try:
                            bot.send_message(chat_id=select_user[0], text='<b>Вы заблокированы!</b>')
                        except:
                            select_count_block = cursor.execute("SELECT count_block FROM admin").fetchone()
                            one = int(1)
                            two = int(select_count_block[0])
                            cursor.execute(f"UPDATE admin SET count_block = {one + two}")
                    else:
                        pass

        if call.data == 'cancel':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(chat_id=config.id_admins, text='<b>Отменено</b>')
            bot.clear_step_handler_by_chat_id(chat_id=config.id_admins)


@bot.message_handler(content_types=['text', 'photo'])
def text_photo(message):
    with sqlite3.connect('base/data.db') as db:
        cursor = db.cursor()
        if message.chat.type == 'private':
            select_ban_system = cursor.execute(f"SELECT ban FROM users WHERE id_user = '{message.chat.id}'").fetchone()
            select_warring_system = cursor.execute(f"SELECT warring FROM users WHERE id_user = '{message.chat.id}'").fetchone()
            select_limit_system = cursor.execute(f"SELECT limits FROM users WHERE id_user = '{message.chat.id}'").fetchone()
            one = int(select_warring_system[0])
            war_max = int(3)
            mes = message.text
            if select_ban_system[0] == False:
                if war_max > one:
                    if select_limit_system[0] != 1:
                        if f'{config.id_admins}' == f'{message.chat.id}':
                            if message.text == 'Админка 👑':
                                adminka = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                but1 = types.KeyboardButton(text='Рассылка 📪')
                                but2 = types.KeyboardButton(text='Статистика 📊')
                                but3 = types.KeyboardButton(text='⬅️ Назад')
                                adminka.add(but1, but2)
                                adminka.add(but3)
                                bot.send_message(config.id_admins, text='<b>Админка Открыта</b>', reply_markup=adminka)

                            if message.text == 'Рассылка 📪':
                                msg = bot.send_message(config.id_admins, text='<b>📪 Отправьте сообщение для пользователей:</b>')
                                par3 = msg.message_id
                                bot.register_next_step_handler(msg, rassilka, par3)

                            if message.text == 'Статистика 📊':
                                adminka_statistics = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                but1 = types.KeyboardButton(text='Админка 👑')
                                adminka_statistics.add(but1)
                                select_all_id = cursor.execute("SELECT id FROM dialog").fetchone()
                                select_statistics = cursor.execute("SELECT * FROM admin").fetchall()
                                for i in select_statistics:
                                    bot.send_message(config.id_admins, text=f'<b>Всего юзеров:</b> {i[0]}\n'
                                                                            f'<b>Забанены юзеров:</b> {i[1]}\n'
                                                                            f'<b>Заблокировали бота:</b> {i[2]}\n')

                            if message.text == '⬅️ Назад':
                                bot.delete_message(config.id_admins, message.message_id)
                                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                but1 = types.KeyboardButton('Админка 👑')
                                markup.add(but1)
                                bot.send_message(config.id_admins, text='<b>Главное Меню</b>', reply_markup=markup)

                        else:
                            if len(mes) > 1000:
                                bot.send_message(message.chat.id, text=f'<b>Ваще сообщение содержит {len(mes)} символов, максимальное кол-во символов 1000!</b>')
                            else:
                                cursor.execute("INSERT INTO dialog (`id_user`, `message`) VALUES (?, ?)", (message.chat.id, message.text,))
                                cursor.execute(f"UPDATE users SET limits = 1 WHERE id_user = '{message.chat.id}'")
                                select_id_system = cursor.execute(f"SELECT id FROM dialog WHERE id_user = '{message.chat.id}'").fetchone()
                                bot.send_message(message.chat.id, text=f'<b>Принято! Ожидайте ответа от Администрации\nID вопроса:</b> <code>#{select_id_system[0]}</code>\n<i>Вы можете отправить этот хеш сюда для просмота своего вопроса</i>')
                                repl = types.InlineKeyboardMarkup()
                                in1 = types.InlineKeyboardButton(text='Ответить', callback_data=f'{select_id_system[0]} repl')
                                in2 = types.InlineKeyboardButton(text='Предупреждение', callback_data=f'{select_id_system[0]} war')
                                in3 = types.InlineKeyboardButton(text='Бан', callback_data=f'{select_id_system[0]} ban')
                                repl.add(in1)
                                repl.add(in2, in3)
                                bot.send_message(config.id_admins, text=f'<b>Новый вопрос по ID</b> <code>#{select_id_system[0]}</code>\n'
                                                                        f'<b>Имя:</b> <code>{message.from_user.first_name}</code>\n'
                                                                        f'<b>User:</b> @{message.from_user.username}\n'
                                                                        f'<b>ID:</b> <code>{message.chat.id}</code>\n'
                                                                        f'<b>Символов:</b> {len(mes)}\n\n'
                                                                        f'<b>Message User:</b> {message.text}', reply_markup=repl)

                    else:
                        select_id_system = cursor.execute(f"SELECT id FROM dialog WHERE id_user = '{message.chat.id}'").fetchone()
                        if message.text == f'#{select_id_system[0]}':
                            select_user_text = cursor.execute(f"SELECT message FROM dialog WHERE id_user = '{message.chat.id}'").fetchone()
                            bot.send_message(message.chat.id, text=f'<b>Ваш вопрос по ID: <code>#{select_id_system[0]}</code>\n\nMessage user:</b> {select_user_text[0]}')
                        else:
                            select_id_system = cursor.execute(f"SELECT id FROM dialog WHERE id_user = '{message.chat.id}'").fetchone()
                            bot.send_message(message.chat.id, text=f'<b>Вопрос не принят!\nОжидайте ответа на ваш предыдущий вопрос по ID:</b> <code>#{select_id_system[0]}</code>')
                else:
                    select_ban_list = cursor.execute(f"SELECT id_user_in_ban FROM all_ban_users WHERE id_user_in_ban = '{message.chat.id}'").fetchone()
                    if select_ban_list is None:
                        cursor.execute("INSERT INTO all_ban_users (`id_user_in_ban`) VALUES (?)", (message.chat.id,))
                        bot.send_message(message.chat.id, text='<b>Вы заблокированы!</b>')
                    else:
                        bot.send_message(message.chat.id, text='<b>Вы заблокированы!</b>')
            else:
                bot.send_message(message.chat.id, text='<b>Вы заблокированы!</b>')

bot.infinity_polling()
