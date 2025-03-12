import logging
import asyncio
import subprocess
import time
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext, Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, Dict
from dotenv import load_dotenv
from tasks import send_capsule_task
import i18n
import sys
import pytz
import nest_asyncio

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Применение nest_asyncio
nest_asyncio.apply()

# Инициализация клиентов
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN, ENCRYPTION_KEY]):
    logger.error("Отсутствуют необходимые переменные окружения.")
    sys.exit(1)

# Преобразование ключа шифрования
ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
scheduler = AsyncIOScheduler(timezone=pytz.utc)
bot: Optional[Bot] = None

# Состояния беседы
CAPSULE_TITLE, CAPSULE_CONTENT, SCHEDULE_TIME, ADD_RECIPIENT, SELECTING_SEND_DATE, SELECTING_CAPSULE, SELECTING_CAPSULE_FOR_RECIPIENTS = range(7)

# Инициализация i18n с проверкой
i18n.load_path.append(os.path.join(os.path.dirname(__file__), 'locales'))
i18n.set('locale', 'ru')
i18n.set('fallback', 'en')

# Проверка загрузки локализации
locale_dir = os.path.join(os.path.dirname(__file__), 'locales')
if not os.path.exists(locale_dir):
    logger.error(f"Папка locales не найдена по пути: {locale_dir}")
    sys.exit(1)
if not os.path.exists(os.path.join(locale_dir, 'ru.json')):
    logger.error("Файл ru.json не найден в папке locales")
    sys.exit(1)
logger.info(f"Текущая локаль: {i18n.get('locale')}")
logger.info(f"Тест перевода start_message: {i18n.t('start_message')}")
logger.info(f"Тест перевода capsule_created: {i18n.t('capsule_created', capsule_id=1)}")

# Функция для запуска внешних процессов
def start_process(command, name):
    try:
        # Проверяем, запущен ли процесс уже
        if name == "redis" and os.system("redis-cli ping") == 0:
            logger.info("Redis уже запущен.")
            return True
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"{name} запущен с PID: {process.pid}")
        # Даем процессу время на запуск
        time.sleep(2)
        # Проверяем, работает ли процесс
        if process.poll() is None:
            return True
        else:
            error = process.stderr.read().decode()
            logger.error(f"Ошибка запуска {name}: {error}")
            return False
    except Exception as e:
        logger.error(f"Не удалось запустить {name}: {e}")
        return False

# Запуск Redis и Celery
def start_services():
    # Запуск Redis
    redis_success = start_process("redis-server", "Redis")
    if not redis_success:
        logger.error("Не удалось запустить Redis. Завершение работы.")
        sys.exit(1)

    # Даем Redis время на инициализацию
    time.sleep(2)

    # Запуск Celery
    celery_command = "celery -A celery_config.celery_app worker --loglevel=info"
    celery_success = start_process(celery_command, "Celery")
    if not celery_success:
        logger.error("Не удалось запустить Celery. Завершение работы.")
        sys.exit(1)

# Шифрование AES-256
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

# Функции работы с Supabase
def fetch_data(table: str, query: dict = {}):
    response = supabase.table(table).select("*")
    for key, value in query.items():
        response = response.eq(key, value)
    return response.execute().data

def post_data(table: str, data: dict):
    return supabase.table(table).insert(data).execute().data

def update_data(table: str, query: dict, data: dict):
    query_builder = supabase.table(table).update(data)
    for key, value in query.items():
        query_builder = query_builder.eq(key, value)
    return query_builder.execute().data

def delete_data(table: str, query: dict):
    return supabase.table(table).delete().eq(next(iter(query)), query[next(iter(query))]).execute().data

def get_chat_id(username: str):
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

def add_user(username: str, telegram_id: int, chat_id: int):
    if not fetch_data("users", {"telegram_id": telegram_id}):
        post_data("users", {"telegram_id": telegram_id, "username": username, "chat_id": chat_id})

def generate_unique_capsule_number(creator_id: int) -> int:
    return len(fetch_data("capsules", {"creator_id": creator_id})) + 1

def create_capsule(creator_id: int, title: str, content: str, user_capsule_number: int, scheduled_at: datetime = None):
    encrypted_content = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    data = {"creator_id": creator_id, "title": title, "content": encrypted_content, "user_capsule_number": user_capsule_number}
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    return post_data("capsules", data)[0]['id']

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

def get_user_capsules(telegram_id: int):
    user = fetch_data("users", {"telegram_id": telegram_id})
    return fetch_data("capsules", {"creator_id": user[0]['id']}) if user else []

def get_capsule_recipients(capsule_id: int):
    return fetch_data("recipients", {"capsule_id": capsule_id})

# Обработчики команд
async def start(update: Update, context: CallbackContext):
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
    await update.message.reply_text(i18n.t('start_message'), reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(i18n.t('help_message'), reply_markup=reply_markup)

async def create_capsule_command(update: Update, context: CallbackContext):
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

        context.user_data['current_capsule'] = capsule_id
        context.user_data['capsule_content'] = json.loads(initial_content)

        await update.message.reply_text(i18n.t('capsule_created', capsule_id=capsule_id))
    except Exception as e:
        logger.error(f"Ошибка при создании капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def add_recipient_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "selecting_capsule_for_recipients"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_recipients'))

async def view_capsules_command(update: Update, context: CallbackContext):
    try:
        capsules = get_user_capsules(update.message.from_user.id)
        if capsules:
            response = [f"📦 #{c['id']} {c['title']}\n🕒 {i18n.t('created_at')}: {datetime.fromisoformat(c['created_at']).strftime('%d.%m.%Y %H:%M')}\n🔒 {i18n.t('status')}: {i18n.t('scheduled') if c['scheduled_at'] else i18n.t('draft')}" for c in capsules]
            await update.message.reply_text(i18n.t('your_capsules') + "\n" + "\n".join(response), parse_mode="Markdown")
        else:
            await update.message.reply_text(i18n.t('no_capsules'))
    except Exception as e:
        logger.error(f"Ошибка при получении капсул: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def send_capsule_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "sending_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_to_send'))

async def delete_capsule_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "deleting_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_to_delete'))

async def edit_capsule_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "editing_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_to_edit'))

async def view_recipients_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "viewing_recipients"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_recipients'))

async def select_send_date(update: Update, context: CallbackContext):
    context.user_data['state'] = "selecting_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_date'))

async def support_author(update: Update, context: CallbackContext):
    DONATION_URL = "https://www.donationalerts.com/r/lunarisqqq"
    await update.message.reply_text(i18n.t('support_author', url=DONATION_URL))

async def change_language(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="ru")],
        [InlineKeyboardButton("English", callback_data="en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(i18n.t('select_language'), reply_markup=reply_markup)

# Обработчики callback-запросов
async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    lang = query.data
    i18n.set('locale', lang)
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
    await context.bot.send_message(chat_id=update.effective_chat.id, text=i18n.t('start_message'), reply_markup=reply_markup)

async def handle_date_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == 'week':
        send_date = datetime.now() + timedelta(weeks=1)
    elif query.data == 'month':
        send_date = datetime.now() + timedelta(days=30)
    else:
        await handle_calendar(update, context)
        return
    context.user_data['send_date'] = send_date
    await query.edit_message_text(i18n.t('date_selected', date=send_date))
    await save_send_date(update, context)

async def handle_calendar(update: Update, context: CallbackContext):
    query = update.callback_query
    current_date = datetime.now()
    keyboard = [[InlineKeyboardButton(f"{(current_date + timedelta(days=i)).day} ({i18n.t('today') if i == 0 else i18n.t('tomorrow') if i == 1 else f'{i} days'})", callback_data=f"day_{(current_date + timedelta(days=i)).day}")] for i in range(8)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(i18n.t('select_date'), reply_markup=reply_markup)

async def handle_calendar_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_day = int(query.data.split('_')[1])
    send_date = datetime.now().replace(day=selected_day)
    context.user_data['send_date'] = send_date
    await query.edit_message_text(i18n.t('date_selected', date=send_date))
    await save_send_date(update, context)

# Обработчики текстовых сообщений и состояний
async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    logger.info(f"Получен текст: {text}")
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
    elif context.user_data.get('state') == "adding_recipient":
        await handle_recipient(update, context)
    elif context.user_data.get('state') == "sending_capsule":
        await handle_send_capsule(update, context)
    elif context.user_data.get('state') == "deleting_capsule":
        await handle_delete_capsule(update, context)
    elif context.user_data.get('state') == "editing_capsule":
        await handle_edit_capsule(update, context)
    elif context.user_data.get('state') == "editing_capsule_content":
        await handle_edit_capsule_content(update, context)
    elif context.user_data.get('state') == "viewing_recipients":
        await handle_view_recipients(update, context)
    elif context.user_data.get('state') == "selecting_send_date":
        await handle_select_send_date(update, context)
    elif context.user_data.get('state') == "selecting_capsule":
        await handle_select_capsule(update, context)
    elif context.user_data.get('state') == "selecting_capsule_for_recipients":
        await handle_select_capsule_for_recipients(update, context)
    elif text and context.user_data.get('current_capsule'):
        capsule_content = context.user_data.get('capsule_content', {"text": []})
        capsule_content['text'].append(text)
        context.user_data['capsule_content'] = capsule_content
        save_capsule_content(context, context.user_data['current_capsule'])
        await update.message.reply_text(i18n.t('text_added'))
    else:
        await update.message.reply_text(i18n.t('create_capsule_first'))

async def handle_select_capsule_for_recipients(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "selecting_capsule_for_recipients":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return
            context.user_data['selected_capsule_id'] = capsule_id
            await update.message.reply_text(i18n.t('enter_recipients'))
            context.user_data['state'] = "adding_recipient"
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id'))
    except Exception as e:
        logger.error(f"Ошибка при выборе капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_recipient(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "adding_recipient":
            usernames = set(update.message.text.strip().split())
            capsule_id = context.user_data.get('selected_capsule_id')
            for username in usernames:
                add_recipient(capsule_id, username.lstrip('@'))
            await update.message.reply_text(i18n.t('recipients_added', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателя: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_send_capsule(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "sending_capsule":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return
            capsule = fetch_data("capsules", {"id": capsule_id})[0]
            recipients = get_capsule_recipients(capsule_id)
            if not recipients:
                await update.message.reply_text(i18n.t('no_recipients'))
                return
            content = json.loads(decrypt_data_aes(capsule['content'], ENCRYPTION_KEY_BYTES))
            for recipient in recipients:
                chat_id = get_chat_id(recipient['recipient_username'])
                if chat_id:
                    await context.bot.send_message(chat_id=chat_id, text=i18n.t('capsule_received', sender=update.message.from_user.username))
                    for item in content.get('text', []): await context.bot.send_message(chat_id, item)
                    for item in content.get('stickers', []): await context.bot.send_sticker(chat_id, item)
                    for item in content.get('photos', []): await context.bot.send_photo(chat_id, item)
                    for item in content.get('documents', []): await context.bot.send_document(chat_id, item)
                    for item in content.get('voices', []): await context.bot.send_voice(chat_id, item)
                    for item in content.get('videos', []): await context.bot.send_video(chat_id, item)
                    for item in content.get('audios', []): await context.bot.send_audio(chat_id, item)
                    await update.message.reply_text(i18n.t('capsule_sent', recipient=recipient['recipient_username']))
                else:
                    await update.message.reply_text(i18n.t('recipient_not_registered', recipient=recipient['recipient_username']))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_delete_capsule(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "deleting_capsule":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return
            context.user_data['deleting_capsule_id'] = capsule_id
            await update.message.reply_text(i18n.t('confirm_delete'), reply_markup=ReplyKeyboardMarkup([["Да"], ["Нет"]], resize_keyboard=True))
    except Exception as e:
        logger.error(f"Ошибка при удалении капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_delete(update: Update, context: CallbackContext):
    if update.message.text == "Да":
        capsule_id = context.user_data.get('deleting_capsule_id')
        delete_capsule(capsule_id)
        await update.message.reply_text(i18n.t('capsule_deleted', capsule_id=capsule_id))
    elif update.message.text == "Нет":
        await update.message.reply_text(i18n.t('delete_canceled'))
    context.user_data['state'] = "idle"

async def handle_edit_capsule(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "editing_capsule":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return
            context.user_data['editing_capsule_id'] = capsule_id
            await update.message.reply_text(i18n.t('enter_new_content'))
            context.user_data['state'] = "editing_capsule_content"
    except Exception as e:
        logger.error(f"Ошибка при редактировании капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_edit_capsule_content(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "editing_capsule_content":
            capsule_id = context.user_data.get('editing_capsule_id')
            content = json.dumps(context.user_data.get('capsule_content', {"text": [update.message.text]}))
            edit_capsule(capsule_id, title="Без названия", content=content)
            await update.message.reply_text(i18n.t('capsule_edited', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при редактировании капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_view_recipients(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "viewing_recipients":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return
            recipients = get_capsule_recipients(capsule_id)
            if recipients:
                recipient_list = "\n".join([f"@{r['recipient_username']}" for r in recipients])
                await update.message.reply_text(i18n.t('recipients_list', capsule_id=capsule_id, recipients=recipient_list))
            else:
                await update.message.reply_text(i18n.t('no_recipients_for_capsule', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id'))
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_select_capsule(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "selecting_capsule":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return
            context.user_data['selected_capsule_id'] = capsule_id
            keyboard = [
                [InlineKeyboardButton(i18n.t('through_week'), callback_data='week')],
                [InlineKeyboardButton(i18n.t('through_month'), callback_data='month')],
                [InlineKeyboardButton(i18n.t('select_date'), callback_data='calendar')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(i18n.t('choose_send_date'), reply_markup=reply_markup)
            context.user_data['state'] = "selecting_send_date"
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id'))
    except Exception as e:
        logger.error(f"Ошибка при выборе капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_select_send_date(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "selecting_send_date":
            capsule_id = context.user_data.get('selected_capsule_id')
            send_date_str = update.message.text.strip()
            send_date = datetime.strptime(send_date_str, "%d.%m.%Y %H:%M")
            send_date_utc = pytz.utc.localize(send_date)
            edit_capsule(capsule_id, scheduled_at=send_date_utc)
            send_capsule_task.apply_async((capsule_id,), eta=send_date_utc)
            await update.message.reply_text(i18n.t('date_set', date=send_date_utc))
            context.user_data['state'] = "idle"
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ ЧЧ:ММ")
    except Exception as e:
        logger.error(f"Ошибка при установке даты: {e}")
        await update.message.reply_text(i18n.t('error_general'))

# Обработчики медиа
async def handle_photo(update: Update, context: CallbackContext):
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"photos": []})
    photo_file_id = (await update.message.photo[-1].get_file()).file_id
    capsule_content.setdefault('photos', []).append(photo_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(i18n.t('photo_added'))

async def handle_video(update: Update, context: CallbackContext):
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"videos": []})
    video_file_id = (await update.message.video.get_file()).file_id
    capsule_content.setdefault('videos', []).append(video_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(i18n.t('video_added'))

async def handle_audio(update: Update, context: CallbackContext):
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"audios": []})
    audio_file_id = (await update.message.audio.get_file()).file_id
    capsule_content.setdefault('audios', []).append(audio_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(i18n.t('audio_added'))

async def handle_document(update: Update, context: CallbackContext):
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"documents": []})
    document_file_id = (await update.message.document.get_file()).file_id
    capsule_content.setdefault('documents', []).append(document_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(i18n.t('document_added'))

async def handle_sticker(update: Update, context: CallbackContext):
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"stickers": []})
    sticker_file_id = (await update.message.sticker.get_file()).file_id
    capsule_content.setdefault('stickers', []).append(sticker_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(i18n.t('sticker_added'))

async def handle_voice(update: Update, context: CallbackContext):
    if not context.user_data.get('current_capsule'):
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"voices": []})
    voice_file_id = (await update.message.voice.get_file()).file_id
    capsule_content.setdefault('voices', []).append(voice_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, context.user_data['current_capsule'])
    await update.message.reply_text(i18n.t('voice_added'))

# Вспомогательные функции
async def check_capsule_ownership(update: Update, capsule_id: int) -> bool:
    user = fetch_data("users", {"telegram_id": update.message.from_user.id})
    if not user:
        await update.message.reply_text(i18n.t('not_registered'))
        return False
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule or capsule[0]['creator_id'] != user[0]['id']:
        await update.message.reply_text(i18n.t('not_your_capsule'))
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
            await update.message.reply_text(i18n.t('error_general'))
            return
        edit_capsule(capsule_id, scheduled_at=send_date)
        send_capsule_task.apply_async((capsule_id,), eta=send_date)
        await update.message.reply_text(i18n.t('date_set', date=send_date))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при установке даты: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def post_init(application):
    capsules = fetch_data("capsules")
    now = datetime.now(pytz.utc)
    for capsule in capsules:
        if capsule.get('scheduled_at'):
            scheduled_at = datetime.fromisoformat(capsule['scheduled_at']).replace(tzinfo=pytz.utc)
            if scheduled_at > now:
                scheduler.add_job(send_capsule_task.delay, 'date', run_date=scheduled_at, args=[capsule['id']], id=f"capsule_{capsule['id']}", timezone=pytz.utc)

async def check_bot_permissions(context: CallbackContext):
    me = await context.bot.get_me()
    logger.info(f"Бот запущен как @{me.username}")

# Главная функция
async def main():
    # Запускаем Redis и Celery перед стартом бота
    start_services()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    await check_bot_permissions(application)

    # Регистрация обработчиков команд
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

    # Регистрация callback-запросов
    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r'^(ru|en)$'))
    application.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r'^(week|month|calendar)$'))
    application.add_handler(CallbackQueryHandler(handle_calendar_selection, pattern=r'^day_\d+$'))

    # Регистрация обработчиков сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    scheduler.start()
    await application.initialize()
    await post_init(application)
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
