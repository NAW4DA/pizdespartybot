from telebot import types

def create_gender_menu():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("💙 Мальчик", "💗 Девочка", "👥 Компания")
    return markup

def create_seeking_gender_menu():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("💙 Мальчика", "💗 Девочку", "👥 Компанию")
    return markup

def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔥 Моя анкета", "🔍 Просмотр анкет", "🚫 Не хочу никого искать")
    return markup

def create_second_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔥 Моя анкета", "🚫 Не хочу больше никого искать")
    return markup

def create_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔥 Моя анкета", "🔍 Просмотр анкет", "🚫 Не хочу никого искать", "🛠️ Админ панель")
    return markup

def create_into_admin_menu(level):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if level >= 1:
        markup.add("📋 Просмотр жалоб")
    if level >= 2:
        markup.add("👥 Рассылка")
    if level >= 3:
        markup.add("🥶 Просмотр админов", "🚫 Изменить пользователя для обжалования")
    elif level == 1 or level == 2:
        markup.add("🔓 Разблокировать")
    markup.add("⬅️ Назад")
    return markup