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

PROGRAMS_TEXT = """
📚 ПРОГРАММЫ ОБУЧЕНИЯ

👶 0 ступень (3-4 года)
🇬🇧 I can sing / Games
💰 3600₽
📅 2 раза в неделю
⏱ 20 минут

🧒 Дети 6-10 лет
🇬🇧 I can speak
💰 6500₽
📅 2 раза в неделю
⏱ 60 минут

👦 Подростки
💰 7900₽
📅 1 раз в неделю
⏱ 2 часа

👨‍🎓 Взрослые
💰 7900₽
📅 1 раз в неделю
⏱ 2 часа
"""

ABOUT_SCHOOL = """
🏫 О школе English House

Мы обучаем английскому языку детей, подростков и взрослых.

📚 Наши занятия проходят в небольших группах, что позволяет уделить внимание каждому ученику.

Мы используем современные методики обучения, развиваем разговорную речь, понимание языка и уверенность в использовании английского.

Наши программы подходят для:
• детей
• подростков
• взрослых

Мы помогаем ученикам развивать навыки общения, понимания и уверенного использования английского языка.
"""

# =========================
# Данные пользователей
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
    (user_id,username,client_name,phone,age_group,program,schedule)
    VALUES (?,?,?,?,?,?,?)
    """,(
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

def notify_admin(app_id,data):

    text=f"""
🔔 НОВАЯ ЗАЯВКА #{app_id}

👤 {data['client_name']}
📞 {data['phone']}

👥 {data['age_group']}
📚 {data['program']}
📅 {data['schedule']}

@{data['username']}
"""

    bot.send_message(ADMIN_CHAT_ID,text)

# =========================
# Главное меню
# =========================

def main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("📝 Записаться","👥 Программы")
    markup.add("📞 Контакты","ℹ️ О школе")

    return markup

# =========================
# Меню записи
# =========================

def signup_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("👩‍🏫 Офлайн","💻 Онлайн")
    markup.add("⬅️ Назад")

    return markup

# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    text=f"""
🏫 English House

Привет {message.from_user.first_name}!

Я помогу записаться
на занятия английским.
"""

    bot.send_message(message.chat.id,text,reply_markup=main_menu())

# =========================
# Текстовые сообщения
# =========================

@bot.message_handler(func=lambda m:True)
def handle_text(message):

    chat_id = message.chat.id
    msg = message.text

    if msg == "📝 Записаться":

        bot.send_message(chat_id,"Выберите формат обучения",reply_markup=signup_menu())

    elif msg == "👩‍🏫 Офлайн":

        user_data[chat_id]={"state":"name","format":"офлайн"}

        bot.send_message(chat_id,"Как вас зовут?")

    elif msg == "💻 Онлайн":

        user_data[chat_id]={"state":"name","format":"онлайн"}

        bot.send_message(chat_id,"Как вас зовут?")

    elif msg == "👥 Программы":

        bot.send_message(chat_id,PROGRAMS_TEXT)

    elif msg == "📞 Контакты":

        text=f"""
📍 Адрес:
{SCHOOL_INFO["address"]}

🏫 {SCHOOL_INFO["cabinet"]}

📞 Телефон:
{SCHOOL_INFO["phone"]}

🕒 Часы работы:
{SCHOOL_INFO["working_hours"]}

📷 Instagram:
@{SCHOOL_INFO["instagram"]}
"""

        bot.send_message(chat_id,text)

    elif msg == "ℹ️ О школе":

        bot.send_message(chat_id,ABOUT_SCHOOL)

    elif msg == "⬅️ Назад":

        bot.send_message(chat_id,"Главное меню",reply_markup=main_menu())

    else:

        if chat_id in user_data:

            state=user_data[chat_id]["state"]

            if state=="name":

                user_data[chat_id]["client_name"]=msg
                user_data[chat_id]["username"]=message.from_user.username
                user_data[chat_id]["state"]="phone"

                bot.send_message(chat_id,"Введите номер телефона")

            elif state=="phone":

                user_data[chat_id]["phone"]=msg

                format_type=user_data[chat_id]["format"]

                if format_type=="онлайн":

                    user_data[chat_id]["age_group"]="Онлайн"
                    user_data[chat_id]["program"]="Онлайн обучение"
                    user_data[chat_id]["schedule"]="Нужно обсудить по телефону"

                else:

                    user_data[chat_id]["age_group"]="Офлайн"
                    user_data[chat_id]["program"]="Офлайн обучение"
                    user_data[chat_id]["schedule"]="По расписанию школы"

                app_id=save_application(chat_id,user_data[chat_id])

                notify_admin(app_id,user_data[chat_id])

                bot.send_message(chat_id,f"""
✅ Заявка #{app_id} отправлена!

Мы скоро перезвоним вам,
чтобы обсудить время и дату занятий.
""")

                del user_data[chat_id]

# =========================
# Админ команды
# =========================

@bot.message_handler(commands=["apps"])
def apps(message):

    if message.chat.id!=ADMIN_CHAT_ID:
        return

    conn=sqlite3.connect("english_house.db")
    cursor=conn.cursor()

    cursor.execute("""
    SELECT id,client_name,phone,status
    FROM applications
    ORDER BY id DESC
    LIMIT 10
    """)

    rows=cursor.fetchall()
    conn.close()

    text="📋 Последние заявки\n\n"

    for r in rows:

        text+=f"""
#{r[0]}
👤 {r[1]}
📞 {r[2]}
Статус: {r[3]}
"""

    bot.send_message(message.chat.id,text)

# =========================
# Запуск
# =========================

if __name__=="__main__":

    print("🚀 Bot started")

    flask_thread=threading.Thread(target=run_flask)
    flask_thread.start()

    bot.infinity_polling(
        timeout=20,
        long_polling_timeout=10,
        none_stop=True,
        skip_pending=True
    )