import telebot
from telebot import types
import datetime
import sqlite3
import logging
import os
from flask import Flask
import threading

# Заглушка для Render
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!"


def run_flask():
    app.run(host='0.0.0.0', port=10000)


# Запускаем заглушку в отдельном потоке
threading.Thread(target=run_flask, daemon=True).start()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ВАШИ ДАННЫЕ ===
BOT_TOKEN = '8629886155:AAHSdNohaJGXLuDLFMhXpFiAU_10hmL9mzY'
ADMIN_CHAT_ID = 823680495

if BOT_TOKEN == 'YOUR_BOT_TOKEN':
    logger.error("❌ Токен бота не указан!")
    exit()

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)


# === БАЗА ДАННЫХ ===
def init_database():
    try:
        conn = sqlite3.connect('english_home.db')
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
                           format      TEXT,
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
    'name': 'English Home',
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

# === ПРОГРАММЫ С ЦЕНАМИ ===
PROGRAMS = {
    'kids_3_4': {
        'name': '🇬🇧 0 ступень - Я умею петь / I can sing Games',
        'price': '3600₽/мес'
    },
    'kids_6_7': {
        'name': '🇬🇧 1 ступень - Я умею говорить / I can speak',
        'price': '6500₽/мес'
    },
    'teens_14_15': {
        'name': '🇬🇧 Английский для подростков',
        'price': '6500₽/мес'
    },
    'adults': {
        'name': '🇬🇧 Английский для взрослых',
        'price': '7900₽/мес'
    }
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
        conn = sqlite3.connect('english_home.db')
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO applications
                       (user_id, username, client_name, phone, age_group, program, format, schedule, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           user_id,
                           data.get('username', ''),
                           data.get('client_name', ''),
                           data.get('phone', ''),
                           data.get('age_group', ''),
                           data.get('program', ''),
                           data.get('format', ''),
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
💻 Формат: {data.get('format')}
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

        text = f"""🏠 {SCHOOL_INFO['name']} 🏠

Привет, {user_name}!
Я помогу записаться на занятия.

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
        about = f"""🏠 О школе {SCHOOL_INFO['name']}

Мы помогаем выучить английский с 2015 года!

✅ Опытные преподаватели
✅ Небольшие группы (до 10 чел)
✅ Разговорные клубы
✅ Подготовка к экзаменам

Приходите к нам на занятия!"""
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
    text = f"👥 ПРОГРАММЫ ОБУЧЕНИЯ ({SCHOOL_INFO['name']}):\n\n"
    for age_id, age_name in AGE_GROUPS.items():
        program = PROGRAMS[age_id]
        text += f"{age_name}\n"
        text += f"  • {program['name']}\n"
        text += f"  💰 {program['price']}\n\n"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('⬅️ Назад'))
    bot.send_message(message.chat.id, text, reply_markup=markup)


# === ПОКАЗ ВЫБОРА ФОРМАТА ===
def show_format_choice(chat_id, age_id, msg_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏠 Офлайн", callback_data=f"format_offline_{age_id}"),
        types.InlineKeyboardButton("💻 Онлайн", callback_data=f"format_online_{age_id}")
    )
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))

    bot.edit_message_text(
        "Выберите формат занятий:",
        chat_id,
        msg_id,
        reply_markup=markup
    )


# === ОБРАБОТЧИК ИНЛАЙН КНОПОК ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    try:
        if call.data.startswith('age_'):
            age_key = call.data.replace('age_', '')  # теперь age_key = 'kids_3_4', 'teens_14_15' и т.д.
            if age_key in AGE_GROUPS:
                user_data[chat_id]['age_group'] = AGE_GROUPS[age_key]
                user_data[chat_id]['program'] = PROGRAMS[age_key]['name']
                user_data[chat_id]['price'] = PROGRAMS[age_key]['price']
                user_data[chat_id]['schedule'] = SCHEDULES[age_key]

                # Показываем выбор формата
                show_format_choice(chat_id, age_key, msg_id)

        elif call.data.startswith('format_'):
            parts = call.data.split('_')
            format_type = parts[1]  # online или offline
            age_key = parts[2]  # теперь age_key = 'kids_3_4' или 'teens_14_15'

            format_text = "💻 Онлайн" if format_type == "online" else "🏠 Офлайн"
            user_data[chat_id]['format'] = format_text

            # Сразу показываем подтверждение
            program = PROGRAMS[age_key]
            confirm_text = f"""📝 Подтвердите запись:

👥 Группа: {AGE_GROUPS[age_key]}
📚 Программа: {program['name']}
💰 Стоимость: {program['price']}
💻 Формат: {format_text}
📅 Расписание: {SCHEDULES[age_key]}

После подтверждения мы свяжемся с вами для уточнения деталей."""

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{age_key}"),
                types.InlineKeyboardButton("❌ Отмена", callback_data="cancel")
            )

            bot.edit_message_text(confirm_text, chat_id, msg_id, reply_markup=markup)

        elif call.data.startswith('confirm_'):
            age_key = call.data.replace('confirm_', '')

            app_id = save_application(chat_id, user_data[chat_id])

            if app_id:
                program = PROGRAMS[age_key]
                bot.edit_message_text(
                    f"✅ Заявка #{app_id} создана!\n\n"
                    f"👥 Группа: {user_data[chat_id]['age_group']}\n"
                    f"📚 Программа: {user_data[chat_id]['program']}\n"
                    f"💰 Стоимость: {program['price']}\n"
                    f"💻 Формат: {user_data[chat_id]['format']}\n"
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
        conn = sqlite3.connect('english_home.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applications ORDER BY created_at DESC LIMIT 10')
        apps = cursor.fetchall()
        conn.close()

        if apps:
            text = "📊 ПОСЛЕДНИЕ ЗАЯВКИ:\n\n"
            for app in apps:
                text += f"#{app[0]} - {app[9]}\n"
                text += f"👤 {app[3]} | 📞 {app[4]}\n"
                text += f"👥 {app[5]}\n"
                text += f"📚 {app[6]}\n"
                text += f"💻 {app[7]}\n"
                text += f"📅 {app[8]}\n\n"
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, "📭 Заявок пока нет")
    else:
        bot.send_message(message.chat.id, "❌ Нет прав")


# === ЗАПУСК ===
if __name__ == '__main__':
    print(f"🚀 Бот {SCHOOL_INFO['name']} запущен...")
    print("✅ Нажмите Ctrl+C для остановки")
    bot.infinity_polling()