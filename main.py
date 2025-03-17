import logging
import asyncio
import subprocess
import time
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, List
from dotenv import load_dotenv
from tasks import send_capsule_task
import sys
import pytz
import nest_asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
nest_asyncio.apply()

# Инициализация переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN, ENCRYPTION_KEY]):
    logger.error("Отсутствуют необходимые переменные окружения.")
    sys.exit(1)
ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)
if len(ENCRYPTION_KEY_BYTES) != 32:
    logger.error("Длина ключа шифрования должна быть 32 байта для AES-256")
    sys.exit(1)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
scheduler = AsyncIOScheduler(timezone=pytz.utc)
bot: Optional[Bot] = None

# Состояния беседы
CAPSULE_TITLE, CAPSULE_CONTENT, SCHEDULE_TIME, ADD_RECIPIENT, SELECTING_SEND_DATE, SELECTING_CAPSULE, SELECTING_CAPSULE_FOR_RECIPIENTS, CREATING_CAPSULE = range(8)

# Ограничения контента
MAX_TEXTS = 10
MAX_PHOTOS = 5
MAX_VIDEOS = 5
MAX_AUDIOS = 5
MAX_DOCUMENTS = 5
MAX_STICKERS = 5
MAX_VOICES = 5

# Локализация
LOCALE = 'ru'
TRANSLATIONS = {
    'ru': {
        "start_message": "Добро пожаловать в TimeCapsuleBot! 📬\nЯ помогу вам создавать капсулы времени с текстом, фото, видео и другим контентом, чтобы отправить их себе или друзьям в будущем.\nИспользуйте кнопки ниже, чтобы начать!",
        "help_message": "📋 *Список команд TimeCapsuleBot*\n\n"
                        "/start - Запустить бота и открыть главное меню.\n"
                        "/create_capsule - Создать новую капсулу времени.\n*Пример:* Добавьте текст, фото или видео, укажите получателей и дату отправки.\n"
                        "/add_recipient - Добавить получателей в существующую капсулу.\n*Пример:* @Friend1 @Friend2\n"
                        "/view_capsules - Посмотреть список ваших капсул с их статусом.\n"
                        "/send_capsule - Немедленно отправить капсулу получателям.\n"
                        "/delete_capsule - Удалить капсулу, если она вам больше не нужна.\n"
                        "/edit_capsule - Изменить содержимое капсулы (текст).\n"
                        "/view_recipients - Показать, кто получит вашу капсулу.\n"
                        "/select_send_date - Установить дату отправки капсулы.\n*Пример:* Через неделю или конкретный день.\n"
                        "/support_author - Поддержать разработчика бота.\n"
                        "/change_language - Сменить язык интерфейса.\n\n"
                        "💡 Подсказка: Создайте капсулу и экспериментируйте с медиа!",
        "change_language": "🌍 Сменить язык",
        "select_language": "Выберите ваш язык:",
        "capsule_created": "✅ Капсула #{capsule_id} создана!\nДобавьте в неё текст, фото или видео.",
        "enter_recipients": "👥 Введите Telegram-имена получателей через пробел.\n*Пример:* @Friend1 @Friend2\nОни получат капсулу, когда вы её отправите или наступит заданная дата.",
        "select_capsule": "📦 Введите номер капсулы для действия:",
        "invalid_capsule_id": "❌ Неверный ID капсулы. Проверьте список ваших капсул с помощью 'Просмотреть капсулы'.",
        "recipients_added": "✅ Получатели добавлены в капсулу #{capsule_id}!\nТеперь можно установить дату отправки или отправить её сразу.",
        "error_general": "⚠️ Что-то пошло не так. Попробуйте снова или напишите в поддержку @SupportBot.",
        "service_unavailable": "🛠 Сервис временно недоступен. Пожалуйста, подождите и попробуйте позже.",
        "your_capsules": "📋 *Ваши капсулы времени:*\n",
        "no_capsules": "📭 У вас пока нет капсул. Создайте первую с помощью 'Создать капсулу'!",
        "created_at": "Создано",
        "status": "Статус",
        "scheduled": "⏳ Запланировано",
        "draft": "✏️ Черновик",
        "enter_capsule_id_to_send": "📨 Введите ID капсулы для немедленной отправки (например, #5):",
        "no_recipients": "❌ В этой капсуле нет получателей. Добавьте их с помощью 'Добавить получателя'.",
        "capsule_received": "🎉 Вы получили капсулу времени от @{sender}!\nВот её содержимое:",
        "capsule_sent": "📬 Капсула успешно отправлена @{recipient}!\nОни увидят её прямо сейчас.",
        "recipient_not_registered": "⚠️ Получатель @{recipient} не зарегистрирован в боте и не получит капсулу.",
        "confirm_delete": "🗑 Вы уверены, что хотите удалить капсулу? Это действие нельзя отменить.",
        "capsule_deleted": "✅ Капсула #{capsule_id} удалена.",
        "delete_canceled": "❌ Удаление отменено. Капсула осталась на месте.",
        "enter_new_content": "✏️ Введите новый текст для капсулы (старый будет заменён):",
        "capsule_edited": "✅ Капсула #{capsule_id} обновлена с новым содержимым!",
        "recipients_list": "👥 Получатели капсулы #{capsule_id}:\n{recipients}",
        "no_recipients_for_capsule": "📭 В капсуле #{capsule_id} пока нет получателей.",
        "choose_send_date": "📅 Когда отправить капсулу?\nВыберите один из вариантов:",
        "through_week": "Через неделю",
        "through_month": "Через месяц",
        "select_date": "Выбрать дату",
        "date_selected": "📅 Вы выбрали дату: {date}\nКапсула будет отправлена в указанное время.",
        "date_set": "✅ Дата отправки капсулы установлена на {date}. Ожидайте!",
        "support_author": "💖 Поддержите автора бота:\n{url}\nСпасибо за помощь в развитии проекта!",
        "create_capsule_first": "📦 Сначала создайте капсулу с помощью 'Создать капсулу', чтобы добавить в неё контент.",
        "text_added": "✅ Текстовое сообщение добавлено в капсулу!",
        "photo_added": "✅ Фото добавлено в капсулу!",
        "video_added": "✅ Видео добавлено в капсулу!",
        "audio_added": "✅ Аудио добавлено в капсулу!",
        "document_added": "✅ Документ добавлен в капсулу!",
        "sticker_added": "✅ Стикер добавлен в капсулу!",
        "voice_added": "✅ Голосовое сообщение добавлено в капсулу!",
        "not_registered": "⚠️ Вы не зарегистрированы в боте. Нажмите /start, чтобы начать.",
        "not_your_capsule": "❌ Эта капсула вам не принадлежит. Вы можете работать только со своими капсулами.",
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "content_limit_exceeded": "⚠️ Превышен лимит: вы добавили слишком много {type}.",
    },
    'en': {
        "start_message": "Welcome to TimeCapsuleBot! 📬\nI’ll help you create time capsules with text, photos, videos, and more to send to yourself or friends in the future.\nUse the buttons below to get started!",
        "help_message": "📋 *TimeCapsuleBot Command List*\n\n"
                        "/start - Launch the bot and open the main menu.\n"
                        "/create_capsule - Create a new time capsule.\n*Example:* Add text, photos, or videos, set recipients and a send date.\n"
                        "/add_recipient - Add recipients to an existing capsule.\n*Example:* @Friend1 @Friend2\n"
                        "/view_capsules - View a list of your capsules with their status.\n"
                        "/send_capsule - Send a capsule to recipients immediately.\n"
                        "/delete_capsule - Delete a capsule if you no longer need it.\n"
                        "/edit_capsule - Edit the capsule’s content (text).\n"
                        "/view_recipients - See who will receive your capsule.\n"
                        "/select_send_date - Set a send date for the capsule.\n*Example:* In a week or a specific day.\n"
                        "/support_author - Support the bot’s developer.\n"
                        "/change_language - Change the interface language.\n\n"
                        "💡 Tip: Create a capsule and experiment with media!",
        "change_language": "🌍 Change Language",
        "select_language": "Select your language:",
        "capsule_created": "✅ Capsule #{capsule_id} created!\nAdd text, photos, or videos to it.",
        "enter_recipients": "👥 Enter Telegram usernames of recipients separated by spaces.\n*Example:* @Friend1 @Friend2\nThey’ll receive the capsule when you send it or the scheduled date arrives.",
        "select_capsule": "📦 Enter the capsule number for the action:",
        "invalid_capsule_id": "❌ Invalid capsule ID. Check your capsule list with 'View Capsules'.",
        "recipients_added": "✅ Recipients added to capsule #{capsule_id}!\nNow you can set a send date or send it immediately.",
        "error_general": "⚠️ Something went wrong. Try again or contact support @SupportBot.",
        "service_unavailable": "🛠 Service temporarily unavailable. Please wait and try again later.",
        "your_capsules": "📋 *Your Time Capsules:*\n",
        "no_capsules": "📭 You don’t have any capsules yet. Create your first one with 'Create Capsule'!",
        "created_at": "Created",
        "status": "Status",
        "scheduled": "⏳ Scheduled",
        "draft": "✏️ Draft",
        "enter_capsule_id_to_send": "📨 Enter the capsule ID to send immediately (e.g., #5):",
        "no_recipients": "❌ This capsule has no recipients. Add them with 'Add Recipient'.",
        "capsule_received": "🎉 You’ve received a time capsule from @{sender}!\nHere’s its content:",
        "capsule_sent": "📬 Capsule successfully sent to @{recipient}!\nThey’ll see it now.",
        "recipient_not_registered": "⚠️ Recipient @{recipient} isn’t registered with the bot and won’t receive the capsule.",
        "confirm_delete": "🗑 Are you sure you want to delete this capsule? This action cannot be undone.",
        "capsule_deleted": "✅ Capsule #{capsule_id} deleted.",
        "delete_canceled": "❌ Deletion canceled. The capsule remains intact.",
        "enter_new_content": "✏️ Enter new text for the capsule (old content will be replaced):",
        "capsule_edited": "✅ Capsule #{capsule_id} updated with new content!",
        "recipients_list": "👥 Recipients of capsule #{capsule_id}:\n{recipients}",
        "no_recipients_for_capsule": "📭 No recipients found for capsule #{capsule_id}.",
        "choose_send_date": "📅 When should the capsule be sent?\nChoose an option:",
        "through_week": "In a week",
        "through_month": "In a month",
        "select_date": "Select a date",
        "date_selected": "📅 You’ve selected: {date}\nThe capsule will be sent at this time.",
        "date_set": "✅ Capsule send date set to {date}. Stay tuned!",
        "support_author": "💖 Support the bot’s author:\n{url}\nThanks for helping the project grow!",
        "create_capsule_first": "📦 First, create a capsule with 'Create Capsule' to add content.",
        "text_added": "✅ Text message added to the capsule!",
        "photo_added": "✅ Photo added to the capsule!",
        "video_added": "✅ Video added to the capsule!",
        "audio_added": "✅ Audio added to the capsule!",
        "document_added": "✅ Document added to the capsule!",
        "sticker_added": "✅ Sticker added to the capsule!",
        "voice_added": "✅ Voice message added to the capsule!",
        "not_registered": "⚠️ You’re not registered with the bot. Press /start to begin.",
        "not_your_capsule": "❌ This capsule doesn’t belong to you. You can only manage your own capsules.",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "content_limit_exceeded": "⚠️ Limit exceeded: you’ve added too many {type}.",
    }
}

def t(key: str, **kwargs) -> str:
    translation = TRANSLATIONS.get(LOCALE, TRANSLATIONS['en']).get(key, key)
    return translation.format(**kwargs) if kwargs else translation

# Функции запуска сервисов
def start_process(command, name):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"{name} запущен с PID: {process.pid}")
        time.sleep(2)
        if process.poll() is None:
            logger.info(f"{name} успешно запущен.")
            return True
        else:
            error = process.stderr.read().decode()
            logger.error(f"Ошибка запуска {name}: {error}")
            return False
    except Exception as e:
        logger.error(f"Не удалось запустить {name}: {e}")
        return False

def start_services():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.error("Переменная REDIS_URL не задана.")
        sys.exit(1)
    celery_command = "celery -A celery_config.app worker --loglevel=info --pool=solo"
    if not start_process(celery_command, "Celery"):
        logger.error("Не удалось запустить Celery.")
        sys.exit(1)

# Шифрование и дешифрование
def encrypt_data_aes(data: str, key: bytes) -> str:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return (iv + encrypted).hex()

def decrypt_data_aes(encrypted_hex: str, key: bytes) -> str:
    data = bytes.fromhex(encrypted_hex)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()
    return unpadded.decode('utf-8')

# Работа с Supabase
def fetch_data(table: str, query: dict = {}) -> list:
    try:
        response = supabase.table(table).select("*")
        for key, value in query.items():
            response = response.eq(key, value)
        return response.execute().data
    except Exception as e:
        logger.error(f"Ошибка Supabase: {e}")
        return []

def post_data(table: str, data: dict) -> list:
    try:
        return supabase.table(table).insert(data).execute().data
    except Exception as e:
        logger.error(f"Ошибка записи в Supabase: {e}")
        return []

def update_data(table: str, query: dict, data: dict) -> list:
    try:
        query_builder = supabase.table(table).update(data)
        for key, value in query.items():
            query_builder = query_builder.eq(key, value)
        return query_builder.execute().data
    except Exception as e:
        logger.error(f"Ошибка обновления в Supabase: {e}")
        return []

def delete_data(table: str, query: dict) -> list:
    try:
        return supabase.table(table).delete().eq(next(iter(query)), query[next(iter(query))]).execute().data
    except Exception as e:
        logger.error(f"Ошибка удаления в Supabase: {e}")
        return []

def get_chat_id(username: str) -> Optional[int]:
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

def add_user(username: str, telegram_id: int, chat_id: int):
    if not fetch_data("users", {"telegram_id": telegram_id}):
        post_data("users", {"telegram_id": telegram_id, "username": username, "chat_id": chat_id})

def generate_unique_capsule_number(creator_id: int) -> int:
    return len(fetch_data("capsules", {"creator_id": creator_id})) + 1

def create_capsule(creator_id: int, title: str, content: str, user_capsule_number: int, scheduled_at: Optional[datetime] = None) -> int:
    encrypted_content = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    data = {"creator_id": creator_id, "title": title, "content": encrypted_content, "user_capsule_number": user_capsule_number}
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    response = post_data("capsules", data)
    return response[0]['id'] if response else -1

def add_recipient(capsule_id: int, recipient_username: str):
    post_data("recipients", {"capsule_id": capsule_id, "recipient_username": recipient_username})

def delete_capsule(capsule_id: int):
    delete_data("recipients", {"capsule_id": capsule_id})
    delete_data("capsules", {"id": capsule_id})

def edit_capsule(capsule_id: int, title: Optional[str] = None, content: Optional[str] = None, scheduled_at: Optional[datetime] = None):
    data = {}
    if title:
        data["title"] = title
    if content:
        data["content"] = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    if data:
        update_data("capsules", {"id": capsule_id}, data)

def get_user_capsules(telegram_id: int) -> list:
    user = fetch_data("users", {"telegram_id": telegram_id})
    return fetch_data("capsules", {"creator_id": user[0]['id']}) if user else []

def get_capsule_recipients(capsule_id: int) -> list:
    return fetch_data("recipients", {"capsule_id": capsule_id})

# Обработчики команд
async def start(update: Update, context: CallbackContext):
    """Обработчик команды /start. Отправляет приветственное сообщение и клавиатуру с доступными командами."""
    user = update.message.from_user
    add_user(user.username or str(user.id), user.id, update.message.chat_id)
    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(t('start_message'), reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help. Отправляет сообщение с доступными командами и их описанием."""
    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(t('help_message'), reply_markup=reply_markup)

async def create_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /create_capsule. Создает новую капсулу и сохраняет ее в базе данных."""
    try:
        user = update.message.from_user
        existing_user = fetch_data("users", {"telegram_id": user.id})
        if not existing_user:
            response = post_data("users", {"telegram_id": user.id, "username": user.username or str(user.id), "chat_id": update.message.chat_id})
            creator_id = response[0]['id']
        else:
            creator_id = existing_user[0]['id']
        initial_content = json.dumps({"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []}, ensure_ascii=False)
        user_capsule_number = generate_unique_capsule_number(creator_id)
        capsule_id = create_capsule(creator_id, "Без названия", initial_content, user_capsule_number)
        if capsule_id == -1:
            await update.message.reply_text(t('service_unavailable'))
            return
        context.user_data['current_capsule'] = capsule_id
        context.user_data['capsule_content'] = json.loads(initial_content)
        context.user_data['state'] = CREATING_CAPSULE
        await update.message.reply_text(t('capsule_created', capsule_id=capsule_id))
    except Exception as e:
        logger.error(f"Ошибка при создании капсулы: {e}")
        await update.message.reply_text(t('error_general'))

async def show_capsule_selection(update: Update, context: CallbackContext, action: str):
    """Запрашивает номер капсулы для выполнения действия."""
    await update.message.reply_text(t('select_capsule'))
    context.user_data['action'] = action
    return True

async def add_recipient_command(update: Update, context: CallbackContext):
    """Обработчик команды /add_recipient. Запрашивает номер капсулы для добавления получателей."""
    if await show_capsule_selection(update, context, "add_recipient"):
        context.user_data['state'] = SELECTING_CAPSULE_FOR_RECIPIENTS

async def view_capsules_command(update: Update, context: CallbackContext):
    """Обработчик команды /view_capsules. Показывает список капсул пользователя."""
    try:
        capsules = get_user_capsules(update.message.from_user.id)
        if capsules:
            response = [f"📦 #{c['id']} {c['title']}\n🕒 {t('created_at')}: {datetime.fromisoformat(c['created_at']).strftime('%d.%m.%Y %H:%M')}\n🔒 {t('status')}: {t('scheduled') if c['scheduled_at'] else t('draft')}" for c in capsules]
            await update.message.reply_text(t('your_capsules') + "\n" + "\n".join(response), parse_mode="Markdown")
        else:
            await update.message.reply_text(t('no_capsules'))
    except Exception as e:
        logger.error(f"Ошибка при получении капсул: {e}")
        await update.message.reply_text(t('error_general'))

async def send_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /send_capsule. Запрашивает номер капсулы для отправки."""
    if await show_capsule_selection(update, context, "send_capsule"):
        context.user_data['state'] = "sending_capsule"

async def delete_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /delete_capsule. Запрашивает номер капсулы для удаления."""
    if await show_capsule_selection(update, context, "delete_capsule"):
        context.user_data['state'] = "deleting_capsule"

async def edit_capsule_command(update: Update, context: CallbackContext):
    """Обработчик команды /edit_capsule. Запрашивает номер капсулы для редактирования."""
    if await show_capsule_selection(update, context, "edit_capsule"):
        context.user_data['state'] = "editing_capsule"

async def view_recipients_command(update: Update, context: CallbackContext):
    """Обработчик команды /view_recipients. Запрашивает номер капсулы для просмотра получателей."""
    if await show_capsule_selection(update, context, "view_recipients"):
        context.user_data['state'] = "viewing_recipients"

async def select_send_date(update: Update, context: CallbackContext):
    """Обработчик команды /select_send_date. Запрашивает номер капсулы для установки даты отправки."""
    if await show_capsule_selection(update, context, "select_send_date"):
        context.user_data['state'] = SELECTING_CAPSULE

async def support_author(update: Update, context: CallbackContext):
    """Обработчик команды /support_author. Отправляет сообщение с ссылкой для поддержки автора."""
    DONATION_URL = "https://www.donationalerts.com/r/lunarisqqq"
    await update.message.reply_text(t('support_author', url=DONATION_URL))

async def change_language(update: Update, context: CallbackContext):
    """Обработчик команды /change_language. Показывает кнопки для выбора языка."""
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="ru")],
        [InlineKeyboardButton("English", callback_data="en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t('select_language'), reply_markup=reply_markup)

# Обработчики callback-запросов
async def handle_language_selection(update: Update, context: CallbackContext):
    """Обработчик выбора языка. Обновляет язык интерфейса и отправляет подтверждение."""
    global LOCALE
    query = update.callback_query
    lang = query.data
    LOCALE = lang
    new_lang = "Русский" if lang == 'ru' else "English"
    await query.edit_message_text(f"Язык изменен на {new_lang}.")
    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=t('start_message'), reply_markup=reply_markup)

async def handle_capsule_selection(update: Update, context: CallbackContext):
    """Обработчик выбора капсулы. Выполняет действия в зависимости от выбранного действия."""
    text = update.message.text.strip()
    try:
        capsule_id = int(text.replace('#', ''))
        context.user_data['selected_capsule_id'] = capsule_id
    except ValueError:
        await update.message.reply_text(t('invalid_capsule_id'))
        return
    action = context.user_data.get('action')
    if not await check_capsule_ownership(update, capsule_id):
        return
    if action == "add_recipient":
        await update.message.reply_text(t('enter_recipients'))
        context.user_data['state'] = "adding_recipient"
    elif action == "send_capsule":
        await handle_send_capsule_logic(update, context, capsule_id)
    elif action == "delete_capsule":
        await update.message.reply_text(t('confirm_delete'), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Да", callback_data="confirm_delete"), InlineKeyboardButton("Нет", callback_data="cancel_delete")]]))
    elif action == "edit_capsule":
        await update.message.reply_text(t('enter_new_content'))
        context.user_data['state'] = "editing_capsule_content"
    elif action == "view_recipients":
        await handle_view_recipients_logic(update, context, capsule_id)
    elif action == "select_send_date":
        keyboard = [
            [InlineKeyboardButton(t('through_week'), callback_data='week')],
            [InlineKeyboardButton(t('through_month'), callback_data='month')],
            [InlineKeyboardButton(t('select_date'), callback_data='calendar')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(t('choose_send_date'), reply_markup=reply_markup)
        context.user_data['state'] = "selecting_send_date"

async def handle_date_buttons(update: Update, context: CallbackContext):
    """Обработчик выбора даты отправки. Устанавливает дату отправки на неделю, месяц или позволяет выбрать дату из календаря."""
    query = update.callback_query
    if query.data == 'week':
        send_date = datetime.now(pytz.utc) + timedelta(weeks=1)
    elif query.data == 'month':
        send_date = datetime.now(pytz.utc) + timedelta(days=30)
    else:
        await handle_calendar(update, context)
        return
    context.user_data['send_date'] = send_date
    await query.edit_message_text(t('date_selected', date=send_date.strftime('%d.%m.%Y %H:%M')))
    await save_send_date(update, context)

async def handle_calendar(update: Update, context: CallbackContext):
    """Обработчик выбора даты из календаря. Показывает кнопки с датами для выбора."""
    query = update.callback_query
    current_date = datetime.now(pytz.utc)
    keyboard = [[InlineKeyboardButton(f"{(current_date + timedelta(days=i)).day} ({t('today') if i == 0 else t('tomorrow') if i == 1 else f'{i} days'})", callback_data=f"day_{(current_date + timedelta(days=i)).day}")] for i in range(8)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(t('select_date'), reply_markup=reply_markup)

async def handle_calendar_selection(update: Update, context: CallbackContext):
    """Обработчик выбора даты из календаря. Устанавливает выбранную дату для отправки капсулы."""
    query = update.callback_query
    selected_day = int(query.data.split('_')[1])
    send_date = datetime.now(pytz.utc).replace(day=selected_day, hour=0, minute=0, second=0, microsecond=0)
    context.user_data['send_date'] = send_date
    await query.edit_message_text(t('date_selected', date=send_date.strftime('%d.%m.%Y %H:%M')))
    await save_send_date(update, context)

async def handle_delete_confirmation(update: Update, context: CallbackContext):
    """Обработчик подтверждения удаления капсулы. Удаляет капсулу и отправляет подтверждение."""
    query = update.callback_query
    if query.data == "confirm_delete":
        capsule_id = context.user_data.get('selected_capsule_id')
        delete_capsule(capsule_id)
        await query.edit_message_text(t('capsule_deleted', capsule_id=capsule_id))
    else:
        await query.edit_message_text(t('delete_canceled'))
    context.user_data['state'] = "idle"

async def handle_text(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений. Выполняет действия в зависимости от текущего состояния."""
    text = update.message.text.strip()
    state = context.user_data.get('state', 'idle')
    actions = {
        "📦 Создать капсулу": create_capsule_command,
        "📂 Просмотреть капсулы": view_capsules_command,
        "👤 Добавить получателя": add_recipient_command,
        "📨 Отправить капсулу": send_capsule_command,
        "🗑 Удалить капсулу": delete_capsule_command,
        "✏️ Редактировать капсулу": edit_capsule_command,
        "👥 Просмотреть получателей": view_recipients_command,
        "❓ Помощь": help_command,
        "📅 Установить дату отправки": select_send_date,
        "💸 Поддержать автора": support_author,
        "🌍 Сменить язык": change_language
    }
    if text in actions:
        await actions[text](update, context)
    elif state == CREATING_CAPSULE:
        await handle_create_capsule_steps(update, context, text)
    elif state == "adding_recipient":
        await handle_recipient(update, context)
    elif state == "editing_capsule_content":
        await handle_edit_capsule_content(update, context)
    elif state in [SELECTING_CAPSULE_FOR_RECIPIENTS, "sending_capsule", "deleting_capsule", "editing_capsule", "viewing_recipients", SELECTING_CAPSULE]:
        await handle_capsule_selection(update, context)
    else:
        await update.message.reply_text(t('create_capsule_first'))

async def handle_create_capsule_steps(update: Update, context: CallbackContext, text: str):
    """Обработчик шагов создания капсулы. Добавляет текст в капсулу."""
    capsule_content = context.user_data.get('capsule_content', {"text": []})
    if len(capsule_content['text']) < MAX_TEXTS:
        capsule_content['text'].append(text)
        context.user_data['capsule_content'] = capsule_content
        save_capsule_content(context, context.user_data['current_capsule'])
        await update.message.reply_text(t('text_added'))
    else:
        await update.message.reply_text(t('content_limit_exceeded', type="текст"))

async def handle_recipient(update: Update, context: CallbackContext):
    """Обработчик добавления получателей."""
    try:
        usernames = set(update.message.text.strip().split())
        capsule_id = context.user_data.get('selected_capsule_id')
        for username in usernames:
            add_recipient(capsule_id, username.lstrip('@'))
        await update.message.reply_text(t('recipients_added', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателя: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_send_capsule_logic(update: Update, context: CallbackContext, capsule_id: int):
    """Логика отправки капсулы."""
    try:
        capsule = fetch_data("capsules", {"id": capsule_id})
        if not capsule:
            await update.message.reply_text(t('invalid_capsule_id'))
            return
        recipients = get_capsule_recipients(capsule_id)
        if not recipients:
            await update.message.reply_text(t('no_recipients'))
            return
        content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
        for recipient in recipients:
            chat_id = get_chat_id(recipient['recipient_username'])
            if chat_id:
                await context.bot.send_message(chat_id=chat_id, text=t('capsule_received', sender=update.effective_user.username))
                for item in content.get('text', []):
                    await context.bot.send_message(chat_id, item)
                for item in content.get('stickers', []):
                    await context.bot.send_sticker(chat_id, item)
                for item in content.get('photos', []):
                    await context.bot.send_photo(chat_id, item)
                for item in content.get('documents', []):
                    await context.bot.send_document(chat_id, item)
                for item in content.get('voices', []):
                    await context.bot.send_voice(chat_id, item)
                for item in content.get('videos', []):
                    await context.bot.send_video(chat_id, item)
                for item in content.get('audios', []):
                    await context.bot.send_audio(chat_id, item)
                await update.message.reply_text(t('capsule_sent', recipient=recipient['recipient_username']))
            else:
                await update.message.reply_text(t('recipient_not_registered', recipient=recipient['recipient_username']))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.message.reply_text(t('service_unavailable'))

async def handle_edit_capsule_content(update: Update, context: CallbackContext):
    """Обработчик редактирования содержимого капсулы."""
    try:
        capsule_id = context.user_data.get('selected_capsule_id')
        content = json.dumps({"text": [update.message.text]}, ensure_ascii=False)
        edit_capsule(capsule_id, content=content)
        await update.message.reply_text(t('capsule_edited', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при редактировании содержимого капсулы: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_view_recipients_logic(update: Update, context: CallbackContext, capsule_id: int):
    """Логика просмотра получателей капсулы."""
    try:
        recipients = get_capsule_recipients(capsule_id)
        if recipients:
            recipient_list = "\n".join([f"@{r['recipient_username']}" for r in recipients])
            await update.message.reply_text(t('recipients_list', capsule_id=capsule_id, recipients=recipient_list))
        else:
            await update.message.reply_text(t('no_recipients_for_capsule', capsule_id=capsule_id))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_media(update: Update, context: CallbackContext, media_type: str, file_attr: str, max_limit: int):
    """Обработчик медиафайлов."""
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {media_type: []})
    if len(capsule_content[media_type]) >= max_limit:
        await update.message.reply_text(t('content_limit_exceeded', type=media_type[:-1]))
        return
    try:
        file_id = (await getattr(update.message, file_attr).get_file()).file_id
        capsule_content.setdefault(media_type, []).append(file_id)
        context.user_data['capsule_content'] = capsule_content
        save_capsule_content(context, context.user_data['current_capsule'])
        await update.message.reply_text(t(f'{media_type[:-1]}_added'))
        logger.info(f"Добавлен {media_type[:-1]} в капсулу #{context.user_data['current_capsule']}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении {media_type[:-1]}: {e}")
        await update.message.reply_text(t('error_general'))

async def handle_photo(update: Update, context: CallbackContext):
    await handle_media(update, context, "photos", "photo[-1]", MAX_PHOTOS)

async def handle_video(update: Update, context: CallbackContext):
    await handle_media(update, context, "videos", "video", MAX_VIDEOS)

async def handle_audio(update: Update, context: CallbackContext):
    await handle_media(update, context, "audios", "audio", MAX_AUDIOS)

async def handle_document(update: Update, context: CallbackContext):
    await handle_media(update, context, "documents", "document", MAX_DOCUMENTS)

async def handle_sticker(update: Update, context: CallbackContext):
    await handle_media(update, context, "stickers", "sticker", MAX_STICKERS)

async def handle_voice(update: Update, context: CallbackContext):
    await handle_media(update, context, "voices", "voice", MAX_VOICES)

# Вспомогательные функции
async def check_capsule_ownership(update: Update, capsule_id: int, query=None) -> bool:
    user = fetch_data("users", {"telegram_id": update.effective_user.id})
    if not user:
        if query:
            await query.edit_message_text(t('not_registered'))
        else:
            await update.message.reply_text(t('not_registered'))
        return False
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule or capsule[0]['creator_id'] != user[0]['id']:
        if query:
            await query.edit_message_text(t('not_your_capsule'))
        else:
            await update.message.reply_text(t('not_your_capsule'))
        return False
    return True

def save_capsule_content(context: CallbackContext, capsule_id: int):
    content = context.user_data.get('capsule_content', {})
    json_str = json.dumps(content, ensure_ascii=False)
    encrypted = encrypt_data_aes(json_str, ENCRYPTION_KEY_BYTES)
    update_data("capsules", {"id": capsule_id}, {"content": encrypted})

async def save_send_date(update: Update, context: CallbackContext):
    try:
        send_date = context.user_data.get('send_date')
        capsule_id = context.user_data.get('selected_capsule_id')
        if not send_date or not capsule_id:
            await update.callback_query.edit_message_text(t('error_general'))
            return
        edit_capsule(capsule_id, scheduled_at=send_date)
        send_capsule_task.apply_async((capsule_id,), eta=send_date)
        await update.callback_query.edit_message_text(t('date_set', date=send_date.strftime('%d.%m.%Y %H:%M')))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при установке даты: {e}")
        await update.callback_query.edit_message_text(t('service_unavailable'))

async def post_init(application):
    capsules = fetch_data("capsules")
    now = datetime.now(pytz.utc)
    for capsule in capsules:
        if capsule.get('scheduled_at'):
            scheduled_at = datetime.fromisoformat(capsule['scheduled_at']).replace(tzinfo=pytz.utc)
            if scheduled_at > now:
                send_capsule_task.apply_async((capsule['id'],), eta=scheduled_at)
                logger.info(f"Запланирована отправка капсулы #{capsule['id']} на {scheduled_at}")

async def check_bot_permissions(context: CallbackContext):
    me = await context.bot.get_me()
    logger.info(f"Бот запущен как @{me.username}")

# Главная функция
async def main():
    start_services()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    await check_bot_permissions(application)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create_capsule", create_capsule_command))
    application.add_handler(CommandHandler("add_recipient", add_recipient_command))
    application.add_handler(CommandHandler("view_capsules", view_capsules_command))
    application.add_handler(CommandHandler("send_capsule", send_capsule_command))
    application.add_handler(CommandHandler("delete_capsule", delete_capsule_command))
    application.add_handler(CommandHandler("edit_capsule", edit_capsule_command))
    application.add_handler(CommandHandler("view_recipients", view_recipients_command))
    application.add_handler(CommandHandler("support_author", support_author))
    application.add_handler(CommandHandler("select_send_date", select_send_date))
    application.add_handler(CommandHandler("change_language", change_language))
    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r'^(ru|en)$'))
    application.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r'^(week|month|calendar)$'))
    application.add_handler(CallbackQueryHandler(handle_calendar_selection, pattern=r'^day_\d+$'))
    application.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern=r'^(confirm_delete|cancel_delete)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    await application.initialize()
    await post_init(application)
    scheduler.start()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
