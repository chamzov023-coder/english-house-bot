import telebot
from telebot import types
import sqlite3
import logging
import os
from flask import Flask
import threading

# =================================
# Flask (для Render)
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
# Токен и админы
# =================================
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    823680495,
    987654321
]

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
    "phone": "89235467182",
    "address": "г. Кызыл, ТД Континент, ул. Лопсанчапа 35",
    "cabinet": "56 кабинет",
    "working_hours": "08:00 - 21:00",
    "vk_school": "https://vk.ru/flowers_languagestudio",
    "vk_teacher": "https://vk.ru/vip.chechek"
}

AGE_GROUPS = {
    'kids_3_4': '👶 Дети 3-4 лет',
    'kids_6_10': '🧒 Дети 6-10 лет',
    'teens': '👦 Подростки 11-17 лет',
    'adults': '👨‍🎓 Взрослые'
}

PROGRAMS = {

    'kids_3_4': """🇬🇧 0 ступень - I can sing / Games
дети учатся воспринимать английский язык на слух, играть и петь песенки на английском языке""",

    'kids_6_10': """🇬🇧 1 ступень - I can speak
дети начинают бегло говорить по-английски, используя в своей речи около 250 слов""",

    'teens': """🇬🇧 Английский для подростков
подготовка к ОГЭ, ЕГЭ только после прохождения предыдущих курсов""",

    'adults': """🇬🇧 Английский для взрослых
для общения, для путешествий и для здоровья мозга 😊"""
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
# Уведомление админам
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

    for admin_id in ADMIN_IDS:
        bot.send_message(admin_id, text)

# =================================
# Главное меню
# =================================
def main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("📝 Записаться")
    markup.add("👥 Программы", "💰 Прайс")
    markup.add("📞 Контакты", "📚 Про English Home")

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

Привет, {message.from_user.first_name}! 👋
Добро пожаловать в English Home.

Помогу выбрать программу и записаться на занятия.
""",
        reply_markup=main_menu()
    )

# =================================
# Текстовые сообщения
# =================================
@bot.message_handler(func=lambda m: True)
def handle_text(message):

    chat_id = message.chat.id
    text = message.text

    if text == "📝 Записаться":

        markup = types.InlineKeyboardMarkup()

        for key, name in AGE_GROUPS.items():
            markup.add(types.InlineKeyboardButton(name, callback_data=f"age_{key}"))

        bot.send_message(chat_id, "Выберите возраст:", reply_markup=markup)

    elif text == "👥 Программы":

        msg = "👥 ПРОГРАММЫ ОБУЧЕНИЯ\n\n"

        for key in PROGRAMS:

            msg += f"{AGE_GROUPS[key]}\n{PROGRAMS[key]}\n\n"

        bot.send_message(chat_id, msg)

    elif text == "💰 Прайс":

        msg = "💰 СТОИМОСТЬ\n\n"

        for key in PRICES:

            msg += f"{AGE_GROUPS[key]} — {PRICES[key]}\n"

        bot.send_message(chat_id, msg)

    elif text == "📞 Контакты":

        bot.send_message(chat_id, f"""
📍 Адрес: {SCHOOL_INFO['address']}
🏫 Кабинет: {SCHOOL_INFO['cabinet']}

📞 Телефон:
{SCHOOL_INFO['phone']}

🕒 Часы работы:
{SCHOOL_INFO['working_hours']}

🌐 VK школы:
{SCHOOL_INFO['vk_school']}

👩‍🏫 VK учителя:
{SCHOOL_INFO['vk_teacher']}
""")

    elif text == "📚 Про English Home":

        bot.send_message(chat_id, """
🏫 English Home

Приветствую вас! Меня зовут Монгуш Чечек Шойовна.

Я учитель английского языка, тренер-педагог развития речи на английском языке по методике В.Н. Мещеряковой I Love English (ILE) с 2012 года, методист.

English Home проводит подготовку и стажировку учителей английского языка.

Помогаю детям и взрослым заговорить на английском языке. Это возможно и это реально.

Мы работаем по эмпирической системе I Love English.

Автор методики В.Н. Мещерякова создала методику, которая копирует естественный процесс освоения родного языка.

Сначала слушаем и понимаем, потом говорим, затем читаем и пишем.

🔥 Почему это работает?
Потому что это естественный процесс развития языка.

❓ Кому подойдёт?

Всем, кто готов слушать аудио каждый день и хочет говорить на английском языке.
""")

    elif chat_id in user_data and user_data[chat_id]["state"] == "name":

        user_data[chat_id]["client_name"] = text
        user_data[chat_id]["username"] = message.from_user.username

        user_data[chat_id]["state"] = "phone"

        bot.send_message(chat_id, "Введите номер телефона:")

    elif chat_id in user_data and user_data[chat_id]["state"] == "phone":

        user_data[chat_id]["phone"] = text

        app_id = save_application(chat_id, user_data[chat_id])

        notify_admin(app_id, user_data[chat_id])

        bot.send_message(chat_id, f"✅ Заявка №{app_id} отправлена!")

        del user_data[chat_id]

# =================================
# Inline кнопки возраста
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

    if message.chat.id not in ADMIN_IDS:
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

    text = "📋 Последние заявки\n\n"

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