from bot import bot
from database import cursor, conn
from telebot import types
from io import BytesIO
import logging
from button_menu import *
from datetime import timedelta, datetime
from datetime import datetime as dt

logging.basicConfig(level=logging.DEBUG)

warn_admin = []

def is_admin(user_id):
    cursor.execute("SELECT level FROM admins WHERE user_id=?", (user_id,))
    admin_info = cursor.fetchone()
    return admin_info is not None and admin_info[0] > 0

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def back_to_main_menu(message):
    bot.send_message(message.chat.id, "🔙 Возвращаемся в главное меню", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "🛠️ Админ панель")
def admin_panel(message):
    logging.debug(f"Received '🛠️ Админ панель' from {message.chat.id}")
    cursor.execute("SELECT level FROM admins WHERE user_id=?", (message.chat.id,))
    admin = cursor.fetchone()
    if admin:
        with open('images/adminxd.gif', 'rb') as gif:
            bot.send_animation(message.chat.id, gif, caption="🔻 Вас приветствует Админ-панель!\n\n🔻 Что будем делать?", reply_markup=create_into_admin_menu(admin[0]))
    else:
        bot.send_message(message.chat.id, "❌ У вас нет прав доступа к этой панели.")

@bot.message_handler(func=lambda message: message.text == "👥 Рассылка")
def manage_users(message):
    cursor.execute("SELECT level FROM admins WHERE user_id=?", (message.chat.id,))
    admin = cursor.fetchone()

    if admin and admin[0] >= 2:
        cancel_button = types.InlineKeyboardButton("❌ Отменить", callback_data="cancel")
        markup = types.InlineKeyboardMarkup().add(cancel_button)
        with open('images/example.png', 'rb') as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption="✍️ Введите текст сообщения для рассылки:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        bot.register_next_step_handler(message, handle_broadcast_message)
    else:
        bot.send_message(message.chat.id, "❌ У вас недостаточно уровня для рассылки. Требуется уровень 2 или выше.")

def handle_broadcast_message(message):
    if message.text == "❌ Отменить":
        bot.send_message(message.chat.id, "🔙 Возвращаемся в главное меню...")
        return

    broadcast_message = message.text
    cursor.execute("SELECT chat_id FROM users")
    users = cursor.fetchall()
    
    successful = 0
    failed = 0

    for user in users:
        try:
            bot.send_message(user[0], broadcast_message, parse_mode='Markdown')
            successful += 1
        except:
            failed += 1

    bot.send_message(
        message.chat.id,
        f"📢 Рассылка завершена\n\n✅ Успешно доставлено: {successful}\n❌ Не удалось доставить: {failed}"
    )

@bot.message_handler(func=lambda message: message.text == "📋 Просмотр жалоб")
def view_reports(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды.")
        return

    send_next_report(message.chat.id)

def send_next_report(admin_id):
    cursor.execute("SELECT id, reporter_username, reporter_user_id, reported_username, reported_user_id, reason, report_text FROM reports WHERE resolved IS NULL")
    report = cursor.fetchone()
    if report:
        report_id = report[0]
        reporter_username = report[1]
        reporter_user_id = report[2]
        reported_username = report[3]
        reported_user_id = report[4]
        reason = report[5]
        report_text = report[6]

        cursor.execute("SELECT name, age, description, photo FROM users WHERE chat_id=?", (reported_user_id,))
        reported_user_info = cursor.fetchone()
        reported_name = reported_user_info[0]
        reported_age = reported_user_info[1]
        reported_description = reported_user_info[2]
        reported_photo = reported_user_info[3]

        profile_text = f"{reported_name}, {reported_age} лет, описание - {reported_description}"

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(f"🚫 Заблокировать {report_id}", f"❌ Игнорировать {report_id}", f"🥶 Заморозить анкету {report_id}")

        report_message = f"🚨 Жалоба #{report_id}\n\n" \
                         f"От пользователя: @{reporter_username} (ID: {reporter_user_id})\n" \
                         f"Нарушитель: @{reported_username} (ID: {reported_user_id})\n\n" \
                         f"Причина жалобы: {reason}\n\n" \
                         f"Анкета нарушителя (ID: {reported_user_id}):\n{profile_text}"

        if reported_photo:
            photo_bytes = BytesIO(reported_photo)
            bot.send_photo(admin_id, photo_bytes, caption=report_message, reply_markup=markup)
        else:
            bot.send_message(admin_id, report_message, reply_markup=markup)
    else:
        bot.send_message(admin_id, "ℹ️ Нет новых жалоб.", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text.startswith("🚫 Заблокировать "))
def block_user(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды.")
        return

    try:
        report_id = int(message.text.split(" ")[2])
        cursor.execute("SELECT reported_user_id FROM reports WHERE id = ?", (report_id,))
        reported_user_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO blocked_users (user_id) VALUES (?)", (reported_user_id,))
        cursor.execute("UPDATE reports SET resolved = 1, resolved_by = ? WHERE id = ?", (message.chat.id, report_id))
        conn.commit()
        bot.send_message(message.chat.id, f"🚫 Пользователь {reported_user_id} заблокирован.")
        send_next_report(message.chat.id)
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Ошибка в обработке блокировки. Пожалуйста, повторите попытку.")

@bot.message_handler(func=lambda message: message.text.startswith("🔓 Разблокировать"))
def unblock_user(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды.")
        return
    try:
        cancel_button = types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_unblock")
        markup = types.InlineKeyboardMarkup().add(cancel_button)
        unblock_message = "Введите ID пользователя для разблокировки"
        sent_message = bot.send_message(message.chat.id, unblock_message, reply_markup=markup)
        bot.register_next_step_handler(sent_message, handle_unblock_user)
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Ошибка в обработке разблокировки. Пожалуйста, повторите попытку.")

def handle_unblock_user(message):
    if message.text == "❌ Отменить":
        cursor.execute("SELECT level FROM admins WHERE user_id=?", (message.chat.id,))
        admin = cursor.fetchone()
        if admin:
            bot.send_message(message.chat.id, "🔙 Возвращаемся в админ-панель...", reply_markup=create_into_admin_menu(admin[0]))
        else:
            bot.send_message(message.chat.id, "🔙 Возвращаемся в главное меню...", reply_markup=create_main_menu())
        return

    try:
        user_id_to_unblock = int(message.text)
        
        cursor.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id_to_unblock,))
        conn.commit()
        
        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, f"✅ Пользователь с ID {user_id_to_unblock} разблокирован.")
        else:
            bot.send_message(message.chat.id, f"❌ Пользователь с ID {user_id_to_unblock} не найден в списке заблокированных.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ID. Пожалуйста, введите числовой ID пользователя.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Произошла ошибка при разблокировке пользователя: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_unblock")
def cancel_unblock_callback(call):
    cursor.execute("SELECT level FROM admins WHERE user_id=?", (call.message.chat.id,))
    admin = cursor.fetchone()
    if admin:
        bot.send_message(call.message.chat.id, "🔙 Возвращаемся в админ-панель...", reply_markup=create_into_admin_menu(admin[0]))
    else:
        bot.send_message(call.message.chat.id, "🔙 Возвращаемся в главное меню...", reply_markup=create_main_menu())


@bot.message_handler(func=lambda message: message.text.startswith("❌ Игнорировать "))
def ignore_user(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды.")
        return

    try:
        report_id = int(message.text.split(" ")[2])
        cursor.execute("UPDATE reports SET resolved = 0, resolved_by = ? WHERE id = ?", (message.chat.id, report_id))
        conn.commit()
        bot.send_message(message.chat.id, f"ℹ️ Жалоба на пользователя проигнорирована.")
        send_next_report(message.chat.id)
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Ошибка в обработке игнорирования. Пожалуйста, повторите попытку.")

@bot.message_handler(func=lambda message: message.text.startswith("🥶 Заморозить анкету "))
def freeze_user(message):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды.")
        return

    try:
        report_id = int(message.text.split(" ")[3])
        cursor.execute("SELECT reported_user_id FROM reports WHERE id = ?", (report_id,))
        reported_user_id = cursor.fetchone()[0]
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("🕒 1 час", "📆 1 день", "📆 1 неделя", "📆 1 месяц")
        bot.send_message(message.chat.id, "⏱ Выберите время заморозки:", reply_markup=markup)
        bot.register_next_step_handler(message, process_freeze_duration, reported_user_id, report_id)
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Ошибка в обработке заморозки. Пожалуйста, повторите попытку.")

def process_freeze_duration(message, reported_user_id, report_id):
    if not is_admin(message.chat.id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды.")
        return

    duration = message.text
    now = dt.now()
    if duration == "🕒 1 час":
        freeze_until = now + timedelta(hours=1)
    elif duration == "📆 1 день":
        freeze_until = now + timedelta(days=1)
    elif duration == "📆 1 неделя":
        freeze_until = now + timedelta(weeks=1)
    elif duration == "📆 1 месяц":
        freeze_until = now + timedelta(days=30)
    freeze_until = freeze_until.strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO frozen_users (user_id, freeze_until) VALUES (?, ?)", (reported_user_id, freeze_until))
    cursor.execute("UPDATE reports SET resolved = 1, resolved_by = ? WHERE id = ?", (message.chat.id, report_id))
    conn.commit()
    bot.send_message(message.chat.id, f"❄️ Пользователь {reported_user_id} заморожен до {freeze_until}.")
    send_next_report(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "🥶 Просмотр админов")
def admin_view_command(message):
    cursor.execute("SELECT level FROM admins WHERE user_id = ?", (message.chat.id,))
    admin = cursor.fetchone()

    if admin and admin[0] >= 3:
        view_admins(message)
    else:
        bot.send_message(message.chat.id, "❌ У вас недостаточно уровня для просмотра списка администраторов. Требуется уровень 3 или выше.")

def view_admins(message):
    cursor.execute("SELECT username, user_id, level FROM admins")
    admins = cursor.fetchall()
    
    if admins:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for admin in admins:
            username = admin[0] if admin[0] else f"Telegram ID: {admin[1]}"
            level = admin[2]
            button_text = f"{username} | LVL {level}"
            markup.add(types.InlineKeyboardButton(button_text, callback_data=f"admin_info_{admin[1]}"))
        
        markup.add(types.InlineKeyboardButton("🧊 Добавить админа", callback_data="add_admin"))
        
        bot.send_message(message.chat.id, "📋 Список администраторов:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "ℹ️ В списке администраторов пока никого нет.")

@bot.callback_query_handler(func=lambda call: call.data == 'add_admin')
def add_admin_callback(call):
    bot.send_message(call.message.chat.id, "🔍 Введите @username нового администратора:")
    bot.register_next_step_handler(call.message, process_new_admin_username)

def process_new_admin_username(message):
    new_admin_username = message.text.strip('@')
    try:
        cursor.execute("SELECT chat_id FROM users WHERE username = ?", (new_admin_username,))
        user_id = cursor.fetchone()
        if user_id:
            bot.send_message(message.chat.id, f"🔍 Найден пользователь @{new_admin_username}. Введите уровень администратора (1-3):\n\nP.S \n1️⃣ LVL - жалобы\n2️⃣ LVL - жалобы + рассылка\n3️⃣ LVL - управление админами + рассылка")
            bot.register_next_step_handler(message, lambda m: process_new_admin_level(m, user_id[0], new_admin_username))
        else:
            bot.send_message(message.chat.id, f"❌ Пользователь @{new_admin_username} не найден в базе данных пользователей. Пожалуйста, добавьте его в список пользователей перед назначением администратором.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Произошла ошибка при поиске пользователя в базе данных: {e}")

def process_new_admin_level(message, new_admin_id, new_admin_username):
    try:
        new_level = int(message.text)
        if new_level < 1 or new_level > 3:
            bot.send_message(message.chat.id, "❌ Неверное значение уровня. Пожалуйста, введите число от 1 до 3.")
            return
        current_date = datetime.now().strftime("%Y-%m-%d %H:%М:%S")
        cursor.execute("INSERT INTO admins (user_id, username, level, joined_date) VALUES (?, ?, ?, ?)", (new_admin_id, f"@{new_admin_username}", new_level, current_date))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Администратор @{new_admin_username} с ID {new_admin_id} и уровнем {new_level} успешно добавлен.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ввода. Пожалуйста, введите число от 1 до 3.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_info_'))
def admin_info_callback(call):
    admin_id = call.data.split('_')[2]
    cursor.execute("SELECT username, user_id, level, joined_date FROM admins WHERE user_id = ?", (admin_id,))
    admin_data = cursor.fetchone()
    if admin_data:
        username = admin_data[0]
        user_id = admin_data[1]
        level = admin_data[2]
        joined_date = admin_data[3]
        
        cursor.execute("SELECT COUNT(*) FROM reports WHERE resolved = 1 AND resolved_by = ?", (user_id,))
        resolved_reports = cursor.fetchone()[0]
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("🚫 Отстранить", callback_data=f"ban_admin_{admin_id}"),
            types.InlineKeyboardButton("📊 Указать уровень", callback_data=f"set_level_{admin_id}")
        )
        keyboard.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin_menu"))
        
        bot.send_message(call.message.chat.id, f"👤 *Пользователь:* {username}\n🆔 *TG ID:* {user_id}\n🔒 *Уровень администратора:* {level}\n📅 *Дата вступления:* {joined_date}\n✅ *Решено жалоб:* {resolved_reports}", parse_mode='Markdown', reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, "❌ Ошибка: Администратор не найден.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('ban_admin_'))
def ban_admin_callback(call):
    admin_id = call.data.split('_')[2]
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (admin_id,))
    conn.commit()
    bot.answer_callback_query(call.id, "❌ Администратор удален")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_admin_menu')
def back_to_admin_menu_callback(call):
    cursor.execute("SELECT level FROM admins WHERE user_id = ?", (call.message.chat.id,))
    admin = cursor.fetchone()
    if admin:
        bot.send_message(call.message.chat.id, "🔙 Возвращаемся в админ-панель", reply_markup=create_into_admin_menu(admin[0]))
    else:
        bot.send_message(call.message.chat.id, "❌ У вас нет прав доступа к этой панели.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_level_'))
def set_level_callback(call):
    admin_id = call.data.split('_')[2]
    bot.send_message(call.message.chat.id, "Введите новый уровень администратора (1-3):\n\nP.S \n1 LVL - жалобы\n2 LVL - жалобы + рассылка 3 LVL - управление админами + рассылка")
    bot.register_next_step_handler(call.message, lambda message: process_level_setting(message, admin_id))

def process_level_setting(message, admin_id):
    try:
        new_level = int(message.text)
        if new_level < 1 or new_level > 3:
            bot.send_message(message.chat.id, "❌ Неверное значение уровня. Пожалуйста, введите число от 1 до 3.")
            return
        cursor.execute("UPDATE admins SET level = ? WHERE user_id = ?", (new_level, admin_id))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ Уровень администратора успешно обновлен на {new_level}")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Неверный формат ввода. Пожалуйста, введите число от 1 до 3.")

@bot.message_handler(func=lambda message: message.text == "🚫 Изменить пользователя для обжалования")
def change_user_for_appeal(message):
    cancel_button = types.InlineKeyboardButton("❌ Отменить", callback_data="back_to_admin_menu")
    markup = types.InlineKeyboardMarkup().add(cancel_button)
    bot.send_message(message.chat.id, "🔍 Введите @username пользователя куда будут писать обжалования:", reply_markup=markup)
    bot.register_next_step_handler(message, process_user_for_appeal)

def process_user_for_appeal(message):
    username_for_appeal = message.text
    warn_admin.clear()
    warn_admin.append(username_for_appeal)
    bot.send_message(message.chat.id, f"✅ Пользователь @{username_for_appeal} добавлен для обжалования.")
