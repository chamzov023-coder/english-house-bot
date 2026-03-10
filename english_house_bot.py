import telebot
from telebot import types
import sqlite3
import logging
import os
from flask import Flask
import threading

# =========================
# Flask для Render
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)

# =========================
# Логи
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# Токен
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 823680495

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# =========================
# База данных
# =========================
def init_db():
    conn = sqlite3.connect("english_house.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        client_name TEXT,
        phone TEXT,
        age_group TEXT,
        program TEXT,
        schedule TEXT,
        status TEXT DEFAULT 'новая',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# Данные школы
# =========================
SCHOOL_INFO = {
    "phone": "+7 (939) 489-80-33",
    "address": "г. Кызыл, ТД Континент, ул. Лопсанчапа 35",
    "cabinet": "56 кабинет",
    "working_hours": "08:00 - 21:00",
    "instagram": "english_home17"
}

AGE_GROUPS = {
    "kids_3_4": "👶 Дети 3-4 года",
    "kids_6_10": "🧒 Дети 6-10 лет",
    "teens": "👦 Подростки",
    "adults": "👨‍🎓 Взрослые"
}

PROGRAMS = {
    "kids_3_4": "🇬🇧 0 ступень - I can sing / Games",
    "kids_6_10": "🇬🇧 1 ступень - I can speak",
    "teens": "🇬🇧 Английский для подростков",
    "adults": "🇬🇧 Английский для взрослых"
}

PRICES = {
    "kids_3_4": "3600₽, 2 раза в неделю, 20 минут",
    "kids_6_10": "6500₽, 2 раза в неделю, 60 минут",
    "teens": "7900₽, 1 раз в неделю, 2 часа",
    "adults": "7900₽, 1 раз в неделю, 2 часа"
}

SCHEDULES = {
    "kids_3_4": "ПН, СР, ЧТ с 08:30 до 15:15",
    "kids_6_10": "ПН, СР, ЧТ с 08:30 до 15:15",
    "teens": "СБ с 13:00 до 15:00",
    "adults": "СБ с 13:00 до 15:00"
}

# =========================
# Пользователи
# =========================
user_data = {}

# =========================
# Сохранение заявки
# =========================
def save_application(user_id, data):
    conn = sqlite3.connect("english_house.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO applications
    (user_id, username, client_name, phone, age_group, program, schedule)
    VALUES (?,?,?,?,?,?,?)
    """, (
        user_id,
        data.get("username", ""),
        data.get("client_name", ""),
        data.get("phone", ""),
        data.get("age_group", ""),
        data.get("program", ""),
        data.get("schedule", "")
    ))
    conn.commit()
    app_id = cursor.lastrowid
    conn.close()
    return app_id

# =========================
# Уведомление админу
# =========================
def notify_admin(app_id, data):
    msg = f"""🔔 НОВАЯ ЗАЯВКА #{app_id}

👤 {data.get('client_name')}
📞 {data.get('phone')}
👥 {data.get('age_group')}
📚 {data.get('program')}
📅 {data.get('schedule')}
🆔 @{data.get('username','нет')}
"""
    bot.send_message(ADMIN_CHAT_ID, msg)

# =========================
# Меню
# =========================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Записаться","👥 Программы")
    markup.add("💰 Прайс","📞 Контакты")
    markup.add("ℹ️ О школе")
    return markup

def signup_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👩‍🏫 Офлайн","💻 Онлайн")
    markup.add("⬅️ Назад")
    return markup

def age_group_menu():
    markup = types.InlineKeyboardMarkup()
    for age_id, age_name in AGE_GROUPS.items():
        markup.add(types.InlineKeyboardButton(f"{age_name} ({PROGRAMS[age_id]})", callback_data=f"age_{age_id}"))
    return markup

# =========================
# START
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    text = f"🏫 English House\nПривет, {message.from_user.first_name}!\nВыберите действие:"
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

# =========================
# Основные кнопки
# =========================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    if chat_id in user_data:
        handle_registration(message)
        return

    if text == "📝 Записаться":
        bot.send_message(chat_id, "Выберите формат обучения:", reply_markup=signup_menu())

    elif text == "👩‍🏫 Офлайн":
        user_data[chat_id] = {"state":"waiting_age","format":"офлайн"}
        bot.send_message(chat_id, "Выберите возрастную группу:", reply_markup=age_group_menu())

    elif text == "💻 Онлайн":
        user_data[chat_id] = {"state":"waiting_name","format":"онлайн"}
        bot.send_message(chat_id, "Как вас зовут?")

    elif text == "👥 Программы":
        programs_text = ""
        for k, v in PROGRAMS.items():
            programs_text += f"{v}\n"
        bot.send_message(chat_id, programs_text)

    elif text == "💰 Прайс":
        price_text = ""
        for k, v in PRICES.items():
            price_text += f"{AGE_GROUPS[k]}: {v}\n"
        bot.send_message(chat_id, price_text)

    elif text == "📞 Контакты":
        bot.send_message(chat_id, f"📍 Адрес: {SCHOOL_INFO['address']}\n🏫 {SCHOOL_INFO['cabinet']}\n📞 Телефон: {SCHOOL_INFO['phone']}\n🕒 Часы работы: {SCHOOL_INFO['working_hours']}\n📷 Instagram: @{SCHOOL_INFO['instagram']}")

    elif text == "ℹ️ О школе":
        bot.send_message(chat_id, "🏫 О школе English House\n\nНаши занятия проходят в небольших группах, развивают разговорную речь и уверенное использование английского языка. Программы подходят для детей, подростков и взрослых.")

    elif text == "⬅️ Назад":
        bot.send_message(chat_id, "Главное меню:", reply_markup=main_menu())

# =========================
# Callback для офлайн возрастов
# =========================
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("age_") and chat_id in user_data:
        age_id = data.replace("age_", "")
        user_data[chat_id]["age_group"] = AGE_GROUPS[age_id]
        user_data[chat_id]["program"] = PROGRAMS[age_id]
        user_data[chat_id]["schedule"] = SCHEDULES[age_id]
        user_data[chat_id]["state"] = "waiting_name"
        bot.send_message(chat_id, f"Вы выбрали {AGE_GROUPS[age_id]} ({PROGRAMS[age_id]}).\nВведите ваше имя:")

# =========================
# Регистрация имени и телефона
# =========================
def handle_registration(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    state = user_data[chat_id]["state"]
    text = message.text

    if state == "waiting_name":
        user_data[chat_id]["client_name"] = text
        user_data[chat_id]["username"] = message.from_user.username
        user_data[chat_id]["state"] = "waiting_phone"
        bot.send_message(chat_id, "Введите ваш номер телефона:")

    elif state == "waiting_phone":
        user_data[chat_id]["phone"] = text
        if user_data[chat_id]["format"] == "онлайн":
            user_data[chat_id]["age_group"] = "Онлайн"
            user_data[chat_id]["program"] = "Онлайн обучение"
            user_data[chat_id]["schedule"] = "Нужно обсудить по телефону"

        app_id = save_application(chat_id, user_data[chat_id])
        notify_admin(app_id, user_data[chat_id])
        bot.send_message(chat_id, f"✅ Заявка #{app_id} отправлена! Мы свяжемся с вами для обсуждения времени и даты.")
        del user_data[chat_id]

# =========================
# Админ команда /apps
# =========================
@bot.message_handler(commands=["apps"])
def show_apps(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    conn = sqlite3.connect("english_house.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, client_name, phone, age_group, program, schedule FROM applications ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    text = "📋 Последние заявки:\n\n"
    for r in rows:
        text += f"#{r[0]} {r[3]} | {r[4]} | {r[5]}\n👤 {r[1]} | 📞 {r[2]}\n\n"
    bot.send_message(message.chat.id, text)

# =========================
# Запуск
# =========================
if __name__=="__main__":
    print("🚀 Bot started")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10, none_stop=True, skip_pending=True)