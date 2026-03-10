import telebot
from telebot import types
import sqlite3
import logging
import os
from flask import Flask, request

# =========================
# Flask для Render
# =========================

app = Flask(__name__)

# =========================
# Логи
# =========================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# Токен и админ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 823680495
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://english-house-bot.onrender.com/

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
# Данные школы и программы
# =========================

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
    'teens': '👦 Подростки',
    'adults': '👨‍🎓 Взрослые'
}

PROGRAMS = {
    'kids_3_4': '🇬🇧 0 ступень - I can sing / Games',
    'kids_6_10': '🇬🇧 1 ступень - I can speak',
    'teens': 'Английский для подростков',
    'adults': 'Английский для взрослых'
}

PRICES = {
    'kids_3_4': '💰 3600₽, 2 раза в неделю по 20 минут',
    'kids_6_10': '💰 6500₽, 2 раза в неделю по 60 минут',
    'teens': '💰 7900₽, 1 раз в неделю по 2 часа',
    'adults': '💰 7900₽, 1 раз в неделю по 2 часа'
}

ABOUT_SCHOOL = """
🏫 О школе English House

Мы обучаем английскому детей, подростков и взрослых.
Наши занятия проходят в небольших группах, внимание каждому ученику.
Мы развиваем разговорную речь, понимание языка и уверенность в использовании английского.
"""

user_data = {}

# =========================
# Сохранение заявки
# =========================

def save_application(user_id, data):
    conn = sqlite3.connect("english_house.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO applications(user_id,username,client_name,phone,age_group,program,schedule)
    VALUES (?,?,?,?,?,?,?)
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
    app_id = cursor.lastrowid
    conn.close()
    return app_id

# =========================
# Уведомление админу
# =========================

def notify_admin(app_id, data):
    text = f"""
🔔 НОВАЯ ЗАЯВКА #{app_id}

👤 {data['client_name']}
📞 {data['phone']}
👥 {data['age_group']}
📚 {data['program']}
📅 {data['schedule']}

@{data['username']}
"""
    bot.send_message(ADMIN_CHAT_ID, text)

# =========================
# Меню
# =========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Записаться","👥 Программы")
    markup.add("💰 Прайс","📞 Контакты","ℹ️ О школе")
    return markup

def signup_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👩‍🏫 Офлайн","💻 Онлайн")
    markup.add("⬅️ Назад")
    return markup

# =========================
# Обработчики сообщений
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    text = f"🏫 English House\nПривет {message.from_user.first_name}!\nЯ помогу записаться на занятия английским."
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    msg = message.text

    if msg == "📝 Записаться":
        bot.send_message(chat_id, "Выберите формат обучения", reply_markup=signup_menu())

    elif msg == "👩‍🏫 Офлайн":
        # Добавляем выбор возраста и программы
        markup = types.InlineKeyboardMarkup()
        for key, name in AGE_GROUPS.items():
            markup.add(types.InlineKeyboardButton(name, callback_data=f"offline_{key}"))
        bot.send_message(chat_id, "Выберите возрастную группу:", reply_markup=markup)
        user_data[chat_id] = {"state":"waiting_age", "format":"офлайн"}

    elif msg == "💻 Онлайн":
        user_data[chat_id] = {"state":"name", "format":"онлайн"}
        bot.send_message(chat_id, "Как вас зовут?")

    elif msg == "👥 Программы":
        text = "📚 ПРОГРАММЫ ОБУЧЕНИЯ\n"
        for key, name in PROGRAMS.items():
            text += f"{AGE_GROUPS[key]}: {name}\n"
        bot.send_message(chat_id, text)

    elif msg == "💰 Прайс":
        text = "💰 Цены и расписание занятий\n"
        for key, price in PRICES.items():
            text += f"{AGE_GROUPS[key]}: {price}\n"
        bot.send_message(chat_id, text)

    elif msg == "📞 Контакты":
        text = f"""
📍 Адрес: {SCHOOL_INFO['address']}
🏫 Кабинет: {SCHOOL_INFO['cabinet']}
📞 Телефон: {SCHOOL_INFO['phone']}
🕒 Часы работы: {SCHOOL_INFO['working_hours']}
📷 Instagram: @{SCHOOL_INFO['instagram']}
"""
        bot.send_message(chat_id, text)

    elif msg == "ℹ️ О школе":
        bot.send_message(chat_id, ABOUT_SCHOOL)

    elif msg == "⬅️ Назад":
        bot.send_message(chat_id, "Главное меню", reply_markup=main_menu())

# =========================
# Callback для офлайн
# =========================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if call.data.startswith("offline_"):
        key = call.data.replace("offline_", "")
        if chat_id in user_data:
            user_data[chat_id]["age_group"] = AGE_GROUPS[key]
            user_data[chat_id]["program"] = PROGRAMS[key]
            user_data[chat_id]["schedule"] = PRICES[key]
            user_data[chat_id]["state"] = "name"
        bot.send_message(chat_id, "Как вас зовут?")

# =========================
# Обработка имени и телефона
# =========================

@bot.message_handler(func=lambda m: m.chat.id in user_data)
def handle_user_data(message):
    chat_id = message.chat.id
    state = user_data[chat_id].get("state")
    msg = message.text

    if state == "name":
        user_data[chat_id]["client_name"] = msg
        user_data[chat_id]["username"] = message.from_user.username
        user_data[chat_id]["state"] = "phone"
        bot.send_message(chat_id, "Введите номер телефона:")

    elif state == "phone":
        user_data[chat_id]["phone"] = msg
        # Для онлайн просто указываем "Нужно обсудить"
        if user_data[chat_id]["format"] == "онлайн":
            user_data[chat_id]["age_group"] = "Онлайн"
            user_data[chat_id]["program"] = "Онлайн обучение"
            user_data[chat_id]["schedule"] = "Нужно обсудить по телефону"
        app_id = save_application(chat_id, user_data[chat_id])
        notify_admin(app_id, user_data[chat_id])
        bot.send_message(chat_id, f"✅ Заявка #{app_id} отправлена!\nМы скоро перезвоним вам, чтобы обсудить время и дату занятий.")
        del user_data[chat_id]

# =========================
# Админ команды
# =========================

@bot.message_handler(commands=["apps"])
def apps(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    conn = sqlite3.connect("english_house.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, client_name, phone, status
    FROM applications
    ORDER BY id DESC
    LIMIT 10
    """)
    rows = cursor.fetchall()
    conn.close()
    text = "📋 Последние заявки\n\n"
    for r in rows:
        text += f"#{r[0]}\n👤 {r[1]}\n📞 {r[2]}\nСтатус: {r[3]}\n\n"
    bot.send_message(message.chat.id, text)

# =========================
# Webhook для Render
# =========================

@app.route('/', methods=['POST'])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return "OK", 200

# =========================
# Запуск
# =========================

if __name__ == "__main__":
    # Ставим webhook
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)