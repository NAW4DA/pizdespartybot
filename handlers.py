import random
import logging
import telebot
from telebot import types
from datetime import datetime, timedelta
from datetime import datetime as dt
from io import BytesIO
from PIL import Image
from bot import bot
from database import cursor, conn
from admin_handlers import *
from button_menu import *

logging.basicConfig(level=logging.DEBUG)

warn_admin = "@sc4r3dem0t1on"

def compress_image(image_bytes, max_size=(800, 800)):
    image = Image.open(BytesIO(image_bytes))
    image.thumbnail(max_size)
    output = BytesIO()
    image.save(output, format="JPEG")
    output.seek(0)
    return output

def is_user_blocked(user_id):
    cursor.execute("SELECT 1 FROM blocked_users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None

def is_user_frozen(user_id):
    cursor.execute("SELECT freeze_until FROM frozen_users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        freeze_until = result[0]
        freeze_until = datetime.strptime(freeze_until, "%Y-%m-%d %H:%M")
        if dt.now() < freeze_until:
            return True
        else:
            cursor.execute("DELETE FROM frozen_users WHERE user_id=?", (user_id,))
            conn.commit()
    return False

@bot.message_handler(commands=['start'])
def start(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    cursor.execute("SELECT name FROM users WHERE id=?", (message.chat.id,))
    user_name = cursor.fetchone()
    cursor.execute("SELECT user_id FROM admins WHERE user_id=?", (message.chat.id,))
    is_admin = cursor.fetchone()
    if user_name:
        if user_name[0]:
            bot.send_message(message.chat.id, f"👋 С возвращением, {user_name[0]}!")
            if is_admin:
                bot.send_message(message.chat.id, "📋 Админ меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать \n\n• 🛠️ Админ панель", reply_markup=create_admin_menu())
            else:
                bot.send_message(message.chat.id, "📋 Главное меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать", reply_markup=create_main_menu())
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 Начать знакомства", callback_data="start_yes"),
                       types.InlineKeyboardButton("🙅 В другой раз", callback_data="start_no"))
            bot.send_message(message.chat.id, "👋 Wassup! Давай поможем тебе найти компашку на PIZDES PARTY! ⚡️", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚀 Начать знакомства", callback_data="start_yes"),
                   types.InlineKeyboardButton("🙅 В другой раз", callback_data="start_no"))
        bot.send_message(message.chat.id, "👋 Wassup! Давай поможем тебе найти компашку на PIZDES PARTY! ⚡️", reply_markup=markup)
        cursor.execute("INSERT INTO users (id, chat_id, current_profile_id) VALUES (?, ?, ?)", (message.chat.id, message.chat.id, message.chat.id))
        conn.commit()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if is_user_blocked(call.message.chat.id):
        bot.send_message(call.message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(call.message.chat.id):
        bot.send_message(call.message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    if call.data == "start_yes":
        bot.send_message(call.message.chat.id, "🔥 Кайф! Как тебя зовут?")
        bot.register_next_step_handler(call.message, process_name_step)
    elif call.data == "start_no":
        bot.send_message(call.message.chat.id, "Мы были рады тебе! Возвращайся 🙁")

def process_name_step(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    cursor.execute("SELECT id FROM users WHERE id=?", (message.chat.id,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET name = ?, username = ? WHERE id = ?", (message.text, '@' + message.from_user.username, message.chat.id))
    else:
        cursor.execute("INSERT INTO users (id, name, username) VALUES (?, ?, ?)", (message.chat.id, message.text, '@' + message.from_user.username))
    conn.commit()
    bot.send_message(message.chat.id, "🔥 Неплохо! Теперь выбери свой пол:", reply_markup=create_gender_menu())
    bot.register_next_step_handler(message, process_gender_step)

def process_gender_step(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    gender = message.text
    if gender not in ["💙 Мальчик", "💗 Девочка", "👥 Компания"]:
        bot.send_message(message.chat.id, "🚻 Пожалуйста, выберите корректный пол:", reply_markup=create_gender_menu())
        bot.register_next_step_handler(message, process_gender_step)
        return
    cursor.execute("UPDATE users SET gender = ? WHERE id = ?", (gender, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "💭 Теперь укажи, кого ты ищешь здесь:", reply_markup=create_seeking_gender_menu())
    bot.register_next_step_handler(message, process_seeking_gender_step)

def process_seeking_gender_step(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    seeking_gender = message.text
    if seeking_gender not in ["💙 Мальчика", "💗 Девочку", "👥 Компанию"]:
        bot.send_message(message.chat.id, "🚻 Пожалуйста, выберите корректный пол для поиска:", reply_markup=create_seeking_gender_menu())
        bot.register_next_step_handler(message, process_seeking_gender_step)
        return
    cursor.execute("UPDATE users SET seeking_gender = ? WHERE id = ?", (seeking_gender, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "📝 Отлично! Теперь расскажи немного о себе:")
    bot.register_next_step_handler(message, process_description_step)

def process_description_step(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    cursor.execute("UPDATE users SET description = ? WHERE id = ?", (message.text, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "🔢 Хорошо бро, сколько тебе лет?")
    bot.register_next_step_handler(message, process_age_step)

def process_age_step(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    try:
        age = int(message.text)
        if age <= 0:
            raise ValueError
        cursor.execute("UPDATE users SET age = ? WHERE id = ?", (age, message.chat.id))
        conn.commit()
        bot.send_message(message.chat.id, "📸 Okaaay, осталось лишь твое фото!")
        bot.register_next_step_handler(message, process_photo_step)
    except ValueError:
        bot.send_message(message.chat.id, "❗️ Введите корректный возраст, пожалуйста.")
        bot.register_next_step_handler(message, process_age_step)

def process_photo_step(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        compressed_image = compress_image(downloaded_file)

        cursor.execute("UPDATE users SET photo = ? WHERE id = ?", (compressed_image.read(), message.chat.id))
        conn.commit()

        bot.send_message(message.chat.id, "✅ Спасибо за информацию!")
        bot.send_message(message.chat.id, "📋 Главное меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать", reply_markup=create_main_menu())
    else:
        bot.send_message(message.chat.id, "❗️ Пожалуйста, отправьте ваше фото.")
        bot.register_next_step_handler(message, process_photo_step)

@bot.message_handler(func=lambda message: message.text == "🔥 Моя анкета")
def my_profile(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    cursor.execute("SELECT * FROM users WHERE id=?", (message.chat.id,))
    user = cursor.fetchone()
    if user:
        profile_text = f"{user[3]}, {user[4]} лет, описание - \n{user[5]}"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🔄 Изменить возраст", "🖼️ Изменить фото", "✏️ Изменить описание", "🔁 Перезаполнить анкету", "🔍 Смотреть анкеты")
        if user[8]:
            bot.send_message(message.chat.id, "Вот так выглядит твоя анкета:", reply_markup=markup)
            photo_data = user[8]
            photo_bytes = BytesIO(photo_data)
            bot.send_photo(message.chat.id, photo_bytes, caption=profile_text)
        else:
            bot.send_message(message.chat.id, "❌ Фото не найдено.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Ваш профиль не найден.")

@bot.message_handler(func=lambda message: message.text == "🔄 Изменить возраст")
def change_age(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    bot.send_message(message.chat.id, "🔢 Укажите ваш возраст")
    bot.register_next_step_handler(message, update_age)

def update_age(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    try:
        age = int(message.text)
        if age <= 0:
            raise ValueError
        cursor.execute("UPDATE users SET age = ? WHERE id = ?", (age, message.chat.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Ваш возраст успешно обновлен!")
        bot.send_message(message.chat.id, "📋 Главное меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать", reply_markup=create_main_menu())
    except ValueError:
        bot.send_message(message.chat.id, "❗️ Введите корректный возраст, пожалуйста.")
        change_age(message)

@bot.message_handler(func=lambda message: message.text == "🖼️ Изменить фото")
def change_photo(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    bot.send_message(message.chat.id, "📸 Отправьте свое новое фото.")
    bot.register_next_step_handler(message, update_photo)

def update_photo(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        compressed_image = compress_image(downloaded_file)

        cursor.execute("UPDATE users SET photo = ? WHERE id = ?", (compressed_image.read(), message.chat.id))
        conn.commit()

        bot.send_message(message.chat.id, "✅ Ваше фото успешно обновлено!")
        bot.send_message(message.chat.id, "📋 Главное меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать", reply_markup=create_main_menu())
    else:
        bot.send_message(message.chat.id, "❗️ Пожалуйста, отправьте ваше новое фото.")
        bot.register_next_step_handler(message, update_photo)

@bot.message_handler(func=lambda message: message.text == "✏️ Изменить описание")
def change_description(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    bot.send_message(message.chat.id, "📝 Введите новое описание.")
    bot.register_next_step_handler(message, update_description)

def update_description(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    new_description = message.text
    cursor.execute("UPDATE users SET description = ? WHERE id = ?", (new_description, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Ваше описание успешно обновлено!")
    bot.send_message(message.chat.id, "📋 Главное меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "🔁 Перезаполнить анкету")
def refill_profile(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    bot.send_message(message.chat.id, "💘 Давай начнем заново.")
    cursor.execute("UPDATE users SET name = NULL, age = NULL, description = NULL, gender = NULL, seeking_gender = NULL, photo = NULL WHERE id = ?", (message.chat.id,))
    conn.commit()
    start(message)

@bot.message_handler(func=lambda message: message.text == "🔍 Просмотр анкет" or message.text == "🔍 Смотреть анкеты")
def view_profiles(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    cursor.execute("SELECT seeking_gender FROM users WHERE id=?", (message.chat.id,))
    user = cursor.fetchone()
    if user:
        seeking_gender = user[0]
        if seeking_gender in ['💙 Мальчика', '💗 Девочку', '👥 Компанию']:
            gender_map = {
                '💙 Мальчика': '💙 Мальчик',
                '💗 Девочку': '💗 Девочка',
                '👥 Компанию': '👥 Компания'
            }
            seeking_gender = gender_map.get(seeking_gender, seeking_gender)
            
            now = dt.now()
            cursor.execute("""
                SELECT u.*
                FROM users u
                LEFT JOIN mutual_likes ml1 ON (u.id = ml1.user1_id AND ml1.user2_id = ?)
                LEFT JOIN mutual_likes ml2 ON (u.id = ml1.user2_id AND ml1.user1_id = ?)
                LEFT JOIN dislikes d ON (u.id = d.disliked_user_id AND d.user_id = ?)
                LEFT JOIN likes l ON (u.id = l.liked_user_id AND l.user_id = ?)
                LEFT JOIN inactive_users iu ON (u.id = iu.user_id)
                WHERE u.gender = ? AND u.id != ?
                AND (ml1.timestamp IS NULL OR ml1.timestamp < ?)
                AND (ml2.timestamp IS NULL OR ml2.timestamp < ?)
                AND (d.timestamp IS NULL OR d.timestamp < ?)
                AND l.user_id IS NULL
                AND iu.user_id IS NULL
            """, (message.chat.id, message.chat.id, message.chat.id, message.chat.id, seeking_gender, message.chat.id, now - timedelta(hours=24), now - timedelta(hours=24), now - timedelta(hours=24)))
            profiles = cursor.fetchall()
            
            if profiles:
                random_profile = random.choice(profiles)
                cursor.execute("UPDATE users SET current_profile_id = ? WHERE id = ?", (random_profile[0], message.chat.id))
                conn.commit()
                send_profile(message.chat.id, random_profile)
            else:
                bot.send_message(message.chat.id, "📜 Анкет больше нет", reply_markup=create_main_menu())
        else:
            bot.send_message(message.chat.id, "❌ Некорректное значение пола, которое вы ищете.")
    else:
        bot.send_message(message.chat.id, "❌ Ваш профиль не найден.")

def send_profile(chat_id, profile):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    like_button = types.KeyboardButton("❤️")
    dislike_button = types.KeyboardButton("👎")
    b_main = types.KeyboardButton("💤")
    report_button = types.KeyboardButton(f"🚨 Жалоба {profile[0]}")
    markup.add(like_button, dislike_button, b_main, report_button)
    profile_text = f"{profile[3]}, {profile[4]} лет, описание - \n{profile[5]}"
    if profile[8]:
        try:
            photo_data = profile[8]
            photo_bytes = BytesIO(photo_data)
            bot.send_photo(chat_id, photo_bytes, caption=profile_text, reply_markup=markup)
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(chat_id, f"❗️ Ошибка отправки фото: {e}")
    else:
        bot.send_message(chat_id, profile_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "❤️")
def like_profile(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    sender_user_id = message.chat.id

    cursor.execute("SELECT current_profile_id FROM users WHERE id=?", (sender_user_id,))
    current_profile_id = cursor.fetchone()[0]

    cursor.execute("SELECT 1 FROM likes WHERE user_id = ? AND liked_user_id = ?", (current_profile_id, sender_user_id))
    mutual_like = cursor.fetchone()

    cursor.execute("INSERT INTO likes (user_id, liked_user_id, timestamp) VALUES (?, ?, ?)", (sender_user_id, current_profile_id, dt.now()))
    conn.commit()

    if mutual_like:
        cursor.execute("SELECT username FROM users WHERE id = ?", (sender_user_id,))
        sender_username = cursor.fetchone()[0]
        cursor.execute("SELECT username FROM users WHERE id = ?", (current_profile_id,))
        receiver_username = cursor.fetchone()[0]

        sender_contact = f"@{sender_username.lstrip('@')}" if sender_username else f"User ID: {sender_user_id}"
        receiver_contact = f"@{receiver_username.lstrip('@')}" if receiver_username else f"User ID: {current_profile_id}"

        bot.send_message(sender_user_id, f"💕 У вас взаимная симпатия! Думаю у вас будет хорошее общение - {receiver_contact}")
        bot.send_message(current_profile_id, f"💕 У вас взаимная симпатия! Думаю у вас будет хорошее общение - {sender_contact}")

        cursor.execute("DELETE FROM likes WHERE user_id IN (?, ?) AND liked_user_id IN (?, ?)", (sender_user_id, current_profile_id, sender_user_id, current_profile_id))
        conn.commit()

        cursor.execute("INSERT INTO mutual_likes (user1_id, user2_id, timestamp) VALUES (?, ?, ?)", (sender_user_id, current_profile_id, dt.now()))
        conn.commit()
    else:
        cursor.execute("SELECT seeking_gender FROM users WHERE id = ?", (current_profile_id,))
        seeking_gender = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM likes WHERE liked_user_id = ?", (current_profile_id,))
        count = cursor.fetchone()[0]

        if seeking_gender == "💙 Мальчика":
            message_text = f"💬 Вы понравились {count} парню(-ям)! Смотрим?"
        elif seeking_gender == "💗 Девочку":
            message_text = f"💬 Вы понравились {count} девочке(-ам)! Смотрим?"
        elif seeking_gender == "👥 Компанию":
            message_text = f"💬 Вы понравились {count} компании(-ям)! Смотрим?"
        else:
            message_text = f"💬 Вы понравились {count} человеку(-ам)! Смотрим?"

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("Да, смотрим", "Нет, не смотрим")
        bot.send_message(current_profile_id, message_text, reply_markup=markup)

        cursor.execute("INSERT OR IGNORE INTO likes_queue (user_id, liked_user_id) VALUES (?, ?)", (current_profile_id, sender_user_id))
        conn.commit()

    view_profiles(message)
@bot.message_handler(func=lambda message: message.text == "👎")
def dislike_profile(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    sender_user_id = message.chat.id

    cursor.execute("SELECT current_profile_id FROM users WHERE id=?", (sender_user_id,))
    current_profile_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO dislikes (user_id, disliked_user_id, timestamp) VALUES (?, ?, ?)", (sender_user_id, current_profile_id, dt.now()))
    conn.commit()

    view_profiles(message)

@bot.message_handler(func=lambda message: message.text == "🚫 Не хочу никого искать")
def not_looking_for_anyone(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    cursor.execute("INSERT INTO inactive_users (user_id) VALUES (?)", (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "💔 Надеюсь ты нашел ту или того кого искал(а)! С тобой было весело, будем рады твоему возвращению!")

@bot.message_handler(func=lambda message: message.text == "💤")
def back_main(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    bot.send_message(message.chat.id, "📋 Главное меню\n\n• 🔥 Моя анкета \n\n• 🔍 Просмотр анкет \n\n• 🚫 Не хочу никого искать", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "Да, смотрим" or message.text == "Нет, не смотрим")
def handle_view_likes(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    if message.text == "Нет, не смотрим":
        bot.send_message(message.chat.id, "👌 Хорошо, анкета была скрыта.")
        back_main(message)
    else:
        cursor.execute("SELECT user_id FROM likes WHERE liked_user_id=?", (message.chat.id,))
        liked_users = cursor.fetchall()
        if liked_users:
            for user in liked_users:
                cursor.execute("INSERT OR IGNORE INTO likes_queue (user_id, liked_user_id) VALUES (?, ?)", (message.chat.id, user[0]))
            conn.commit()
            show_next_liked_profile(message.chat.id)
        else:
            bot.send_message(message.chat.id, "😓 Пока вас никто не лайкнул.")


def show_next_liked_profile(user_id):
    cursor.execute("SELECT liked_user_id FROM likes_queue WHERE user_id=?", (user_id,))
    next_liked_user = cursor.fetchone()

    if not next_liked_user:
        bot.send_message(user_id, "🔺 Все анкеты просмотрены.", reply_markup=create_main_menu())
        return

    next_liked_user_id = next_liked_user[0]

    cursor.execute("SELECT * FROM users WHERE id=?", (next_liked_user_id,))
    liked_user_info = cursor.fetchone()

    if liked_user_info:
        profile_text = f"{liked_user_info[3]}, {liked_user_info[4]} лет, описание - {liked_user_info[5]}"
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("💘", "💔", "💤", f"🚨 Жалоба {liked_user_info[0]}")

        if liked_user_info[8]:
            photo_data = liked_user_info[8]
            photo_bytes = BytesIO(photo_data)
            bot.send_photo(user_id, photo_bytes, caption=profile_text, reply_markup=markup)
        else:
            bot.send_message(user_id, profile_text, reply_markup=markup)

        cursor.execute("UPDATE users SET current_profile_id = ? WHERE chat_id = ?", (next_liked_user_id, user_id))
        conn.commit()
    else:
        bot.send_message(user_id, "❗️ Не удалось загрузить информацию о пользователе.", reply_markup=create_main_menu())


@bot.message_handler(func=lambda message: message.text in ["💘"])
def like_like_profile(message):
    sender_user_id = message.chat.id

    cursor.execute("SELECT liked_user_id FROM likes_queue WHERE user_id=?", (sender_user_id,))
    row = cursor.fetchone()
    if row:
        current_profile_id = row[0]
    else:
        bot.send_message(sender_user_id, "😖 Ваша очередь лайков пуста.")
        return

    cursor.execute("SELECT 1 FROM likes WHERE user_id = ? AND liked_user_id = ?", (current_profile_id, sender_user_id))
    mutual_like = cursor.fetchone()

    cursor.execute("INSERT INTO likes (user_id, liked_user_id, timestamp) VALUES (?, ?, ?)", (sender_user_id, current_profile_id, dt.now()))
    conn.commit()

    if mutual_like:
        cursor.execute("SELECT username FROM users WHERE id = ?", (sender_user_id,))
        sender_username = cursor.fetchone()[0]
        cursor.execute("SELECT username FROM users WHERE id = ?", (current_profile_id,))
        receiver_username = cursor.fetchone()[0]

        sender_contact = f"@{sender_username.lstrip('@')}" if sender_username else f"User ID: {sender_user_id}"
        receiver_contact = f"@{receiver_username.lstrip('@')}" if receiver_username else f"User ID: {current_profile_id}"

        bot.send_message(sender_user_id, f"💕 У вас взаимная симпатия! Думаю у вас будет хорошее общение - {receiver_contact}")
        bot.send_message(current_profile_id, f"💕 У вас взаимная симпатия! Думаю у вас будет хорошее общение - {sender_contact}")

        cursor.execute("DELETE FROM likes_queue WHERE user_id = ? AND liked_user_id = ?", (sender_user_id, current_profile_id))
        conn.commit()

        cursor.execute("DELETE FROM likes WHERE user_id IN (?, ?) AND liked_user_id IN (?, ?)", (sender_user_id, current_profile_id, sender_user_id, current_profile_id))
        conn.commit()

        cursor.execute("INSERT INTO mutual_likes (user1_id, user2_id, timestamp) VALUES (?, ?, ?)", (sender_user_id, current_profile_id, dt.now()))
        conn.commit()

        show_next_liked_profile(sender_user_id)

@bot.message_handler(func=lambda message: message.text in ["💔"])
def dislike_profile_profile(message):
    sender_user_id = message.chat.id

    cursor.execute("SELECT current_profile_id FROM users WHERE chat_id=?", (sender_user_id,))
    current_profile_id = cursor.fetchone()

    if current_profile_id:
        current_profile_id = current_profile_id[0]

        cursor.execute("INSERT INTO dislikes (user_id, disliked_user_id, timestamp) VALUES (?, ?, ?)", (sender_user_id, current_profile_id, dt.now()))
        conn.commit()
        bot.send_message(message.chat.id, "💔 Вы поставили дизлайк!")

        cursor.execute("DELETE FROM likes_queue WHERE user_id = ? AND liked_user_id = ?", (sender_user_id, current_profile_id))
        conn.commit()

        show_next_liked_profile(sender_user_id)
    else:
        bot.send_message(message.chat.id, "❗️ Не удалось найти текущий профиль.")

def is_admin(user_id):
    cursor.execute("SELECT level FROM admins WHERE user_id=?", (user_id,))
    admin_info = cursor.fetchone()
    return admin_info is not None and admin_info[0] in (1, 2)

@bot.message_handler(func=lambda message: message.text.startswith("🚨 Жалоба"))
def report_profile(message):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    try:
        reported_user_id = int(message.text.split(" ")[2])
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("🔞 Порнография, насилие, кровь, запрещенные вещества", 
                "👎 Оскорбление или травля в чью-то личность",
                "📢 Реклама, пиар",
                "✍️ Другое")
        bot.send_message(message.chat.id, "🔻 Пожалуйста, выберите причину жалобы:", reply_markup=markup)
        bot.register_next_step_handler(message, process_report_reason, reported_user_id)
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❗️ Ошибка в обработке жалобы. Пожалуйста, повторите попытку.")

def process_report_reason(message, reported_user_id):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    reason = message.text
    if reason == "✍️ Другое":
        bot.send_message(message.chat.id, "🔻 Пожалуйста, опишите подробности жалобы:")
        bot.register_next_step_handler(message, process_report_details, reported_user_id)
    else:
        send_report_to_admin(message, reason, reported_user_id)

def process_report_details(message, reported_user_id):
    if is_user_blocked(message.chat.id):
        bot.send_message(message.chat.id, f"❌ Вы были заблокированы! Для подачи апелляции напишите - {warn_admin}")
        return
    if is_user_frozen(message.chat.id):
        bot.send_message(message.chat.id, f"⏸️ Ваш аккаунт временно заморожен! Для подачи апелляции напишите - {warn_admin}")
        return

    reason = message.text
    send_report_to_admin(message, reason, reported_user_id)

def send_report_to_admin(message, reason, reported_user_id):
    cursor.execute("SELECT username, name, age, description, photo FROM users WHERE id=?", (reported_user_id,))
    reported_user_info = cursor.fetchone()
    cursor.execute("SELECT username FROM users WHERE id=?", (message.chat.id,))
    reporting_user_info = cursor.fetchone()
    
    reporter_username = f"{reporting_user_info[0].lstrip('@')}" if reporting_user_info[0] else f"User ID: {message.chat.id}"
    reported_username = f"{reported_user_info[0].lstrip('@')}" if reported_user_info[0] else f"User ID: {reported_user_id}"
    
    reported_name = reported_user_info[1]
    reported_age = reported_user_info[2]
    reported_description = reported_user_info[3]
    reported_photo = reported_user_info[4]

    cursor.execute("""
        INSERT INTO reports (reporter_username, reporter_user_id, reported_username, reported_user_id, reason, report_text, resolved)
        VALUES (?, ?, ?, ?, ?, ?, NULL)
    """, (reporter_username, message.chat.id, reported_username, reported_user_id, reason, f"{reported_name}, {reported_age} лет, описание - {reported_description}"))
    report_id = cursor.lastrowid
    conn.commit()

    report_message = f"🚨 Поступила новая Жалоба #{report_id}\nпосмотреть можно в 📋 Просмотр жалоб"

    cursor.execute("SELECT user_id FROM admins WHERE level IN (1, 2)")
    admin_ids = cursor.fetchall()

    for admin_id in admin_ids:
        if reported_photo:
            bot.send_message(admin_id[0], report_message)
        else:
            bot.send_message(admin_id[0], report_message)
    
    bot.send_message(message.chat.id, "🔻 Апелляция жалобы успешно отправлена на проверку.")
    view_profiles(message)

bot.polling()
