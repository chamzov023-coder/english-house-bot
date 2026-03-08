import telebot
from telebot import types
import datetime
import sqlite3
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ВАШИ ДАННЫЕ ===
BOT_TOKEN = '8629886155:AAHxvCytE5IkbVUz2zwENSzEza-dTkwU39E'
ADMIN_CHAT_ID = 823680495

if BOT_TOKEN == 'YOUR_BOT_TOKEN':
    logger.error("❌ Токен бота не указан!")
    exit()

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)


# === БАЗА ДАННЫХ ===
def init_database():
    try:
        conn = sqlite3.connect('english_house.db')
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS applications")

        cursor.execute('''
                       CREATE TABLE applications
                       (
                           id          INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id     INTEGER,
                           username    TEXT,
                           client_name TEXT,
                           phone       TEXT,
                           age_group   TEXT,
                           program     TEXT,
                           schedule    TEXT,
                           status      TEXT      DEFAULT 'новая',
                           created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        conn.commit()
        conn.close()
        logger.info("✅ База данных успешно создана!")
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")


init_database()

# === ДАННЫЕ ШКОЛЫ ===
SCHOOL_INFO = {
    'phone': '+7 (939) 489-80-33',
    'address': 'г. Кызыл, ТД Континент, ул. Лопсанчапа, д. 35, 56 кабинет',
    'working_hours': '08:00 - 21:00',
    'instagram': 'english_home17',
}

# === ВОЗРАСТНЫЕ ГРУППЫ ===
AGE_GROUPS = {
    'kids_3_4': '👶 Дети 3-4 лет',
    'kids_6_7': '🧒 Дети 6-7 лет',
    'teens_14_15': '👦 Подростки 14-15 лет',
    'adults': '👨‍🎓 Взрослые'
}

# === ПРОГРАММЫ (ТОЛЬКО ПО ОДНОЙ ДЛЯ КАЖДОЙ ГРУППЫ) ===
PROGRAMS = {
    'kids_3_4': '🇬🇧 0 ступень - Я умею петь / I can sing Games',
    'kids_6_7': '🇬🇧 1 ступень - Я умею говорить / I can speak',
    'teens_14_15': '🇬🇧 Английский для подростков',
    'adults': '🇬🇧 Английский для взрослых'
}

# === РАСПИСАНИЕ (ОДНО ДЛЯ КАЖДОЙ ГРУППЫ) ===
SCHEDULES = {
    'kids_3_4': '📅 ПН, СР, ЧТ с 08:30 до 15:15 (3 раза в неделю)',
    'kids_6_7': '📅 ПН, СР, ЧТ с 08:30 до 15:15 (3 раза в неделю)',
    'teens_14_15': '📅 ПН, СР, ЧТ с 08:30 до 15:15 (3 раза в неделю)',
    'adults': '📅 СБ с 13:00 до 15:00 (суббота)',
}

# Временное хранилище
user_data = {}


# === СОХРАНЕНИЕ ЗАЯВКИ ===
def save_application(user_id, data):
    try:
        conn = sqlite3.connect('english_house.db')
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO applications
                       (user_id, username, client_name, phone, age_group, program, schedule, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           user_id,
                           data.get('username', ''),
                           data.get('client_name', ''),
                           data.get('phone', ''),
                           data.get('age_group', ''),
                           data.get('program', ''),
                           data.get('schedule', ''),
                           'новая'
                       ))
        conn.commit()
        app_id = cursor.lastrowid
        conn.close()
        return app_id
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        return None


# === УВЕДОМЛЕНИЕ АДМИНУ ===
def notify_admin(app_id, data):
    try:
        msg = f"""🔔 НОВАЯ ЗАЯВКА #{app_id}

👤 Имя: {data.get('client_name')}
📞 Телефон: {data.get('phone')}
👥 Возраст: {data.get('age_group')}
📚 Программа: {data.get('program')}
📅 Расписание: {data.get('schedule')}
🆔 @{data.get('username', 'нет')}"""
        bot.send_message(ADMIN_CHAT_ID, msg)
    except Exception as e:
        logger.error(f"❌ Ошибка уведомления: {e}")


# === КОМАНДА /start ===
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_name = message.from_user.first_name
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton('📝 Записаться'),
            types.KeyboardButton('👥 Программы'),
            types.KeyboardButton('📞 Контакты'),
            types.KeyboardButton('ℹ️ О школе')
        )

        text = f"""🏠 English House 🏠

Привет, {user_name}!
Я помогу записаться на пробный урок.

Выберите действие в меню 👇"""
        bot.send_message(message.chat.id, text, reply_markup=markup)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


# === ОБРАБОТЧИК ТЕКСТА ===
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    chat_id = message.chat.id

    if text == '📝 Записаться':
        user_data[chat_id] = {'state': 'waiting_name'}
        bot.send_message(chat_id, "Как вас зовут?")

    elif text == '👥 Программы':
        show_programs(message)

    elif text == '📞 Контакты':
        contacts = f"""📞 КОНТАКТЫ:

🏫 Адрес: {SCHOOL_INFO['address']}
📱 Телефон: {SCHOOL_INFO['phone']}
🕐 Часы работы: {SCHOOL_INFO['working_hours']}
📷 Instagram: @{SCHOOL_INFO['instagram']}

💬 Мы на связи!"""
        bot.send_message(chat_id, contacts)

    elif text == 'ℹ️ О школе':
        about = """🏠 О школе English House

Мы помогаем выучить английский с 2015 года!

✅ Опытные преподаватели
✅ Небольшие группы (до 10 чел)
✅ Разговорные клубы
✅ Подготовка к экзаменам

Приходите на бесплатный пробный урок!"""
        bot.send_message(chat_id, about)

    elif text == '⬅️ Назад':
        start_command(message)

    else:
        if chat_id in user_data:
            state = user_data[chat_id].get('state')

            if state == 'waiting_name':
                user_data[chat_id]['client_name'] = text
                user_data[chat_id]['username'] = message.from_user.username
                user_data[chat_id]['state'] = 'waiting_phone'
                bot.send_message(chat_id, "📞 Введите ваш номер телефона:")

            elif state == 'waiting_phone':
                phone = text.strip()
                if phone.startswith('+7') or phone.startswith('8') or phone.startswith('9'):
                    user_data[chat_id]['phone'] = phone
                    user_data[chat_id]['state'] = 'choosing_age'

                    markup = types.InlineKeyboardMarkup(row_width=1)
                    for age_id, age_name in AGE_GROUPS.items():
                        markup.add(types.InlineKeyboardButton(age_name, callback_data=f"age_{age_id}"))

                    bot.send_message(chat_id, "👥 Выберите возрастную группу:", reply_markup=markup)
                else:
                    bot.send_message(chat_id, "❌ Неверный формат. Введите: +7 999 123 45 67")
        else:
            bot.send_message(chat_id, "Используйте кнопки меню 👆")


# === ПОКАЗ ПРОГРАММ ===
def show_programs(message):
    text = "👥 ПРОГРАММЫ ОБУЧЕНИЯ:\n\n"
    for age_id, age_name in AGE_GROUPS.items():
        text += f"{age_name}\n"
        text += f"  • {PROGRAMS[age_id]}\n\n"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('⬅️ Назад'))
    bot.send_message(message.chat.id, text, reply_markup=markup)


# === ОБРАБОТЧИК ИНЛАЙН КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    try:
        if call.data.startswith('age_'):
            age_id = call.data.replace('age_', '')
            if age_id in AGE_GROUPS:
                user_data[chat_id]['age_group'] = AGE_GROUPS[age_id]
                user_data[chat_id]['program'] = PROGRAMS[age_id]
                user_data[chat_id]['schedule'] = SCHEDULES[age_id]

                # Сразу показываем подтверждение с выбранными данными
                confirm_text = f"""📝 Подтвердите запись:

👥 Группа: {AGE_GROUPS[age_id]}
📚 Программа: {PROGRAMS[age_id]}
📅 Расписание: {SCHEDULES[age_id]}

Всё верно?"""

                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("✅ Да, всё верно", callback_data=f"confirm_{age_id}"),
                    types.InlineKeyboardButton("❌ Отмена", callback_data="cancel")
                )

                bot.edit_message_text(confirm_text, chat_id, msg_id, reply_markup=markup)

        elif call.data.startswith('confirm_'):
            age_id = call.data.replace('confirm_', '')

            app_id = save_application(chat_id, user_data[chat_id])

            if app_id:
                bot.edit_message_text(
                    f"✅ Заявка #{app_id} создана!\n\n"
                    f"👥 Группа: {user_data[chat_id]['age_group']}\n"
                    f"📚 Программа: {user_data[chat_id]['program']}\n"
                    f"📅 Расписание: {user_data[chat_id]['schedule']}\n\n"
                    f"Скоро мы свяжемся с вами для подтверждения!",
                    chat_id,
                    msg_id
                )
                notify_admin(app_id, user_data[chat_id])
                del user_data[chat_id]
            else:
                bot.edit_message_text("❌ Ошибка. Попробуйте позже.", chat_id, msg_id)

        elif call.data == "cancel":
            bot.edit_message_text("❌ Отменено", chat_id, msg_id)
            if chat_id in user_data:
                del user_data[chat_id]

    except Exception as e:
        logger.error(f"❌ Ошибка в callback: {e}")
        bot.send_message(chat_id, "Произошла ошибка. Попробуйте снова.")


# === КОМАНДА ДЛЯ ПРОСМОТРА ЗАЯВОК ===
@bot.message_handler(commands=['apps'])
def show_apps(message):
    if message.chat.id == ADMIN_CHAT_ID:
        conn = sqlite3.connect('english_house.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications ORDER BY created_at DESC LIMIT 10')
        apps = cursor.fetchall()
        conn.close()

        if apps:
            text = "📊 ПОСЛЕДНИЕ ЗАЯВКИ:\n\n"
            for app in apps:
                text += f"#{app[0]} - {app[8]}\n"
                text += f"👤 {app[3]} | 📞 {app[4]}\n"
                text += f"👥 {app[5]}\n"
                text += f"📚 {app[6]}\n"
                text += f"📅 {app[7]}\n\n"
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, "📭 Заявок пока нет")
    else:
        bot.send_message(message.chat.id, "❌ Нет прав")


# === ЗАПУСК ===
if __name__ == '__main__':
    print("🚀 Бот English House запущен...")
    print("✅ Нажмите Ctrl+C для остановки")
    bot.infinity_polling()