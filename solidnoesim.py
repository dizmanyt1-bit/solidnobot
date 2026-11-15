import telebot
import json
import os
import re
import time
import logging
import shutil
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton as _InlineKeyboardButton
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# НАСТРОЙКИ (Solidno eSIM)
# ============================================================
TOKEN = os.getenv("BOT_TOKEN", "9207375074:AAG4Ty7tJZzfXUo8t9UjmLpEmg0Qa9PGuz8")
if not TOKEN:
    raise RuntimeError("Укажи токен бота в переменной окружения BOT_TOKEN")

ADMIN_IDS = os.getenv("ADMIN_IDS", "8720533304,8761907131").split(",")
SUPPORT_USERNAME = "solidnowork"
SERVICE_NAME = "Solidno eSIM"

# НАСТРОЙКИ ДЛЯ ОБЯЗАТЕЛЬНОЙ ПОДПИСКИ
CHANNEL_ID = "@INFOSOLIDNO"  
CHANNEL_URL = "https://t.me/INFOSOLIDNO" 

# ССЫЛКА НА ТВОЮ СТАТЬЮ С ПРАВИЛАМИ В TELEGRAPH
RULES_URL = "https://telegra.ph/Pravila-raboty-SOLIDNO-ESIM-11-07" 

DATA_FILE = "solidno_esim_data.json"
IMAGES_FOLDER = "solidno_esim_images"

if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)
if not os.path.exists("backups"):
    os.makedirs("backups")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['emojiid'])
def get_emoji_id(message):
    found = False
    for entity in message.entities or []:
        if entity.type == "custom_emoji":
            bot.reply_to(message, entity.custom_emoji_id)
            found = True
    if not found:
        bot.reply_to(message, "Не найден Premium Emoji!")

# ============================================================
# PREMIUM EMOJI
# ============================================================
CUSTOM_EMOJI_IDS = {
    "👋": "5282967425149609980", "📱": "5406745015365943482", "📋": "5282843764451195532", "👤": "5334544901428229844", "📊": "5231200819986047254",
    "🆘": "5460755126761312667", "💸": "5267131305203636582", "📩": "5409346017495656775", "🔙": "5352759161945867747", "📢": "5388632425314140043",    
    "✅": "5368832943907151548", "📄": "5269609320944772058", "📥": "5253742260054409879", "📝": "5395444784611480792", "⏳": "5175181110572745347",
    "💰": "5436001155765279046", "❌": "5210952531676504517", "⚠️": "5447644880824181073", "📅": "5274055917766202507", "📆": "6071398415672020586",
    "🌍": "5399898266265475100", "🔐": "5472308992514464048", "⚙️": "5341715473882955310", "📞": "5465624021947140508", "📡": "5388704211397522006",
    "📸": "5235837920081887219", "📭": "5352896944496728039", "❓": "5436113877181941026", "🕒": "5440621591387980068", "🏦": "5264895611517300926",
    "📜": "5388922215347534633", "💳": "5445353829304387411", "🔗": "5271604874419647061", "🔄": "5346269127059196142", "👥": "5388738824538959063",
    "🆔": "5014902839575577394", "👇": "5470177992950946662", "👆": "5469718869536940860", "🚀": "5188481279963715781", "⛔": "5260293700088511294",
    "🔴": "5343961844857973520", "⚫️": "5343733807864362193", "🟡": "5343909802739249278", "🟢": "5343873355646775152", "🟣": "5431368281917265384",
    "🟠": "5444876813056644300", "🔵": "5345944277207755575", "🟤": "5344039673960344837", "🔷": "5345957144929775175", "1️⃣": "5382322671679708881",
    "2️⃣": "5381990043642502553", "3️⃣": "5381879959335738545", "4️⃣": "5382054253403577563", "5️⃣": "5391197405553107640", 
}

def _premium_entities(text):
    if not isinstance(text, str) or not text:
        return []
    matches = []
    for emoji, custom_id in CUSTOM_EMOJI_IDS.items():
        if not custom_id:
            continue
        start = 0
        while True:
            pos = text.find(emoji, start)
            if pos < 0:
                break
            end = pos + len(emoji)
            offset = len(text[:pos].encode("utf-16-le")) // 2
            length = len(text[pos:end].encode("utf-16-le")) // 2
            matches.append((pos, end, offset, length, str(custom_id)))
            start = end
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    entities = []
    last_end = -1
    for _, end, offset, length, custom_id in matches:
        if offset < last_end:
            continue
        entities.append(telebot.types.MessageEntity(
            type="custom_emoji", offset=offset, length=length,
            custom_emoji_id=custom_id
        ))
        last_end = offset + length
    return entities

_original_send_message = bot.send_message
def _send_message_with_premium(*args, **kwargs):
    text_value = kwargs.get("text", args[1] if len(args) > 1 else None)
    if "entities" not in kwargs:
        entities = _premium_entities(text_value)
        if entities:
            kwargs["entities"] = entities
    return _original_send_message(*args, **kwargs)
bot.send_message = _send_message_with_premium

_original_send_photo = bot.send_photo
def _send_photo_with_premium(*args, **kwargs):
    caption = kwargs.get("caption", args[2] if len(args) > 2 else None)
    if "caption_entities" not in kwargs:
        entities = _premium_entities(caption)
        if entities:
            kwargs["caption_entities"] = entities
    return _original_send_photo(*args, **kwargs)
bot.send_photo = _send_photo_with_premium

_original_edit_message_text = bot.edit_message_text
def _edit_message_text_with_premium(*args, **kwargs):
    text_value = kwargs.get("text", args[0] if args else None)
    if "entities" not in kwargs:
        entities = _premium_entities(text_value)
        if entities:
            kwargs["entities"] = entities
    return _original_edit_message_text(*args, **kwargs)
bot.edit_message_text = _edit_message_text_with_premium

def InlineKeyboardButton(text, *args, **kwargs):
    if isinstance(text, str):
        for emoji, custom_id in CUSTOM_EMOJI_IDS.items():
            if custom_id and text.startswith(emoji):
                kwargs.setdefault("icon_custom_emoji_id", str(custom_id))
                text = text[len(emoji):].lstrip()
                break
    return _InlineKeyboardButton(text, *args, **kwargs)

# ============================================================
# БЕЗОПАСНОСТЬ
# ============================================================
user_last_message = {}
MESSAGE_COOLDOWN = 0.1
MAX_MESSAGES_PER_MINUTE = 999
user_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_TIME = 300

def check_rate_limit(user_id):
    now = time.time()
    if user_id not in user_last_message:
        user_last_message[user_id] = []
    user_last_message[user_id] = [t for t in user_last_message[user_id] if now - t < 60]
    if len(user_last_message[user_id]) >= MAX_MESSAGES_PER_MINUTE:
        return False
    if user_last_message[user_id] and now - user_last_message[user_id][-1] < MESSAGE_COOLDOWN:
        return False
    user_last_message[user_id].append(now)
    return True

def check_attempts(user_id):
    now = time.time()
    if user_id not in user_attempts:
        user_attempts[user_id] = {"count": 0, "blocked_until": 0}
    if user_attempts[user_id]["blocked_until"] > now:
        remaining = int(user_attempts[user_id]["blocked_until"] - now)
        return False, f"⛔ Ожидание: {remaining} сек."
    return True, None

def increment_attempts(user_id):
    now = time.time()
    if user_id not in user_attempts:
        user_attempts[user_id] = {"count": 0, "blocked_until": 0}
    user_attempts[user_id]["count"] += 1
    if user_attempts[user_id]["count"] >= MAX_ATTEMPTS:
        user_attempts[user_id]["blocked_until"] = now + BLOCK_TIME
        user_attempts[user_id]["count"] = 0
        return True
    return False

def reset_attempts(user_id):
    if user_id in user_attempts:
        user_attempts[user_id]["count"] = 0
        user_attempts[user_id]["blocked_until"] = 0

# ============================================================
# РАБОТА С ДАННЫМИ
# ============================================================
def backup_data():
    if os.path.exists(DATA_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            shutil.copy2(DATA_FILE, f"backups/{DATA_FILE}_{timestamp}.backup")
        except: pass
        try:
            backups = sorted([f for f in os.listdir("backups") if f.endswith(".backup")])
            for old in backups[:-10]:
                os.remove(f"backups/{old}")
        except: pass

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for uid, u_data in data.items():
                    if "esims" in u_data:
                        for esim in u_data["esims"]:
                            if "status" not in esim:
                                esim["status"] = "queue"
                return data
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
    return {}

def save_data(data):
    try:
        backup_data()
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

user_stats = load_data()
user_states = {}

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

def get_operator_price(operator_name):
    prices = {
        "🔴 МТС-20$": 20.0, 
        "⚫️ Теле2-20$": 20.0,
        "🟡 Билайн-20$": 20.0, 
        "🟢 Сбер-19$": 19.0,
        "🟣 Миранда-21.5$": 21.5, 
        "🟠 Добросвязь-20$": 20.0,
        "🔵 Тбанк-20$": 20.0, 
        "🟤 Газпром-20$": 20.0,
        "🔷 Альфа-39$": 39.0,
    }
    return prices.get(operator_name, 0.0)

def create_user_profile(user_id, username):
    if user_id not in user_stats:
        user_stats[user_id] = {
            "username": username, "loaded": 0, "queue": 0, "in_work": 0, "checked": 0,
            "blocked": 0, "no_scan": 0, "last_load": None, "balance": 0.0,
            "pending_withdraw": None, "esims": [], "balance_history": [],
            "agreed_rules": False
        }
        save_data(user_stats)
    else:
        user_stats[user_id]["username"] = username
        if "in_work" not in user_stats[user_id]:
            user_stats[user_id]["in_work"] = 0
        if "agreed_rules" not in user_stats[user_id]:
            user_stats[user_id]["agreed_rules"] = False

def send_photo_or_text(chat_id, photo_name, text, markup):
    try:
        if os.path.exists(photo_name):
            with open(photo_name, "rb") as photo:
                bot.send_photo(chat_id, photo, caption=text, reply_markup=markup)
        else:
            bot.send_message(chat_id, text, reply_markup=markup)
    except Exception as e:
        logger.error(f"Ошибка отправки фото {photo_name}: {e}")
        bot.send_message(chat_id, text, reply_markup=markup)

# ============================================================
# ПРОВЕРКА ПОДПИСКИ И ПРАВИЛА
# ============================================================
def check_subscription(user_id):
    if is_admin(user_id):
        return True
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return True

def sub_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📢 Наш Канал", url=CHANNEL_URL),
        InlineKeyboardButton("✅ Проверить Подписку", callback_data="check_sub")
    )
    return markup

def rules_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📄 Правила Сервиса", url=RULES_URL),
        InlineKeyboardButton("✅ Принимаю Условия", callback_data="agree_rules")
    )
    return markup

# ============================================================
# ИНЛАЙН-КЛАВИАТУРЫ
# ============================================================
def main_inline_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📱 Сдать Куар-Код", callback_data="menu_sdat"),
        InlineKeyboardButton("📋 Мои Заявки", callback_data="menu_moi"),
        InlineKeyboardButton("👤 Мой Профиль", callback_data="menu_lk"),
        InlineKeyboardButton("📊 Аналитика", callback_data="menu_stats"),
        InlineKeyboardButton("🆘 Связь с Оператором", url=f"https://t.me/{SUPPORT_USERNAME}"),
        InlineKeyboardButton("💸 Вывести Средства", callback_data="menu_vyvod")
    )
    if is_admin(user_id):
        markup.add(InlineKeyboardButton("📩 Управление", callback_data="menu_admin"))
    return markup

def select_operator_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    operators = [
        "🔴 МТС-20$", "⚫️ Теле2-20$", "🟡 Билайн-20$",
        "🟢 Сбер-19$", "🟣 Миранда-21.5$", "🟠 Добросвязь-20$",
        "🔵 Тбанк-20$", "🟤 Газпром-20$", "🔷 Альфа-39$"
    ]
    for op in operators:
        markup.add(InlineKeyboardButton(op, callback_data=f"op_select_{op}"))
    markup.add(InlineKeyboardButton("🔙 Вернуться в Меню", callback_data="menu_back_main"))
    return markup

def admin_inline_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("📩 Все Заявки", callback_data="admin_all_orders"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📥 Скачать Базу", callback_data="admin_export"),
        InlineKeyboardButton("📝 Очередь", callback_data="admin_queue"),
        InlineKeyboardButton("⏳ В работе", callback_data="admin_work"),
        InlineKeyboardButton("✅ Отстояло", callback_data="admin_checked"),
        InlineKeyboardButton("💰 Выплатить Всем", callback_data="admin_pay_all"),
        InlineKeyboardButton("❌ Блок", callback_data="admin_blocked"),
        InlineKeyboardButton("⚠️ Не скан", callback_data="admin_noscan"),
        InlineKeyboardButton("💸 Заявки На Вывод", callback_data="admin_withdraws"),
        InlineKeyboardButton("🔙 Закрыть", callback_data="menu_back_main")
    )
    return markup

def stats_period_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📅 За Сегодня", callback_data="stats_today"),
        InlineKeyboardButton("📆 За Месяц", callback_data="stats_month"),
        InlineKeyboardButton("🌍 За Всё Время", callback_data="stats_all"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main")
    )
    return markup

def safe_edit_or_send(call, text, reply_markup=None):
    try:
        if call.message.photo or call.message.document or call.message.video:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text, reply_markup=reply_markup)
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=reply_markup
            )
    except Exception as e:
        bot.send_message(call.message.chat.id, text, reply_markup=reply_markup)

# ============================================================
# КОМАНДЫ СТАРТА
# ============================================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    username = message.from_user.username or "Клиент"

    create_user_profile(user_id, username)
    user_states[user_id] = None
    
    if not check_subscription(user_id):
        text = (
            f"👋 Приветствуем в {SERVICE_NAME}, @{username}!\n\n"
            f"⛔ Для доступа к функциям бота необходимо быть подписанным на наш канал.\n\n"
            f"1. Перейдите в канал.\n"
            f"2. Нажмите «Проверить Подписку»."
        )
        bot.send_message(message.chat.id, text, reply_markup=sub_menu())
        return

    if not user_stats[user_id].get("agreed_rules", False):
        rules_text = (
            f"👋 Приветствуем в {SERVICE_NAME}!\n\n"
            f"Перед началом работы ознакомьтесь с правилами."
        )
        bot.send_message(message.chat.id, rules_text, reply_markup=rules_menu())
        return

    welcome_text = (
        f"👋 С возвращением, @{username}!\n\n"
        f"📱 Ваш надежный сервис по сдаче eSIM."
    )
    send_photo_or_text(message.chat.id, "logo.jpg", welcome_text, main_inline_menu(user_id))

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = str(message.chat.id)
    if is_admin(user_id):
        bot.send_message(user_id, f"🔐 Панель управления {SERVICE_NAME}", reply_markup=admin_inline_menu(user_id))
    else:
        bot.send_message(user_id, "❌ Доступ закрыт.")

# ============================================================
# РАССЫЛКА
# ============================================================
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'animation'], func=lambda m: user_states.get(str(m.chat.id)) == "waiting_broadcast")
def handle_broadcast(message):
    user_id = str(message.chat.id)
    user_states[user_id] = None
    success = 0
    fail = 0
    msg = bot.send_message(user_id, "⏳ Отправка...")
    for uid in user_stats.keys():
        try:
            if message.content_type == 'text':
                bot.send_message(uid, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(uid, message.video.file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(uid, message.document.file_id, caption=message.caption)
            elif message.content_type == 'animation':
                bot.send_animation(uid, message.animation.file_id, caption=message.caption)
            success += 1
            time.sleep(0.05)
        except:
            fail += 1
    bot.edit_message_text(
        f"✅ Отправлено: {success}\n❌ Ошибок: {fail}",
        chat_id=user_id,
        message_id=msg.message_id,
        reply_markup=admin_inline_menu(user_id)
    )

# ============================================================
# ОБРАБОТКА ФОТО
# ============================================================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = str(message.chat.id)
    username = message.from_user.username or "Клиент"

    if user_states.get(user_id) == "waiting_broadcast" and is_admin(user_id):
        handle_broadcast(message)
        return

    if user_states.get(user_id) != "waiting_esim_photo":
        bot.send_message(user_id, "❌ Сначала выберите оператора.", reply_markup=main_inline_menu(user_id))
        return

    phone_text = message.caption or ""
    digits_only = re.sub(r'\D', '', phone_text) 

    if len(digits_only) not in [10, 11]:
        bot.send_message(
            user_id, 
            "⚠️ Номер не распознан!\n"
            "Пришлите фото заново с подписью.\n"
            "Пример: +79123456789"
        )
        return

    if len(digits_only) == 10:
        cleaned = f"+7{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('7'):
        cleaned = f"+{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('8'):
        cleaned = f"+7{digits_only[1:]}"
    elif len(digits_only) == 11 and digits_only.startswith('9'):
        cleaned = f"+7{digits_only[1:]}"
    else:
        bot.send_message(user_id, "⚠️ Ошибка в номере телефона.")
        return

    try:
        photo = message.photo[-1]
        if photo.width < 200 or photo.height < 200:
            bot.send_message(user_id, "⚠️ Фото слишком размытое/маленькое.")
            return
            
        file_id = photo.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{timestamp}.jpg"
        filepath = os.path.join(IMAGES_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(downloaded_file)

        operator = user_states.get(user_id + "_current_operator")
        stats = user_stats[user_id]

        if "queue" not in stats: stats["queue"] = 0

        stats["esims"].append({
            "data": cleaned,
            "operator": operator,
            "time": datetime.now().isoformat(),
            "paid": False,
            "status": "queue",
            "photo_path": filepath,
            "photo_file_id": file_id
        })
        stats["loaded"] += 1
        stats["queue"] += 1
        save_data(user_stats)

        session_count = user_states.get(user_id + "_session_count", 0) + 1
        user_states[user_id + "_session_count"] = session_count

        for admin_id in ADMIN_IDS:
            try:
                with open(filepath, 'rb') as f:
                    markup = InlineKeyboardMarkup(row_width=2)
                    markup.add(
                        InlineKeyboardButton("📝 Очередь", callback_data=f"status_queue_{user_id}_{cleaned}"),
                        InlineKeyboardButton("⏳ В работе", callback_data=f"status_work_{user_id}_{cleaned}")
                    )
                    bot.send_photo(
                        admin_id,
                        f,
                        caption=(
                            f"📱 Новый куар-код\n"
                            f"👤 Клиент: @{username}\n"
                            f"📞 Номер: {cleaned}\n"
                            f"📡 Оператор: {operator}"
                        ),
                        reply_markup=markup
                    )
            except Exception as e:
                logger.error(f"Ошибка отправки админу {admin_id}: {e}")

        finish_markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Завершить", callback_data="finish_sending")
        )

        bot.send_message(
            user_id,
            f"✅ Куар-код {cleaned} загружен!\n"
            f"📊 Отправлено в этой сессии: {session_count}.\n\n"
            f"Можете отправить следующий или нажать «Завершить».",
            reply_markup=finish_markup
        )

    except Exception as e:
        logger.error(f"Ошибка у {user_id}: {e}")
        bot.send_message(user_id, "❌ Системная ошибка, попробуйте снова.", reply_markup=main_inline_menu(user_id))

# ============================================================
# CALLBACK-КНОПКИ
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = str(call.from_user.id)
    username = call.from_user.username or "Клиент"
    data = call.data

    if data.startswith("menu_") or data.startswith("op_select") or data.startswith("change_wallet") or data.startswith("finish") or data.startswith("stats_"):
        bot.answer_callback_query(call.id)

    if data == "agree_rules":
        user_stats[user_id]["agreed_rules"] = True
        save_data(user_stats)
        bot.answer_callback_query(call.id, "✅ Принято!")
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        welcome_text = f"👋 Добро пожаловать в {SERVICE_NAME}, @{username}!"
        send_photo_or_text(call.message.chat.id, "logo.jpg", welcome_text, main_inline_menu(user_id))
        return

    if data == "check_sub":
        if check_subscription(user_id):
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            if not user_stats[user_id].get("agreed_rules", False):
                bot.send_message(call.message.chat.id, "Ознакомьтесь с правилами:", reply_markup=rules_menu())
                return
            welcome_text = f"👋 С возвращением, @{username}!"
            send_photo_or_text(call.message.chat.id, "logo.jpg", welcome_text, main_inline_menu(user_id))
        else:
            bot.answer_callback_query(call.id, "❌ Вы не подписаны на канал!", show_alert=True)
        return

    if data == "menu_back_main":
        user_states[user_id] = None
        user_states[user_id + "_session_count"] = 0 
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        welcome_text = f"👋 Главное меню {SERVICE_NAME}, @{username}" 
        send_photo_or_text(call.message.chat.id, "logo.jpg", welcome_text, main_inline_menu(user_id))
        return

    if data == "menu_sdat":
        user_states[user_id] = "waiting_esim_operator"
        user_states[user_id + "_session_count"] = 0 
        text = "📱 Выберите оператора из списка:"
        markup = select_operator_menu(user_id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_photo_or_text(call.message.chat.id, "logo_sdat.jpg", text, markup)
        return
        
    if data.startswith("op_select_"):
        operator = data.replace("op_select_", "")
        user_states[user_id + "_current_operator"] = operator
        user_states[user_id] = "waiting_esim_photo"
        text = (
            f"✅ Оператор: {operator}\n\n"
            f"📸 Отправьте фото куар-кода с номером в подписи.\n"
            f"Пример: +79123456789\n\n"
            f"Можно отправлять несколько фото подряд."
        )
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Завершить", callback_data="finish_sending"))
        safe_edit_or_send(call, text, markup)
        return
        
    if data == "finish_sending":
        user_states[user_id] = None
        session_total = user_states.get(user_id + "_session_count", 0)
        text = f"✅ Приём завершен. Вы отправили {session_total} шт."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 В Меню", callback_data="menu_back_main"))
        safe_edit_or_send(call, text, markup)
        return

    if data == "menu_moi":
        stats = user_stats.get(user_id, {})
        esims = stats.get("esims", [])
        today = datetime.now().date().isoformat()
        today_esims = [e for e in esims if e.get("time", "").split("T")[0] == today]

        if not today_esims:
            text = "📭 За сегодня заявок нет."
        else:
            expected_payout = sum(get_operator_price(e.get("operator", "")) for e in today_esims if e.get("status") == "checked")
            text = f"📋 Ваши заявки за сегодня:\n"
            text += f"📱 Всего: {len(today_esims)}.\n"
            text += f"💰 К оплате: {expected_payout:.2f} USDT\n\n"
            for i, esim in enumerate(reversed(today_esims), 1):
                status_str = {"queue": "⏳ Очередь", "work": "⏳ В работе", "checked": "✅ Отстояло", "blocked": "❌ Блок", "no_scan": "⚠️ Не скан"}.get(esim.get("status", ""), "❓ Неизвестно")
                if esim.get("status") == "checked":
                    status_str = "💰 Оплачено" if esim.get("paid", False) else "✅ Отстояло"
                text += f"{i}. {esim.get('operator', '')} | {esim.get('data', '')} - {status_str}\n"
        
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main"))
        safe_edit_or_send(call, text, markup)
        return

    if data == "menu_lk":
        stats = user_stats.get(user_id, {})
        today = datetime.now().date().isoformat()
        today_count = len([e for e in stats.get("esims", []) if e.get("time", "").split("T")[0] == today])

        text = (
            f"👤 Профиль: @{stats.get('username', username)}\n"
            f"🏦 Сервис: {SERVICE_NAME}\n"
            f"📱 За сегодня: {today_count}\n\n"
            f"📊 Общая Статистика:\n"
            f"Всего сдано: {len(stats.get('esims', []))}\n"
            f"В очереди: {stats.get('queue', 0)}\n"
            f"В работе: {stats.get('in_work', 0)}\n"
            f"Отстояло: {stats.get('checked', 0)}\n"
            f"Блок: {stats.get('blocked', 0)}\n"
            f"Не скан: {stats.get('no_scan', 0)}\n\n"
            f"💰 Баланс: {stats.get('balance', 0.0):.2f} USDT"
        )
        history = stats.get('balance_history', [])[-5:]
        if history:
            text += "\n\n📜 Последние операции:\n"
            for item in history:
                if item.get('type') == 'earned': text += f"✅ +{item['amount']:.2f} USDT\n"
                elif item.get('type') == 'withdraw': text += f"💸 -{item['amount']:.2f} USDT ({'✅' if item.get('status') == 'approved' else '❌'})\n"

        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main"))
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_photo_or_text(call.message.chat.id, "logo_lk.jpg", text, markup)
        return

    if data == "menu_stats":
        text = "📊 Выберите период:"
        safe_edit_or_send(call, text, stats_period_menu())
        return

    if data.startswith("stats_"):
        stats = user_stats.get(user_id, {})
        esims = stats.get("esims", [])
        now = datetime.now()
        filtered_esims = []
        title = ""

        if data == "stats_today":
            title = "📅 Аналитика за сегодня"
            filtered_esims = [e for e in esims if e.get("time", "").split("T")[0] == now.date().isoformat()]
        elif data == "stats_month":
            title = "📆 Аналитика за месяц"
            filtered_esims = [e for e in esims if e.get("time", "").split("T")[0] >= now.replace(day=1).date().isoformat()]
        elif data == "stats_all":
            title = "🌍 Аналитика за всё время"
            filtered_esims = esims

        total_sdano = len(filtered_esims)
        checked_count = sum(1 for e in filtered_esims if e.get("status") == "checked")
        queue_count = sum(1 for e in filtered_esims if e.get("status") == "queue")
        work_count = sum(1 for e in filtered_esims if e.get("status") == "work")
        blocked_count = sum(1 for e in filtered_esims if e.get("status") == "blocked")
        noscan_count = sum(1 for e in filtered_esims if e.get("status") == "no_scan")
        earned = sum(get_operator_price(e.get("operator", "")) for e in filtered_esims if e.get("status") == "checked")
        
        withdrawn = 0.0
        for h in stats.get("balance_history", []):
            h_date = h.get("time", "").split("T")[0]
            if data == "stats_today" and h_date != now.date().isoformat(): continue
            if data == "stats_month" and h_date < now.replace(day=1).date().isoformat(): continue
            if h.get("type") == "withdraw" and h.get("status") == "approved":
                withdrawn += h.get("amount", 0.0)

        text = (
            f"{title}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📱 Всего: {total_sdano} шт.\n"
            f"✅ Отстояло: {checked_count} шт.\n"
            f"⏳ В очереди: {queue_count} шт.\n"
            f"⚙️ В работе: {work_count} шт.\n"
            f"❌ Блок: {blocked_count} шт.\n"
            f"⚠️ Не скан: {noscan_count} шт.\n\n"
            f"💰 Заработано: {earned:.2f} USDT\n"
            f"💸 Выведено: {withdrawn:.2f} USDT\n\n"
            f"Баланс: {stats.get('balance', 0.0):.2f} USDT"
        )
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_stats"))
        safe_edit_or_send(call, text, markup)
        return

    if data == "change_wallet":
        user_states[user_id] = "waiting_wallet_link"
        text = f"💳 Введите новый кошелек TRC20:"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отмена", callback_data="menu_back_main"))
        safe_edit_or_send(call, text, markup)
        return

    if data == "menu_vyvod":
        stats = user_stats.get(user_id, {})
        balance = stats.get('balance', 0.0)
        wallet_link = stats.get('wallet_link')
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass

        if balance <= 0:
            text = f"❌ Недостаточно средств на балансе."
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main"))
            send_photo_or_text(call.message.chat.id, "logo_vivod.jpg", text, markup)
            return
            
        if stats.get('pending_withdraw'):
            text = "⏳ У вас уже есть заявка на вывод."
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main"))
            send_photo_or_text(call.message.chat.id, "logo_vivod.jpg", text, markup)
            return

        if not wallet_link:
            user_states[user_id] = "waiting_wallet_link"
            text = f"💳 Укажите ваш кошелек TRC20 для вывода:"
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main"))
            send_photo_or_text(call.message.chat.id, "logo_vivod.jpg", text, markup)
            return

        user_states[user_id] = "waiting_withdraw_amount"
        text = f"💸 Введите сумму для вывода (от 10 USDT):"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔄 Сменить Кошелек", callback_data="change_wallet"), InlineKeyboardButton("🔙 Назад", callback_data="menu_back_main"))
        send_photo_or_text(call.message.chat.id, "logo_vivod.jpg", text, markup)
        return

    # --- АДМИН ПАНЕЛЬ ---
    if data == "menu_admin" and is_admin(user_id):
        safe_edit_or_send(call, f"🔐 Панель управления {SERVICE_NAME}", admin_inline_menu(user_id))
        return

    if data == "admin_broadcast" and is_admin(user_id):
        user_states[user_id] = "waiting_broadcast"
        text = f"📢 **Рассылка**\n\nОтправьте сообщение/фото/видео для всех."
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отмена", callback_data="menu_admin"))
        safe_edit_or_send(call, text, markup)
        return

    if data == "admin_pay_all" and is_admin(user_id):
        total_paid = 0.0
        users_paid = 0
        for uid, u_data in user_stats.items():
            user_earned = 0.0
            has_unpaid = False
            for esim in u_data.get("esims", []):
                if esim.get("status") == "checked" and not esim.get("paid", False):
                    user_earned += get_operator_price(esim.get("operator", ""))
                    esim["paid"] = True
                    has_unpaid = True
            
            if has_unpaid and user_earned > 0:
                u_data["balance"] += user_earned
                u_data.setdefault("balance_history", []).append({"type": "earned", "amount": user_earned, "time": datetime.now().isoformat()})
                total_paid += user_earned
                users_paid += 1
                try: bot.send_message(uid, f"💰 Начислено: +{user_earned:.2f} USDT", reply_markup=main_inline_menu(uid))
                except: pass
        save_data(user_stats)
        if total_paid > 0:
            bot.answer_callback_query(call.id, f"✅ Выплачено {total_paid:.2f} USDT ({users_paid} чел.)", show_alert=True)
            safe_edit_or_send(call, f"✅ Выплачено {total_paid:.2f} USDT.", admin_inline_menu(user_id))
        else:
            bot.answer_callback_query(call.id, "📭 Нет неоплаченных заявок", show_alert=True)
        return

    if data == "admin_all_orders" and is_admin(user_id):
        total = sum(len(d.get("esims", [])) for d in user_stats.values())
        queue_count = sum(d.get("queue", 0) for d in user_stats.values())
        work_count = sum(d.get("in_work", 0) for d in user_stats.values())
        today = datetime.now().date().isoformat()
        today_orders = sum(1 for d in user_stats.values() for esim in d.get("esims", []) if esim.get("time", "").split("T")[0] == today)
        text = f"📩 Заявки:\nВсего: {total}\nОжидание: {queue_count}\nОбработка: {work_count}\nСегодня: {today_orders}"
        safe_edit_or_send(call, text, admin_inline_menu(user_id))
        return

    if data == "admin_stats" and is_admin(user_id):
        total_users = len(user_stats)
        total_esims = sum(len(d.get("esims", [])) for d in user_stats.values())
        total_queue = sum(d.get("queue", 0) for d in user_stats.values())
        total_work = sum(d.get("in_work", 0) for d in user_stats.values())
        total_checked = sum(d.get("checked", 0) for d in user_stats.values())
        total_blocked = sum(d.get("blocked", 0) for d in user_stats.values())
        total_no_scan = sum(d.get("no_scan", 0) for d in user_stats.values())
        text = f"📊 Общая Статистика:\n👥 Юзеров: {total_users}\n📱 eSIM: {total_esims}\n⏳ Очередь: {total_queue}\n⚙️ В работе: {total_work}\n✅ Отстояло: {total_checked}\n❌ Блок: {total_blocked}\n⚠️ Не скан: {total_no_scan}"
        safe_edit_or_send(call, text, admin_inline_menu(user_id))
        return

    if data == "admin_withdraws" and is_admin(user_id):
        pending = []
        for uid, u_data in user_stats.items():
            wd = u_data.get('pending_withdraw')
            if wd and wd.get('status') == 'pending': pending.append({"uid": uid, "data": u_data, "wd": wd})
        if not pending:
            bot.answer_callback_query(call.id, "📭 Нет заявок", show_alert=True)
            return
        bot.send_message(user_id, f"💸 Заявки на вывод: {len(pending)}")
        for p in pending:
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"withdraw_approve_{p['uid']}"), InlineKeyboardButton("❌ Отклонить", callback_data=f"withdraw_reject_{p['uid']}"))
            bot.send_message(user_id, f"👤 @{p['data'].get('username', 'Unknown')}\n💰 Сумма: {p['wd']['amount']:.2f} USDT\n🔗 Кошелек: {p['wd'].get('wallet_link')}", reply_markup=markup)
        return

    if data in ["admin_queue", "admin_work", "admin_checked", "admin_blocked", "admin_noscan"] and is_admin(user_id):
        status_map = {
            "admin_queue": ("queue", "📝 Очередь"),
            "admin_work": ("work", "⏳ В работе"),
            "admin_checked": ("checked", "✅ Отстояло"),
            "admin_blocked": ("blocked", "❌ Блок"),
            "admin_noscan": ("no_scan", "⚠️ Не скан")
        }
        target_status, title = status_map[data]
        
        esims_list = []
        for uid, u_data in user_stats.items():
            for esim in u_data.get("esims", []):
                if esim.get("status") == target_status:
                    esims_list.append({"user_id": uid, "username": u_data.get("username", "Unknown"), "esim": esim, "time": esim.get("time", "")})
        
        esims_list.sort(key=lambda x: x["time"], reverse=True)
        if not esims_list:
            bot.answer_callback_query(call.id, "📭 Пусто", show_alert=True)
            return
        
        bot.send_message(user_id, f"{title}: {len(esims_list)} eSIM. Показываю последние 20:")
        for item in esims_list[:20]:
            esim = item["esim"]
            uid = item["user_id"]
            number = esim.get("data", "")
            
            markup = None
            if target_status in ["queue", "work"]:
                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(
                    InlineKeyboardButton("⏳ В работе", callback_data=f"status_work_{uid}_{number}"),
                    InlineKeyboardButton("✅ Отстояло", callback_data=f"status_checked_{uid}_{number}"),
                    InlineKeyboardButton("❌ Блок", callback_data=f"status_blocked_{uid}_{number}"),
                    InlineKeyboardButton("⚠️ Не скан", callback_data=f"status_noscan_{uid}_{number}")
                )
            
            caption = f"📱 @{item['username']}\n🆔 {uid}\n📞 {number}\n📡 {esim.get('operator', '')}\n💰 {get_operator_price(esim.get('operator', '')):.2f} USDT\n🕒 {esim.get('time', '')[:16]}"
            
            photo_path = esim.get("photo_path")
            if photo_path and os.path.exists(photo_path):
                try:
                    with open(photo_path, 'rb') as f: bot.send_photo(user_id, f, caption=caption, reply_markup=markup)
                except: bot.send_message(user_id, caption, reply_markup=markup)
            else:
                file_id = esim.get("photo_file_id")
                if file_id:
                    try: bot.send_photo(user_id, file_id, caption=caption, reply_markup=markup)
                    except: bot.send_message(user_id, caption, reply_markup=markup)
                else: bot.send_message(user_id, caption, reply_markup=markup)
        return

    if data == "admin_export" and is_admin(user_id):
        with open("export.txt", "w", encoding="utf-8") as f:
            for uid, u_data in user_stats.items():
                f.write(f"ID: {uid} | @{u_data.get('username', 'Unknown')}\n")
                for esim in u_data.get("esims", []): f.write(f"  {esim.get('operator', '')} | {esim.get('data', '')} | {esim.get('status', '')}\n")
                f.write("\n")
        with open("export.txt", "rb") as f: bot.send_document(user_id, f, caption=f"📥 База данных")
        bot.answer_callback_query(call.id, "✅ Отправлено")
        return
    
    # --- СТАТУСЫ eSIM (АДМИН) ---
    if data.startswith("status_"):
        if not is_admin(call.from_user.id): return
        parts = data.split("_")
        status = parts[1]
        target_user = parts[2]
        number = "_".join(parts[3:])

        if target_user not in user_stats: return
        stats = user_stats[target_user]
        
        if "in_work" not in stats: stats["in_work"] = 0
        if "queue" not in stats: stats["queue"] = 0
        if "checked" not in stats: stats["checked"] = 0
        if "blocked" not in stats: stats["blocked"] = 0
        if "no_scan" not in stats: stats["no_scan"] = 0
        
        found_esim = None

        for esim in stats.get("esims", []):
            if esim.get("data") == number and esim.get("status") != status:
                old_status = esim.get("status")
                esim["status"] = status
                found_esim = esim
                
                if old_status == "queue": stats["queue"] -= 1
                elif old_status == "work": stats["in_work"] -= 1
                elif old_status == "checked": stats["checked"] -= 1
                elif old_status == "blocked": stats["blocked"] -= 1
                elif old_status == "no_scan": stats["no_scan"] -= 1
                    
                if status == "work": stats["in_work"] += 1
                elif status == "checked": stats["checked"] += 1
                elif status == "blocked": stats["blocked"] += 1
                elif status == "no_scan": stats["no_scan"] += 1
                elif status == "queue": stats["queue"] += 1
                break

        if not found_esim:
            bot.answer_callback_query(call.id, "❌ Уже с этим статусом")
            return

        save_data(user_stats)

        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass

        if status == "work":
            notify_text = f"⚙️ Ваша заявка {number} в работе."
            status_label = "⏳ В РАБОТЕ"
        elif status == "queue":
            notify_text = f"⏳ Заявка {number} в очереди."
            status_label = "📝 ОЧЕРЕДЬ"
        elif status == "checked":
            notify_text = f"✅ Заявка {number} отстояла!\n(Ожидайте оплату на баланс)."
            status_label = "✅ ОТСТОЯЛО"
        elif status == "blocked":
            notify_text = f"❌ Заявка {number} заблокирована."
            status_label = "❌ БЛОК"
        else:
            notify_text = f"⚠️ Заявка {number} не скан."
            status_label = "⚠️ НЕ СКАН"

        try: bot.send_message(target_user, notify_text)
        except: pass
        bot.answer_callback_query(call.id, f"Статус: {status_label}")
        return

    # --- ВЫВОД (АДМИН) ---
    if data.startswith("withdraw_"):
        if not is_admin(call.from_user.id): return
        parts = data.split("_")
        action = parts[1]
        target_user = parts[2]
        stats = user_stats.get(target_user, {})
        wd = stats.get("pending_withdraw")

        if not wd or wd.get("status") != "pending":
            bot.answer_callback_query(call.id, "❌ Уже обработано")
            return

        amount = wd["amount"]
        if action == "approve":
            stats["balance"] -= amount
            wd["status"] = "approved"
            back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 В Меню", callback_data="menu_back_main"))
            try: bot.send_message(target_user, f"✅ Вывод одобрен!\n💰 Сумма: {amount:.2f} USDT\n\nОжидайте поступление.", reply_markup=back_markup)
            except: pass
            result_text = "✅ ОДОБРЕН"
        else:
            wd["status"] = "rejected"
            try: bot.send_message(target_user, f"❌ Вывод отклонен.\nСредства остались на балансе.")
            except: pass
            result_text = "❌ ОТКЛОНЕН"

        stats["pending_withdraw"] = None
        save_data(user_stats)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.answer_callback_query(call.id, f"Готово: {result_text}")
        return

# ============================================================
# ОБРАБОТКА ТЕКСТА
# ============================================================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.chat.id)
    text = message.text.strip()
    
    if user_states.get(user_id) == "waiting_broadcast" and is_admin(user_id):
        handle_broadcast(message)
        return

    if user_states.get(user_id) == "waiting_wallet_link":
        if "T" not in text or len(text) < 30:
            bot.send_message(user_id, "⚠️ Неверный кошелек TRC20!\nКошелек должен начинаться с 'T' и иметь длину 34 символа.")
            return
            
        stats = user_stats[user_id]
        stats['wallet_link'] = text
        save_data(user_stats)
        user_states[user_id] = None
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💸 К Выводу", callback_data="menu_vyvod"))
        bot.send_message(user_id, f"✅ Кошелек сохранен!\nТеперь можете выводить средства.", reply_markup=markup)
        return

    if user_states.get(user_id) == "waiting_withdraw_amount":
        try:
            amount = float(text)
            stats = user_stats[user_id]
            if amount < 10:
                bot.send_message(user_id, "❌ Минимум 10 USDT.")
                return
            if amount > stats.get('balance', 0.0):
                bot.send_message(user_id, f"❌ Недостаточно средств. Баланс: {stats.get('balance', 0.0):.2f} USDT")
                return

            stats['pending_withdraw'] = {"amount": amount, "wallet_link": stats.get('wallet_link', 'Не привязан'), "time": datetime.now().isoformat(), "status": "pending"}
            save_data(user_stats)
            user_states[user_id] = None

            back_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 В Меню", callback_data="menu_back_main"))
            bot.send_message(user_id, f"✅ Заявка на вывод {amount:.2f} USDT создана!\n⏳ Ожидайте.", reply_markup=back_markup)

            for admin_id in ADMIN_IDS:
                markup = InlineKeyboardMarkup(row_width=2)
                markup.add(InlineKeyboardButton("✅ Одобрить", callback_data=f"withdraw_approve_{user_id}"), InlineKeyboardButton("❌ Отклонить", callback_data=f"withdraw_reject_{user_id}"))
                bot.send_message(admin_id, f"💸 Вывод: @{stats['username']}\n💰 Сумма: {amount:.2f} USDT\n🔗 Кошелек: {stats.get('wallet_link')}", reply_markup=markup)
            return
        except ValueError:
            bot.send_message(user_id, "❌ Введите число!")
            return

    bot.send_message(user_id, "❓ Неизвестная команда. Используйте меню.", reply_markup=main_inline_menu(user_id))

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    logger.info(f"🚀 {SERVICE_NAME} — УСПЕШНЫЙ ЗАПУСК...")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except Exception as e:
            time.sleep(5)