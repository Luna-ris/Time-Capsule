import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext, Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import Optional, Dict
from collections import deque
from dotenv import load_dotenv
from tasks import send_capsule_task  # Импортируйте задачу Celery
import i18n  # Для поддержки нескольких языков
import os
import sys
import threading
import pytz
import nest_asyncio

# Загрузка переменных окружения из файла .env
# load_dotenv()

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

if not SUPABASE_URL or not SUPABASE_KEY or not TELEGRAM_TOKEN or not ENCRYPTION_KEY:
    logger.error("Отсутствуют необходимые переменные окружения.")
    sys.exit(1)

# Преобразование ключа шифрования из строки в байты
ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
scheduler = AsyncIOScheduler(timezone=pytz.utc)
bot: Optional[Bot] = None

# Состояния беседы
CAPSULE_TITLE, CAPSULE_CONTENT, SCHEDULE_TIME, ADD_RECIPIENT, SELECTING_SEND_DATE, SELECTING_CAPSULE, SELECTING_CAPSULE_FOR_RECIPIENTS = range(7)

# Инициализация i18n с абсолютным путем
i18n.load_path.append(os.path.join(os.path.dirname(__file__), 'locales'))
i18n.set('locale', 'ru')
i18n.set('fallback', 'en')
logger.info(f"Текущая локаль: {i18n.get('locale')}")
logger.info(f"Тест перевода: {i18n.t('start_message')}")

# Шифрование AES-256
def encrypt_data_aes(data: str, key: bytes) -> str:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return (iv + encrypted).hex()

def decrypt_data_aes(encrypted_hex: str, key: bytes) -> str:
    data = bytes.fromhex(encrypted_hex)
    iv = data[:16]
    encrypted = data[16:]
    cipher = Cipher(algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()
    return unpadded.decode('utf-8')

def fetch_data(table: str, query: dict = {}):
    response = supabase.table(table).select("*")
    for key, value in query.items():
        response = response.eq(key, value)
    response = response.execute()
    return response.data

def post_data(table: str, data: dict):
    response = supabase.table(table).insert(data).execute()
    return response.data

def update_data(table: str, query: dict, data: dict):
    query_builder = supabase.table(table).update(data)
    for key, value in query.items():
        query_builder = query_builder.eq(key, value)
    response = query_builder.execute()
    return response.data

def delete_data(table: str, query: dict):
    response = supabase.table(table).delete().eq(next(iter(query)), query[next(iter(query))]).execute()
    return response.data

def get_chat_id(username: str):
    response = fetch_data("users", {"username": username})
    if response:
        return response[0]['chat_id']
    else:
        logger.error(f"Пользователь {username} не найден.")
        return None

def add_user(username: str, telegram_id: int, chat_id: int):
    existing_user = fetch_data("users", {"telegram_id": telegram_id})
    if not existing_user:
        post_data("users", {
            "telegram_id": telegram_id,
            "username": username,
            "chat_id": chat_id
        })
    else:
        logger.info(f"Пользователь {username} уже существует в базе данных.")

def generate_unique_capsule_number(creator_id: int) -> int:
    capsules = fetch_data("capsules", {"creator_id": creator_id})
    return len(capsules) + 1

def create_capsule(creator_id: int,
                   title: str,
                   content: str,
                   user_capsule_number: int,
                   scheduled_at: datetime = None):
    encrypted_content = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    data = {
        "creator_id": creator_id,
        "title": title,
        "content": encrypted_content,
        "user_capsule_number": user_capsule_number
    }
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    response = post_data("capsules", data)
    return response[0]['id']

def add_recipient(capsule_id: int, recipient_username: str):
    post_data("recipients", {
        "capsule_id": capsule_id,
        "recipient_username": recipient_username
    })

def delete_capsule(capsule_id: int):
    delete_data("recipients", {"capsule_id": capsule_id})
    delete_data("capsules", {"id": capsule_id})

def edit_capsule(capsule_id: int,
                 title: Optional[str] = None,
                 content: Optional[str] = None,
                 scheduled_at: Optional[datetime] = None):
    data = {}
    if title is not None:
        data["title"] = title
    if content is not None:
        encrypted_content = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
        data["content"] = encrypted_content
    if scheduled_at is not None:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    if data:
        update_data("capsules", {"id": capsule_id}, data)

def get_user_capsules(telegram_id: int):
    user = fetch_data("users", {"telegram_id": telegram_id})
    if not user:
        return []
    return fetch_data("capsules", {"creator_id": user[0]['id']})

def get_capsule_recipients(capsule_id: int):
    return fetch_data("recipients", {"capsule_id": capsule_id})

def add_notification(user_id: int, message: str):
    post_data("notifications", {"user_id": user_id, "message": message})

def get_user_notifications(user_id: int):
    return fetch_data("notifications", {"user_id": user_id})

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    if username:
        add_user(username, user_id, chat_id)

    start_text = i18n.t('start_message')

    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(start_text, reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    help_text = i18n.t('help_message')

    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(help_text, reply_markup=reply_markup)

async def change_language(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="ru")],
        [InlineKeyboardButton("English", callback_data="en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(i18n.t('select_language'), reply_markup=reply_markup)

async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    lang = query.data
    if lang == 'ru':
        i18n.set('locale', 'ru')
        new_lang = 'Русский'
    elif lang == 'en':
        i18n.set('locale', 'en')
        new_lang = 'English'
    await query.edit_message_text(f"Язык изменен на {new_lang}.")

    # Обновите клавиатуру
    keyboard = [
        ["📦 Создать капсулу", "📂 Просмотреть капсулы"],
        ["👤 Добавить получателя", "📨 Отправить капсулу"],
        ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
        ["👥 Просмотреть получателей", "❓ Помощь"],
        ["📅 Установить дату отправки", "💸 Поддержать автора"],
        ["🌍 Сменить язык"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.effective_message.reply_text(i18n.t('start_message'), reply_markup=reply_markup)

async def create_capsule_command(update: Update, context: CallbackContext):
    try:
        user = update.message.from_user
        user_id = user.id
        username = user.username or str(user.id)

        existing_user = fetch_data("users", {"telegram_id": user_id})
        if not existing_user:
            response = post_data(
                "users", {
                    "telegram_id": user_id,
                    "username": username,
                    "chat_id": update.message.chat_id
                })
            creator_id = response[0]['id'] if response else None
        else:
            creator_id = existing_user[0]['id']

        if not creator_id:
            await update.message.reply_text(i18n.t('error_user_creation'))
            return

        initial_content = {
            "text": [],
            "photos": [],
            "videos": [],
            "audios": [],
            "documents": [],
            "stickers": [],
            "voices": []
        }

        json_str = json.dumps(initial_content, ensure_ascii=False)
        encrypted = encrypt_data_aes(json_str, ENCRYPTION_KEY_BYTES)

        user_capsule_number = generate_unique_capsule_number(creator_id)

        response = post_data(
            "capsules", {
                "creator_id": creator_id,
                "title": "Без названия",
                "content": encrypted,
                "user_capsule_number": user_capsule_number,
                "created_at": datetime.now().isoformat()
            })
        capsule_id = response[0]['id'] if response else None

        if not capsule_id:
            await update.message.reply_text(i18n.t('error_capsule_creation'))
            return

        context.user_data['current_capsule'] = capsule_id
        context.user_data['capsule_content'] = initial_content

        logger.info(
            f"Создана капсула {capsule_id} с содержимым: {initial_content}")

        await update.message.reply_text(
            i18n.t('capsule_created', capsule_id=capsule_id)
        )
    except Exception as e:
        logger.error(f"Ошибка при создании капсулы: {e}")
        await update.message.reply_text(
            i18n.t('error_general')
        )

async def add_recipient_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "selecting_capsule_for_recipients"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_recipients'))

async def handle_select_capsule_for_recipients(update: Update,
                                               context: CallbackContext):
    try:
        if context.user_data.get(
                'state') == "selecting_capsule_for_recipients":
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
            usernames = update.message.text.strip().split()
            unique_usernames = set(usernames)
            capsule_id = context.user_data.get('selected_capsule_id')
            for username in unique_usernames:
                if username.startswith('@'):
                    username = username[1:]
                add_recipient(capsule_id, username)
            await update.message.reply_text(
                i18n.t('recipients_added', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателя: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def view_capsules_command(update: Update, context: CallbackContext):
    try:
        user_id = update.message.from_user.id
        capsules = get_user_capsules(user_id)

        if capsules:
            response = []
            for capsule in capsules:
                created_at = datetime.fromisoformat(
                    capsule['created_at']).strftime("%d.%m.%Y %H:%M")
                status = i18n.t('scheduled') if capsule[
                    'scheduled_at'] else i18n.t('draft')
                response.append(f"📦 #{capsule['id']} {capsule['title']}\n"
                                f"🕒 {i18n.t('created_at')}: {created_at}\n"
                                f"🔒 {i18n.t('status')}: {status}\n")

            await update.message.reply_text(i18n.t('your_capsules') + "\n".join(response),
                                            parse_mode="Markdown")
        else:
            await update.message.reply_text(i18n.t('no_capsules'))
    except Exception as e:
        logger.error(f"Ошибка при получении капсул: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def send_capsule_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "sending_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_to_send'))

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

            capsule_content = context.user_data.get('capsule_content', {})

            for recipient in recipients:
                recipient_username = recipient['recipient_username']
                chat_id = get_chat_id(recipient_username)
                if chat_id:
                    try:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=i18n.t('capsule_received', sender=update.message.from_user.username)
                        )
                        for text in capsule_content.get('text', []):
                            await context.bot.send_message(chat_id=chat_id,
                                                           text=text)
                        for sticker in capsule_content.get('stickers', []):
                            await context.bot.send_sticker(chat_id=chat_id,
                                                           sticker=sticker)
                        for photo in capsule_content.get('photos', []):
                            await context.bot.send_photo(chat_id=chat_id,
                                                         photo=photo)
                        for document in capsule_content.get('documents', []):
                            await context.bot.send_document(chat_id=chat_id,
                                                            document=document)
                        for voice in capsule_content.get('voices', []):
                            await context.bot.send_voice(chat_id=chat_id,
                                                         voice=voice)
                        for video in capsule_content.get('videos', []):
                            await context.bot.send_video(chat_id=chat_id,
                                                         video=video)
                        for audio in capsule_content.get('audios', []):
                            await context.bot.send_audio(chat_id=chat_id,
                                                         audio=audio)

                        await update.message.reply_text(
                            i18n.t('capsule_sent', recipient=recipient_username)
                        )
                    except Exception as e:
                        await update.message.reply_text(
                            i18n.t('error_sending_capsule', recipient=recipient_username)
                        )
                        logger.error(f"Ошибка при отправке капсулы: {e}")
                else:
                    await update.message.reply_text(
                        i18n.t('recipient_not_registered', recipient=recipient_username)
                    )
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def delete_capsule_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "deleting_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_to_delete'))

async def handle_delete_capsule(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "deleting_capsule":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return

            context.user_data['deleting_capsule_id'] = capsule_id
            await update.message.reply_text(
                i18n.t('confirm_delete'),
                reply_markup=ReplyKeyboardMarkup([["Да"], ["Нет"]],
                                                 resize_keyboard=True))
    except Exception as e:
        logger.error(f"Ошибка при удалении капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_delete(update: Update, context: CallbackContext):
    if update.message.text == "Да":
        capsule_id = context.user_data.get('deleting_capsule_id')
        delete_capsule(capsule_id)
        await update.message.reply_text(i18n.t('capsule_deleted', capsule_id=capsule_id),
                                        reply_markup=ReplyKeyboardMarkup([["📦 Создать капсулу", "📂 Просмотреть капсулы"],
                                                                          ["👤 Добавить получателя", "📨 Отправить капсулу"],
                                                                          ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
                                                                          ["👥 Просмотреть получателей", "❓ Помощь"],
                                                                          ["📅 Установить дату отправки", "💸 Поддержать автора"],
                                                                          ["🌍 Сменить язык"]], resize_keyboard=True))
    elif update.message.text == "Нет":
        await update.message.reply_text(i18n.t('delete_canceled'),
                                        reply_markup=ReplyKeyboardMarkup([["📦 Создать капсулу", "📂 Просмотреть капсулы"],
                                                                          ["👤 Добавить получателя", "📨 Отправить капсулу"],
                                                                          ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
                                                                          ["👥 Просмотреть получателей", "❓ Помощь"],
                                                                          ["📅 Установить дату отправки", "💸 Поддержать автора"],
                                                                          ["🌍 Сменить язык"]], resize_keyboard=True))

async def edit_capsule_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "editing_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_to_edit'))

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

async def handle_edit_capsule_content(update: Update,
                                      context: CallbackContext):
    try:
        if context.user_data.get('state') == "editing_capsule_content":
            capsule_id = context.user_data.get('editing_capsule_id')
            capsule_content = context.user_data.get(
                'capsule_content', {
                    "text": [],
                    "photos": [],
                    "videos": [],
                    "audios": [],
                    "documents": [],
                    "stickers": [],
                    "voices": []
                })
            capsule_content_str = json.dumps(capsule_content)
            title = "Без названия"
            edit_capsule(capsule_id, title, capsule_content_str)
            await update.message.reply_text(i18n.t('capsule_edited', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при редактировании капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def view_recipients_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "viewing_recipients"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_recipients'))

async def check_capsule_ownership(update: Update, capsule_id: int) -> bool:
    user_id = update.message.from_user.id
    user = fetch_data("users", {"telegram_id": user_id})
    if not user:
        await update.message.reply_text(i18n.t('not_registered'))
        return False

    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule or capsule[0]['creator_id'] != user[0]['id']:
        await update.message.reply_text(i18n.t('not_your_capsule'))
        return False

    return True

def get_utc_time(local_time: datetime) -> datetime:
    local_tz = pytz.timezone("Europe/Moscow")
    utc_time = local_tz.localize(local_time).astimezone(pytz.utc)
    return utc_time

async def handle_view_recipients(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "viewing_recipients":
            capsule_id = int(update.message.text.strip())
            if not await check_capsule_ownership(update, capsule_id):
                return

            recipients = get_capsule_recipients(capsule_id)
            if recipients:
                recipient_list = "\n".join([
                    f"@{recipient['recipient_username']}"
                    for recipient in recipients
                ])
                await update.message.reply_text(i18n.t('recipients_list', capsule_id=capsule_id, recipients=recipient_list))
            else:
                await update.message.reply_text(i18n.t('no_recipients_for_capsule', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id'))
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    logger.info(f"Получен текст: {text}")

    if text in [
            "📦 Создать капсулу", "📂 Просмотреть капсулы",
            "👤 Добавить получателя", "📨 Отправить капсулу",
            "🗑 Удалить капсулу", "✏️ Редактировать капсулу",
            "👥 Просмотреть получателей", "❓ Помощь",
            "📅 Установить дату отправки", "💸 Поддержать автора",
            "🌍 Сменить язык"
    ]:
        if text == "📦 Создать капсулу":
            await create_capsule_command(update, context)
        elif text == "📂 Просмотреть капсулы":
            await view_capsules_command(update, context)
        elif text == "👤 Добавить получателя":
            await add_recipient_command(update, context)
        elif text == "📨 Отправить капсулу":
            await send_capsule_command(update, context)
        elif text == "🗑 Удалить капсулу":
            await delete_capsule_command(update, context)
        elif text == "✏️ Редактировать капсулу":
            await edit_capsule_command(update, context)
        elif text == "👥 Просмотреть получателей":
            await view_recipients_command(update, context)
        elif text == "❓ Помощь":
            await help_command(update, context)
        elif text == "📅 Установить дату отправки":
            await select_send_date(update, context)
        elif text == "💸 Поддержать автора":
            await support_author(update, context)
        elif text == "🌍 Сменить язык":
            await change_language(update, context)
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
    elif text:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        capsule_content.setdefault('text', []).append(text)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('text_added'))

async def handle_photo(update: Update, context: CallbackContext):
    try:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        photo_file = await update.message.photo[-1].get_file()
        photo_file_id = photo_file.file_id
        capsule_content.setdefault('photos', []).append(photo_file_id)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('photo_added'))
    except Exception as e:
        logger.error(f"Ошибка при получении фото: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_video(update: Update, context: CallbackContext):
    try:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        video_file = await update.message.video.get_file()
        video_file_id = video_file.file_id
        capsule_content.setdefault('videos', []).append(video_file_id)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('video_added'))
    except Exception as e:
        logger.error(f"Ошибка при получении видео: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_audio(update: Update, context: CallbackContext):
    try:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        audio_file = await update.message.audio.get_file()
        audio_file_id = audio_file.file_id
        capsule_content.setdefault('audios', []).append(audio_file_id)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('audio_added'))
    except Exception as e:
        logger.error(f"Ошибка при получении аудио: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_document(update: Update, context: CallbackContext):
    try:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        document_file = await update.message.document.get_file()
        document_file_id = document_file.file_id
        capsule_content.setdefault('documents', []).append(document_file_id)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('document_added'))
    except Exception as e:
        logger.error(f"Ошибка при получении документа: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_sticker(update: Update, context: CallbackContext):
    try:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        sticker_file = await update.message.sticker.get_file()
        sticker_file_id = sticker_file.file_id
        capsule_content.setdefault('stickers', []).append(sticker_file_id)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('sticker_added'))
    except Exception as e:
        logger.error(f"Ошибка при получении стикера: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def handle_voice(update: Update, context: CallbackContext):
    try:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return

        capsule_content = context.user_data.get(
            'capsule_content', {
                "text": [],
                "photos": [],
                "videos": [],
                "audios": [],
                "documents": [],
                "stickers": [],
                "voices": []
            })
        voice_file = await update.message.voice.get_file()
        voice_file_id = voice_file.file_id
        capsule_content.setdefault('voices', []).append(voice_file_id)
        context.user_data['capsule_content'] = capsule_content

        save_capsule_content(context, capsule_id)

        await update.message.reply_text(i18n.t('voice_added'))
    except Exception as e:
        logger.error(f"Ошибка при получении голосового сообщения: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def select_send_date(update: Update, context: CallbackContext):
    context.user_data['state'] = "selecting_capsule"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_date'))

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

async def handle_date_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == 'week':
        send_date = datetime.now() + timedelta(weeks=1)
        context.user_data['send_date'] = send_date
        await query.edit_message_text(i18n.t('date_selected', date=send_date))
        await save_send_date(update, context)
    elif query.data == 'month':
        send_date = datetime.now() + timedelta(days=30)
        context.user_data['send_date'] = send_date
        await query.edit_message_text(i18n.t('date_selected', date=send_date))
        await save_send_date(update, context)
    elif query.data == 'calendar':
        await handle_calendar(update, context)

async def handle_calendar(update: Update, context: CallbackContext):
    query = update.callback_query
    current_date = datetime.now()
    keyboard = [
        [InlineKeyboardButton(f"{current_date.day} {i18n.t('today')}", callback_data=f"day_{current_date.day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=1)).day} {i18n.t('tomorrow')}", callback_data=f"day_{(current_date + timedelta(days=1)).day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=2)).day} {i18n.t('in_2_days')}", callback_data=f"day_{(current_date + timedelta(days=2)).day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=3)).day} {i18n.t('in_3_days')}", callback_data=f"day_{(current_date + timedelta(days=3)).day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=4)).day} {i18n.t('in_4_days')}", callback_data=f"day_{(current_date + timedelta(days=4)).day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=5)).day} {i18n.t('in_5_days')}", callback_data=f"day_{(current_date + timedelta(days=5)).day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=6)).day} {i18n.t('in_6_days')}", callback_data=f"day_{(current_date + timedelta(days=6)).day}")],
        [InlineKeyboardButton(f"{(current_date + timedelta(days=7)).day} {i18n.t('in_7_days')}", callback_data=f"day_{(current_date + timedelta(days=7)).day}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(i18n.t('select_date'), reply_markup=reply_markup)

async def handle_calendar_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_day = int(query.data.split('_')[1])
    current_date = datetime.now()
    send_date = current_date.replace(day=selected_day)
    context.user_data['send_date'] = send_date
    await query.edit_message_text(i18n.t('date_selected', date=send_date))
    await save_send_date(update, context)

async def handle_select_send_date(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "selecting_send_date":
            capsule_id = context.user_data.get('selected_capsule_id')
            send_date_str = update.message.text.strip()
            send_date = datetime.strptime(send_date_str, "%d.%m.%Y %H:%M")
            send_date_utc = get_utc_time(send_date)
            edit_capsule(capsule_id, scheduled_at=send_date_utc)
            send_capsule_task.apply_async((capsule_id,), eta=send_date_utc)
            await update.message.reply_text(i18n.t('date_set', date=send_date_utc))
            context.user_data['state'] = "idle"
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите дату в формате ДД.ММ.ГГГГ ЧЧ:ММ")
    except Exception as e:
        logger.error(f"Ошибка при установке даты: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def save_send_date(update: Update, context: CallbackContext):
    try:
        send_date = context.user_data.get('send_date')
        capsule_id = context.user_data.get('selected_capsule_id')
        if not send_date or not capsule_id:
            await update.message.reply_text(i18n.t('error_general'))
            return

        job_id = f"capsule_{capsule_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        edit_capsule(capsule_id, scheduled_at=send_date)

        # Используем Celery для выполнения задачи
        send_capsule_task.apply_async((capsule_id, ), eta=send_date)

        logger.info(f"Задача на отправку капсулы {capsule_id} добавлена в Celery на {send_date}.")

        await update.message.reply_text(i18n.t('date_set', date=send_date))
        context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при установке даты отправки: {e}")
        await update.message.reply_text(i18n.t('error_general'))

async def support_author(update: Update, context: CallbackContext):
    DONATION_URL = "https://www.donationalerts.com/r/lunarisqqq"
    await update.message.reply_text(i18n.t('support_author', url=DONATION_URL))

def save_capsule_content(context: CallbackContext, capsule_id: int):
    try:
        content = context.user_data.get('capsule_content', {})
        validated_content = {
            "text": [str(item) for item in content.get("text", [])],
            "photos": [str(item) for item in content.get("photos", [])],
            "videos": [str(item) for item in content.get("videos", [])],
            "audios": [str(item) for item in content.get("audios", [])],
            "documents": [str(item) for item in content.get("documents", [])],
            "stickers": [str(item) for item in content.get("stickers", [])],
            "voices": [str(item) for item in content.get("voices", [])]
        }

        json_str = json.dumps(validated_content, ensure_ascii=False)
        encrypted = encrypt_data_aes(json_str, ENCRYPTION_KEY_BYTES)
        update_data("capsules", {"id": capsule_id}, {"content": encrypted})

        logger.info(f"Содержимое сохранено для капсулы {capsule_id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения содержимого: {str(e)}")
        raise

async def post_init(application):
    logger.info("Начало инициализации планировщика")
    try:
        capsules = fetch_data("capsules")
        logger.info(f"Найдено {len(capsules)} капсул в базе данных")

        now = datetime.now(pytz.utc)
        logger.info(f"Текущее время UTC: {now}")

        for capsule in capsules:
            if capsule.get('scheduled_at'):
                scheduled_at = datetime.fromisoformat(
                    capsule['scheduled_at']).replace(tzinfo=pytz.utc)
                logger.info(
                    f"Обработка капсулы {capsule['id']}, запланированной на {scheduled_at}"
                )

                if scheduled_at > now:
                    logger.info(
                        f"Добавление задачи для капсулы {capsule['id']}")
                    scheduler.add_job(
                        send_capsule_task.delay,
                        'date',
                        run_date=scheduled_at,
                        args=[capsule['id']],
                        id=f"capsule_{capsule['id']}",
                        timezone=pytz.utc)
        logger.info("Инициализация планировщика завершена")
    except Exception as e:
        logger.error(f"Не удалось инициализировать планировщик: {str(e)}")

async def check_bot_permissions(context: CallbackContext):
    try:
        me = await context.bot.get_me()
        logger.info(f"Бот запущен как @{me.username}")
    except Exception as e:
        logger.error(f"Ошибка аутентификации бота: {str(e)}")
        sys.exit(1)

async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    await check_bot_permissions(application)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        CommandHandler("create_capsule", create_capsule_command))
    application.add_handler(
        CommandHandler("add_recipient", add_recipient_command))
    application.add_handler(
        CommandHandler("view_capsules", view_capsules_command))
    application.add_handler(
        CommandHandler("send_capsule", send_capsule_command))
    application.add_handler(
        CommandHandler("delete_capsule", delete_capsule_command))
    application.add_handler(
        CommandHandler("edit_capsule", edit_capsule_command))
    application.add_handler(
        CommandHandler("view_recipients", view_recipients_command))
    application.add_handler(CommandHandler("support_author", support_author))
    application.add_handler(
        CommandHandler("select_send_date", select_send_date))
    application.add_handler(
        CommandHandler("change_language", change_language))

    application.add_handler(
        CallbackQueryHandler(handle_language_selection, pattern=r'^(ru|en)$'))
    application.add_handler(
        CallbackQueryHandler(handle_date_buttons, pattern=r'^(week|month|calendar)$'))
    application.add_handler(
        CallbackQueryHandler(handle_calendar_selection, pattern=r'^day_\d+$'))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(
        MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.Sticker.ALL,
                                           handle_sticker))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    scheduler.start()

    await application.initialize()
    await post_init(application)
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
