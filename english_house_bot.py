import telebot
from telebot import types
import sqlite3
import logging
import os
from flask import Flask
import threading

# =========================
# Flask (для Render)
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
# Настройки
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
    "address": "г. Кызыл, ТД Континент",
    "working_hours": "08:00 - 21:00",
    "instagram": "english_home17"
}

AGE_GROUPS = {
    "kids_3_4": "👶 Дети 3-4 лет",
    "kids_6_7": "🧒 Дети 6-7 лет",
    "teens": "👦 Подростки 14-15 лет",
    "adults": "👨‍🎓 Взрослые"
}

PROGRAMS = {
    "kids_3_4": "🇬🇧 I can sing",
    "kids_6_7": "🇬🇧 I can speak",
    "teens": "🇬🇧 Английский для подростков",
    "adults": "🇬🇧 Английский для взрослых"
}

SCHEDULES = {
    "kids_3_4": "ПН СР ЧТ 08:30",
    "kids_6_7": "ПН СР ЧТ 08:30",
    "teens": "ПН СР ЧТ 15:00",
    "adults": "СБ 13:00"
}

# =========================
# Временные данные пользователей
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
# Обновление статуса
# =========================

def update_status(app_id, status):

    conn = sqlite3.connect("english_house.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE applications
    SET status = ?
    WHERE id = ?
    """,(status,app_id))

    conn.commit()
    conn.close()

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
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    text=f"""
🏫 English House

Привет {message.from_user.first_name}!

Я помогу записаться
на пробный урок.
"""

    bot.send_message(message.chat.id,text,reply_markup=main_menu())

# =========================
# Текстовые сообщения
# =========================

@bot.message_handler(func=lambda m:True)
def text(message):

    chat_id=message.chat.id
    msg=message.text

    if msg=="📝 Записаться":

        user_data[chat_id]={"state":"name"}
        bot.send_message(chat_id,"Как вас зовут?")

    elif msg=="👥 Программы":

        text="📚 Наши программы:\n\n"

        for age in AGE_GROUPS:
            text+=f"{AGE_GROUPS[age]}\n"
            text+=f"{PROGRAMS[age]}\n\n"

        bot.send_message(chat_id,text)

    elif msg=="📞 Контакты":

        text=f"""
📍 {SCHOOL_INFO["address"]}

📞 {SCHOOL_INFO["phone"]}

🕒 {SCHOOL_INFO["working_hours"]}

📷 @{SCHOOL_INFO["instagram"]}
"""

        bot.send_message(chat_id,text)

    elif msg=="ℹ️ О школе":

        bot.send_message(chat_id,"Школа английского языка с 2015 года")

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

                markup=types.InlineKeyboardMarkup()

                for age in AGE_GROUPS:

                    markup.add(
                        types.InlineKeyboardButton(
                            AGE_GROUPS[age],
                            callback_data=age
                        )
                    )

                bot.send_message(chat_id,"Выберите возрастную группу",reply_markup=markup)

# =========================
# Callback кнопки
# =========================

@bot.callback_query_handler(func=lambda call:True)
def callback(call):

    chat_id=call.message.chat.id
    data=call.data

    if data in AGE_GROUPS:

        user_data[chat_id]["age_group"]=AGE_GROUPS[data]
        user_data[chat_id]["program"]=PROGRAMS[data]
        user_data[chat_id]["schedule"]=SCHEDULES[data]

        app_id=save_application(chat_id,user_data[chat_id])

        notify_admin(app_id,user_data[chat_id])

        bot.edit_message_text(
        f"""
✅ Заявка #{app_id} отправлена!

Мы скоро свяжемся с вами.
""",
        chat_id,
        call.message.message_id
        )

    elif data.startswith("call_"):

        app_id=data.split("_")[1]
        update_status(app_id,"позвонили")
        bot.answer_callback_query(call.id,"Статус: позвонили")

    elif data.startswith("ok_"):

        app_id=data.split("_")[1]
        update_status(app_id,"записан")
        bot.answer_callback_query(call.id,"Статус: записан")

    elif data.startswith("cancel_"):

        app_id=data.split("_")[1]
        update_status(app_id,"отказ")
        bot.answer_callback_query(call.id,"Статус: отказ")

# =========================
# Админ — последние заявки
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
# Админ — открыть заявку
# =========================

@bot.message_handler(commands=["app"])
def open_app(message):

    if message.chat.id!=ADMIN_CHAT_ID:
        return

    try:
        app_id=message.text.split()[1]
    except:
        bot.send_message(message.chat.id,"Например: /app 5")
        return

    conn=sqlite3.connect("english_house.db")
    cursor=conn.cursor()

    cursor.execute("SELECT * FROM applications WHERE id=?",(app_id,))
    app_data=cursor.fetchone()

    conn.close()

    if not app_data:
        bot.send_message(message.chat.id,"Заявка не найдена")
        return

    text=f"""
📋 Заявка #{app_data[0]}

👤 {app_data[3]}
📞 {app_data[4]}

👥 {app_data[5]}
📚 {app_data[6]}
📅 {app_data[7]}

Статус: {app_data[8]}
"""

    markup=types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton("📞 Позвонили",callback_data=f"call_{app_id}"),
        types.InlineKeyboardButton("✅ Записан",callback_data=f"ok_{app_id}")
    )

    markup.add(
        types.InlineKeyboardButton("❌ Отказ",callback_data=f"cancel_{app_id}")
    )

    bot.send_message(message.chat.id,text,reply_markup=markup)

# =========================
# Статистика
# =========================

@bot.message_handler(commands=["stats"])
def stats(message):

    if message.chat.id!=ADMIN_CHAT_ID:
        return

    conn=sqlite3.connect("english_house.db")
    cursor=conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications")
    total=cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM applications
    WHERE date(created_at)=date('now')
    """)
    today=cursor.fetchone()[0]

    conn.close()

    bot.send_message(message.chat.id,f"""
📊 Статистика

Сегодня заявок: {today}

Всего заявок: {total}
""")

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