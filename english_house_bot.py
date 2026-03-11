import telebot
from telebot import types
import sqlite3
import logging
import os
from flask import Flask
import threading

# =================================
# Flask (чтобы Render не засыпал)
# =================================
app = Flask(__name__)

@app.route('/')
def home():
    return "English Home bot running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# =================================
# Логи
# =================================
logging.basicConfig(level=logging.INFO)

# =================================
# Токен
# =================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 823680495

if not BOT_TOKEN:
    print("BOT_TOKEN не найден")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# =================================
# База данных
# =================================
def init_db():
    conn = sqlite3.connect("english_home.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        client_name TEXT,
        phone TEXT,
        age_group TEXT,
        program TEXT,
        schedule TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =================================
# Данные школы
# =================================
SCHOOL_INFO = {
    "phone": "+7 (939) 489-80-33",
    "address": "г. Кызыл, ТД Континент, ул. Лопсанчапа 35",
    "cabinet": "56 кабинет",
    "working_hours": "08:00 - 21:00",
    "instagram": "english_home17"
}

AGE_GROUPS = {
    'kids_3_4': '👶 Дети 3-4 лет',
    'kids_6_10': '🧒 Дети 6-10 лет',
    'teens': '👦 Подростки 11-17 лет',
    'adults': '👨‍🎓 Взрослые'
}

PROGRAMS = {
    'kids_3_4': '🇬🇧 0 ступень - I can sing / Games',
    'kids_6_10': '🇬🇧 1 ступень - I can speak',
    'teens': '🇬🇧 Английский для подростков',
    'adults': '🇬🇧 Английский для взрослых'
}

PRICES = {
    'kids_3_4': '3600₽ — 2 раза в неделю по 20 минут',
    'kids_6_10': '6500₽ — 2 раза в неделю по 60 минут',
    'teens': '7900₽ — 1 раз в неделю по 2 часа',
    'adults': '7900₽ — 1 раз в неделю по 2 часа'
}

# =================================
# Временное хранилище
# =================================
user_data = {}

# =================================
# Сохранение заявки
# =================================
def save_application(user_id, data):

    conn = sqlite3.connect("english_home.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO applications
    (user_id, username, client_name, phone, age_group, program, schedule)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get("username"),
        data.get("client_name"),
        data.get("phone"),
        data.get("age_group"),
        data.get("program"),
        data.get("schedule")
    ))

    conn.commit()
    app_id = cur.lastrowid
    conn.close()

    return app_id

# =================================
# Уведомление админу
# =================================
def notify_admin(app_id, data):

    text = f"""
🔔 НОВАЯ ЗАЯВКА #{app_id}

👤 {data.get("client_name")}
📞 {data.get("phone")}
👥 {data.get("age_group")}
📚 {data.get("program")}
📅 {data.get("schedule")}

@{data.get("username")}
"""

    bot.send_message(ADMIN_CHAT_ID, text)

# =================================
# Меню
# =================================
def main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("📝 Записаться")
    markup.add("👥 Программы", "💰 Прайс")
    markup.add("📞 Контакты", "ℹ️ О школе")

    return markup

# =================================
# START
# =================================
@bot.message_handler(commands=["start"])
def start(message):

    bot.send_message(
        message.chat.id,
        f"""
🏫 English Home

Привет, {message.from_user.first_name}!

Я помогу записаться на занятия английским.
""",
        reply_markup=main_menu()
    )

# =================================
# Сообщения
# =================================
@bot.message_handler(func=lambda m: True)
def handle_text(message):

    chat_id = message.chat.id
    text = message.text

    # Запись
    if text == "📝 Записаться":

        markup = types.InlineKeyboardMarkup()

        for key, name in AGE_GROUPS.items():
            markup.add(types.InlineKeyboardButton(name, callback_data=f"age_{key}"))

        bot.send_message(chat_id, "Выберите возраст:", reply_markup=markup)

    # Программы
    elif text == "👥 Программы":

        msg = "👥 Программы обучения\n\n"

        for key in PROGRAMS:
            msg += f"{AGE_GROUPS[key]}\n{PROGRAMS[key]}\n\n"

        bot.send_message(chat_id, msg)

    # Прайс
    elif text == "💰 Прайс":

        msg = "💰 Стоимость\n\n"

        for key in PRICES:
            msg += f"{AGE_GROUPS[key]} — {PRICES[key]}\n"

        bot.send_message(chat_id, msg)

    # Контакты
    elif text == "📞 Контакты":

        bot.send_message(chat_id, f"""
📍 Адрес: {SCHOOL_INFO['address']}
🏫 Кабинет: {SCHOOL_INFO['cabinet']}
📞 Телефон: {SCHOOL_INFO['phone']}
🕒 Часы работы: {SCHOOL_INFO['working_hours']}
📷 Instagram: @{SCHOOL_INFO['instagram']}
""")

    # О школе
    elif text == "ℹ️ О школе":

        bot.send_message(chat_id, """
🏫 О школе English Home

Приветствую вас! Меня зовут Монгуш Чечек Шойовна.

Я учитель английского языка, тренер-педагог развития речи на английском языке по методике В.Н. Мещеряковой I Love English (ILE) с 2012 года, методист.

Помогаю детям и взрослым заговорить на английском языке. Это возможно и это реально.

Мы работаем по эмпирической системе I Love English.

Автор методики В.Н. Мещерякова создала методику, которая копирует естественный процесс освоения родного языка.

Сначала слушаем и понимаем, потом говорим, затем читаем и пишем.

🔥 Почему это работает?
Потому что это естественный процесс развития языка.

❓ Кому подойдёт?

Всем, кто готов слушать аудио каждый день и хочет говорить на английском языке.
""")

    # Имя
    elif chat_id in user_data and user_data[chat_id]["state"] == "name":

        user_data[chat_id]["client_name"] = text
        user_data[chat_id]["username"] = message.from_user.username

        user_data[chat_id]["state"] = "phone"

        bot.send_message(chat_id, "Введите номер телефона:")

    # Телефон
    elif chat_id in user_data and user_data[chat_id]["state"] == "phone":

        user_data[chat_id]["phone"] = text

        app_id = save_application(chat_id, user_data[chat_id])

        notify_admin(app_id, user_data[chat_id])

        bot.send_message(chat_id, f"✅ Заявка №{app_id} отправлена!")

        del user_data[chat_id]

# =================================
# Кнопки возраста
# =================================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    chat_id = call.message.chat.id

    if call.data.startswith("age_"):

        key = call.data.replace("age_", "")

        user_data[chat_id] = {
            "state": "name",
            "age_group": AGE_GROUPS[key],
            "program": PROGRAMS[key],
            "schedule": PRICES[key]
        }

        bot.send_message(chat_id, "Введите ваше имя:")

# =================================
# Админ — последние заявки
# =================================
@bot.message_handler(commands=["apps"])
def apps(message):

    if message.chat.id != ADMIN_CHAT_ID:
        return

    conn = sqlite3.connect("english_home.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT id, client_name, phone
    FROM applications
    ORDER BY id DESC
    LIMIT 10
    """)

    rows = cur.fetchall()

    conn.close()

    text = "Последние заявки\n\n"

    for r in rows:
        text += f"#{r[0]}\n👤 {r[1]}\n📞 {r[2]}\n\n"

    bot.send_message(message.chat.id, text)

# =================================
# Запуск
# =================================
if __name__ == "__main__":

    threading.Thread(target=run_flask).start()

    print("Bot started")

    bot.infinity_polling(skip_pending=True)