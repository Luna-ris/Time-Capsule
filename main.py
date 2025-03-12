import asyncio
import logging
import nest_asyncio
import os
import sys
import threading
import pytz
from telegram import Update, Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

nest_asyncio.apply()

# Инициализация клиентов
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not TELEGRAM_TOKEN or not ENCRYPTION_KEY:
    logger.error("Отсутствуют необходимые переменные окружения.")
    sys.exit(1)

ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
scheduler = AsyncIOScheduler(timezone=pytz.utc)
bot: Optional[Bot] = None

# Состояния беседы
CAPSULE_TITLE, CAPSULE_CONTENT, SCHEDULE_TIME, ADD_RECIPIENT, SELECTING_SEND_DATE, SELECTING_CAPSULE, SELECTING_CAPSULE_FOR_RECIPIENTS = range(7)

# Инициализация i18n
i18n.load_path.append('locales')
i18n.set('locale', 'ru')

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
    iv = data[:16]
    encrypted = data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
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
    response = supabase.table(table).delete().eq(query).execute()
    return response.data

def get_chat_id(username: str):
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

def add_user(username: str, telegram_id: int, chat_id: int):
    existing_user = fetch_data("users", {"telegram_id": telegram_id})
    if not existing_user:
        post_data("users", {"telegram_id": telegram_id, "username": username, "chat_id": chat_id})
    else:
        logger.info(f"Пользователь {username} уже существует.")

def generate_unique_capsule_number(creator_id: int) -> int:
    capsules = fetch_data("capsules", {"creator_id": creator_id})
    return len(capsules) + 1

def create_capsule(creator_id: int, title: str, content: str, user_capsule_number: int, scheduled_at: datetime = None):
    encrypted_content = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    data = {"creator_id": creator_id, "title": title, "content": encrypted_content, "user_capsule_number": user_capsule_number}
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    response = post_data("capsules", data)
    return response[0]['id']

def add_recipient(capsule_id: int, recipient_username: str):
    post_data("recipients", {"capsule_id": capsule_id, "recipient_username": recipient_username})

def delete_capsule(capsule_id: int):
    delete_data("recipients", {"capsule_id": capsule_id})
    delete_data("capsules", {"id": capsule_id})

def edit_capsule(capsule_id: int, title: Optional[str] = None, content: Optional[str] = None, scheduled_at: Optional[datetime] = None):
    data = {}
    if title: data["title"] = title
    if content: data["content"] = encrypt_data_aes(content, ENCRYPTION_KEY_BYTES)
    if scheduled_at: data["scheduled_at"] = scheduled_at.astimezone(pytz.utc).isoformat()
    if data: update_data("capsules", {"id": capsule_id}, data)

def get_user_capsules(telegram_id: int):
    user = fetch_data("users", {"telegram_id": telegram_id})
    return fetch_data("capsules", {"creator_id": user[0]['id']}) if user else []

def get_capsule_recipients(capsule_id: int):
    return fetch_data("recipients", {"capsule_id": capsule_id})

def get_utc_time(local_time: datetime) -> datetime:
    local_tz = pytz.timezone("Europe/Moscow")
    return local_tz.localize(local_time).astimezone(pytz.utc)

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    username = update.message.from_user.username
    if username:
        add_user(username, user_id, chat_id)

    lang = update.message.from_user.language_code or 'en'
    i18n.set('locale', lang if lang in ['ru', 'en'] else 'en')

    start_text = i18n.t('start_message')
    keyboard = [["📦 Создать капсулу", "📂 Просмотреть капсулы"],
                ["👤 Добавить получателя", "📨 Отправить капсулу"],
                ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
                ["👥 Просмотреть получателей", "❓ Помощь"],
                ["📅 Установить дату отправки", "💸 Поддержать автора"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(start_text, reply_markup=reply_markup)

async def help_command(update: Update, context: CallbackContext):
    help_text = i18n.t('help_message')
    keyboard = [["📦 Создать капсулу", "📂 Просмотреть капсулы"],
                ["👤 Добавить получателя", "📨 Отправить капсулу"],
                ["🗑 Удалить капсулу", "✏️ Редактировать капсулу"],
                ["👥 Просмотреть получателей", "❓ Помощь"],
                ["📅 Установить дату отправки", "💸 Поддержать автора"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(help_text, reply_markup=reply_markup)

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
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def add_recipient_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "selecting_capsule_for_recipients"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_recipients'))

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
        await update.message.reply_text(i18n.t('invalid_capsule_id') + "\n\n" + i18n.t('hint_enter_number'))
    except Exception as e:
        logger.error(f"Ошибка при выборе капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def handle_recipient(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "adding_recipient":
            usernames = update.message.text.strip().split()
            capsule_id = context.user_data.get('selected_capsule_id')
            for username in set(usernames):
                if username.startswith('@'): username = username[1:]
                add_recipient(capsule_id, username)
            await update.message.reply_text(i18n.t('recipients_added', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при добавлении получателя: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def view_capsules_command(update: Update, context: CallbackContext):
    try:
        capsules = get_user_capsules(update.message.from_user.id)
        if capsules:
            response = [f"📦 #{c['id']} {c['title']}\n🕒 {i18n.t('created_at')}: {datetime.fromisoformat(c['created_at']).strftime('%d.%m.%Y %H:%M')}\n🔒 {i18n.t('status')}: {i18n.t('scheduled') if c['scheduled_at'] else i18n.t('draft')}\n" for c in capsules]
            await update.message.reply_text(i18n.t('your_capsules') + "\n".join(response), parse_mode="Markdown")
        else:
            await update.message.reply_text(i18n.t('no_capsules'))
    except Exception as e:
        logger.error(f"Ошибка при получении капсул: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

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
                await update.message.reply_text(i18n.t('no_recipients') + "\n\n" + i18n.t('hint_add_recipient'))
                return
            capsule_content = context.user_data.get('capsule_content', {})
            for recipient in recipients:
                chat_id = get_chat_id(recipient['recipient_username'])
                if chat_id:
                    try:
                        await context.bot.send_message(chat_id=chat_id, text=i18n.t('capsule_received', sender=update.message.from_user.username))
                        for item in capsule_content.get('text', []): await context.bot.send_message(chat_id=chat_id, text=item)
                        for item in capsule_content.get('photos', []): await context.bot.send_photo(chat_id=chat_id, photo=item)
                        for item in capsule_content.get('videos', []): await context.bot.send_video(chat_id=chat_id, video=item)
                        for item in capsule_content.get('audios', []): await context.bot.send_audio(chat_id=chat_id, audio=item)
                        for item in capsule_content.get('documents', []): await context.bot.send_document(chat_id=chat_id, document=item)
                        for item in capsule_content.get('stickers', []): await context.bot.send_sticker(chat_id=chat_id, sticker=item)
                        for item in capsule_content.get('voices', []): await context.bot.send_voice(chat_id=chat_id, voice=item)
                        await update.message.reply_text(i18n.t('capsule_sent', recipient=recipient['recipient_username']))
                    except Exception as e:
                        logger.error(f"Ошибка при отправке капсулы: {e}")
                        await update.message.reply_text(i18n.t('error_sending_capsule', recipient=recipient['recipient_username']))
                else:
                    await update.message.reply_text(i18n.t('recipient_not_registered', recipient=recipient['recipient_username']))
            context.user_data['state'] = "idle"
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id') + "\n\n" + i18n.t('hint_enter_number'))
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

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
            await update.message.reply_text(i18n.t('confirm_delete'), reply_markup=ReplyKeyboardMarkup([["Да"], ["Нет"]], resize_keyboard=True))
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id') + "\n\n" + i18n.t('hint_enter_number'))
    except Exception as e:
        logger.error(f"Ошибка при удалении капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def handle_delete(update: Update, context: CallbackContext):
    if update.message.text == "Да":
        capsule_id = context.user_data.get('deleting_capsule_id')
        delete_capsule(capsule_id)
        await update.message.reply_text(i18n.t('capsule_deleted', capsule_id=capsule_id), reply_markup=ReplyKeyboardRemove())
    elif update.message.text == "Нет":
        await update.message.reply_text(i18n.t('delete_canceled'), reply_markup=ReplyKeyboardRemove())

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
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id') + "\n\n" + i18n.t('hint_enter_number'))
    except Exception as e:
        logger.error(f"Ошибка при редактировании капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def handle_edit_capsule_content(update: Update, context: CallbackContext):
    try:
        if context.user_data.get('state') == "editing_capsule_content":
            capsule_id = context.user_data.get('editing_capsule_id')
            capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
            capsule_content['text'].append(update.message.text)
            edit_capsule(capsule_id, content=json.dumps(capsule_content, ensure_ascii=False))
            await update.message.reply_text(i18n.t('capsule_edited', capsule_id=capsule_id))
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при редактировании капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def view_recipients_command(update: Update, context: CallbackContext):
    context.user_data['state'] = "viewing_recipients"
    await update.message.reply_text(i18n.t('enter_capsule_id_for_recipients'))

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
        await update.message.reply_text(i18n.t('invalid_capsule_id') + "\n\n" + i18n.t('hint_enter_number'))
    except Exception as e:
        logger.error(f"Ошибка при получении получателей: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

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

async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text in ["📦 Создать капсулу", "📂 Просмотреть капсулы", "👤 Добавить получателя", "📨 Отправить капсулу", "🗑 Удалить капсулу", "✏️ Редактировать капсулу", "👥 Просмотреть получателей", "❓ Помощь", "📅 Установить дату отправки", "💸 Поддержать автора"]:
        commands = {"📦 Создать капсулу": create_capsule_command, "📂 Просмотреть капсулы": view_capsules_command, "👤 Добавить получателя": add_recipient_command, "📨 Отправить капсулу": send_capsule_command, "🗑 Удалить капсулу": delete_capsule_command, "✏️ Редактировать капсулу": edit_capsule_command, "👥 Просмотреть получателей": view_recipients_command, "❓ Помощь": help_command, "📅 Установить дату отправки": select_send_date, "💸 Поддержать автора": support_author}
        await commands[text](update, context)
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
    elif context.user_data.get('state') == "entering_custom_time":
        await handle_custom_time(update, context)
    elif text:
        capsule_id = context.user_data.get('current_capsule')
        if not capsule_id:
            await update.message.reply_text(i18n.t('create_capsule_first'))
            return
        capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
        capsule_content['text'].append(text)
        context.user_data['capsule_content'] = capsule_content
        save_capsule_content(context, capsule_id)
        await update.message.reply_text(i18n.t('text_added'))

async def handle_photo(update: Update, context: CallbackContext):
    capsule_id = context.user_data.get('current_capsule')
    if not capsule_id:
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
    photo_file_id = update.message.photo[-1].file_id
    capsule_content['photos'].append(photo_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, capsule_id)
    await update.message.reply_text(i18n.t('photo_added'))

async def handle_video(update: Update, context: CallbackContext):
    capsule_id = context.user_data.get('current_capsule')
    if not capsule_id:
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
    video_file_id = update.message.video.file_id
    capsule_content['videos'].append(video_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, capsule_id)
    await update.message.reply_text(i18n.t('video_added'))

async def handle_audio(update: Update, context: CallbackContext):
    capsule_id = context.user_data.get('current_capsule')
    if not capsule_id:
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
    audio_file_id = update.message.audio.file_id
    capsule_content['audios'].append(audio_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, capsule_id)
    await update.message.reply_text(i18n.t('audio_added'))

async def handle_document(update: Update, context: CallbackContext):
    capsule_id = context.user_data.get('current_capsule')
    if not capsule_id:
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
    document_file_id = update.message.document.file_id
    capsule_content['documents'].append(document_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, capsule_id)
    await update.message.reply_text(i18n.t('document_added'))

async def handle_sticker(update: Update, context: CallbackContext):
    capsule_id = context.user_data.get('current_capsule')
    if not capsule_id:
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
    sticker_file_id = update.message.sticker.file_id
    capsule_content['stickers'].append(sticker_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, capsule_id)
    await update.message.reply_text(i18n.t('sticker_added'))

async def handle_voice(update: Update, context: CallbackContext):
    capsule_id = context.user_data.get('current_capsule')
    if not capsule_id:
        await update.message.reply_text(i18n.t('create_capsule_first'))
        return
    capsule_content = context.user_data.get('capsule_content', {"text": [], "photos": [], "videos": [], "audios": [], "documents": [], "stickers": [], "voices": []})
    voice_file_id = update.message.voice.file_id
    capsule_content['voices'].append(voice_file_id)
    context.user_data['capsule_content'] = capsule_content
    save_capsule_content(context, capsule_id)
    await update.message.reply_text(i18n.t('voice_added'))

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
                [InlineKeyboardButton(i18n.t('through_day'), callback_data='day'),
                 InlineKeyboardButton(i18n.t('through_week'), callback_data='week')],
                [InlineKeyboardButton(i18n.t('through_month'), callback_data='month'),
                 InlineKeyboardButton(i18n.t('through_year'), callback_data='year')],
                [InlineKeyboardButton(i18n.t('select_date'), callback_data='calendar')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(i18n.t('choose_send_date'), reply_markup=reply_markup)
            context.user_data['state'] = "selecting_send_date"
    except ValueError:
        await update.message.reply_text(i18n.t('invalid_capsule_id') + "\n\n" + i18n.t('hint_enter_number'))
    except Exception as e:
        logger.error(f"Ошибка при выборе капсулы: {e}")
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))

async def handle_date_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    now = datetime.now()
    if query.data == 'day':
        send_date = now + timedelta(days=1)
    elif query.data == 'week':
        send_date = now + timedelta(weeks=1)
    elif query.data == 'month':
        send_date = now + timedelta(days=30)
    elif query.data == 'year':
        send_date = now + timedelta(days=365)
    elif query.data == 'calendar':
        year = now.year
        keyboard = [[InlineKeyboardButton(str(m), callback_data=f"month:{year}:{m}") for m in range(1, 7)],
                    [InlineKeyboardButton(str(m), callback_data=f"month:{year}:{m}") for m in range(7, 13)],
                    [InlineKeyboardButton("<<", callback_data=f"year:{year-1}"), InlineKeyboardButton(">>", callback_data=f"year:{year+1}")]]
        await query.edit_message_text(i18n.t('select_month'), reply_markup=InlineKeyboardMarkup(keyboard))
        return
    context.user_data['send_date'] = get_utc_time(send_date)
    await query.edit_message_text(i18n.t('date_selected', date=send_date))
    await save_send_date(update, context)

async def handle_calendar(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(':')
    if data[0] == 'year':
        year = int(data[1])
        keyboard = [[InlineKeyboardButton(str(m), callback_data=f"month:{year}:{m}") for m in range(1, 7)],
                    [InlineKeyboardButton(str(m), callback_data=f"month:{year}:{m}") for m in range(7, 13)],
                    [InlineKeyboardButton("<<", callback_data=f"year:{year-1}"), InlineKeyboardButton(">>", callback_data=f"year:{year+1}")]]
        await query.edit_message_text(i18n.t('select_month'), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data[0] == 'month':
        year, month = int(data[1]), int(data[2])
        days_in_month = (datetime(year, month % 12 + 1, 1) - timedelta(days=1)).day if month == 12 else (datetime(year, month + 1, 1) - timedelta(days=1)).day
        keyboard = [[]]
        for day in range(1, days_in_month + 1):
            if len(keyboard[-1]) == 7: keyboard.append([])
            keyboard[-1].append(InlineKeyboardButton(str(day), callback_data=f"day:{year}:{month}:{day}"))
        keyboard.append([InlineKeyboardButton("Back", callback_data=f"year:{year}")])
        await query.edit_message_text(i18n.t('select_day'), reply_markup=InlineKeyboardMarkup(keyboard))
    elif data[0] == 'day':
        year, month, day = int(data[1]), int(data[2]), int(data[3])
        context.user_data['selected_date'] = datetime(year, month, day)
        keyboard = [
            [InlineKeyboardButton("09:00", callback_data='09:00'), InlineKeyboardButton("12:00", callback_data='12:00')],
            [InlineKeyboardButton("15:00", callback_data='15:00'), InlineKeyboardButton("18:00", callback_data='18:00')],
            [InlineKeyboardButton(i18n.t('custom_time'), callback_data='custom_time')]
        ]
        await query.edit_message_text(i18n.t('select_time'), reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_time_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    time_str = query.data
    selected_date = context.user_data.get('selected_date')
    if time_str == 'custom_time':
        await query.edit_message_text(i18n.t('enter_custom_time'))
        context.user_data['state'] = "entering_custom_time"
    else:
        dt = datetime.strptime(f"{selected_date.strftime('%Y-%m-%d')} {time_str}", "%Y-%m-%d %H:%M")
        context.user_data['send_date'] = get_utc_time(dt)
        await query.edit_message_text(i18n.t('date_selected', date=dt))
        await save_send_date(update, context)

async def handle_custom_time(update: Update, context: CallbackContext):
    if context.user_data.get('state') == "entering_custom_time":
        try:
            time_str = update.message.text.strip()
            selected_date = context.user_data.get('selected_date')
            dt = datetime.strptime(f"{selected_date.strftime('%Y-%m-%d')} {time_str}", "%Y-%m-%d %H:%M")
            context.user_data['send_date'] = get_utc_time(dt)
            await update.message.reply_text(i18n.t('date_selected', date=dt))
            await save_send_date(update, context)
            context.user_data['state'] = "idle"
        except ValueError:
            await update.message.reply_text(i18n.t('invalid_time_format'))

async def save_send_date(update: Update, context: CallbackContext):
    send_date = context.user_data.get('send_date')
    capsule_id = context.user_data.get('selected_capsule_id')
    if not send_date or not capsule_id:
        await update.message.reply_text(i18n.t('error_general') + "\n\n" + i18n.t('hint_try_again'))
        return
    job_id = f"capsule_{capsule_id}"
    if scheduler.get_job(job_id): scheduler.remove_job(job_id)
    edit_capsule(capsule_id, scheduled_at=send_date)
    send_capsule_task.apply_async((capsule_id,), eta=send_date)
    await update.message.reply_text(i18n.t('date_set', date=send_date))
    context.user_data['state'] = "idle"

async def support_author(update: Update, context: CallbackContext):
    await update.message.reply_text(i18n.t('support_author', url="https://www.donationalerts.com/r/lunarisqqq"))

async def change_language(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Русский", callback_data='ru'), InlineKeyboardButton("English", callback_data='en')]]
    await update.message.reply_text("Выберите язык / Choose language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    i18n.set('locale', query.data)
    await query.edit_message_text(i18n.t('language_changed'))
    await start(update, context)

def save_capsule_content(context: CallbackContext, capsule_id: int):
    content = context.user_data.get('capsule_content', {})
    json_str = json.dumps(content, ensure_ascii=False)
    encrypted = encrypt_data_aes(json_str, ENCRYPTION_KEY_BYTES)
    update_data("capsules", {"id": capsule_id}, {"content": encrypted})

async def post_init(application):
    capsules = fetch_data("capsules")
    now = datetime.now(pytz.utc)
    for capsule in capsules:
        if capsule.get('scheduled_at'):
            scheduled_at = datetime.fromisoformat(capsule['scheduled_at']).replace(tzinfo=pytz.utc)
            if scheduled_at > now:
                scheduler.add_job(send_capsule_task, 'date', run_date=scheduled_at, args=[capsule['id']], id=f"capsule_{capsule['id']}", timezone=pytz.utc)

async def check_bot_permissions(context: CallbackContext):
    try:
        me = await context.bot.get_me()
        logger.info(f"Бот запущен как @{me.username}")
    except Exception as e:
        logger.error(f"Ошибка аутентификации бота: {e}")
        sys.exit(1)

async def main():
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
    application.add_handler(CommandHandler("lang", change_language))

    application.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r'^(day|week|month|year|calendar)$'))
    application.add_handler(CallbackQueryHandler(handle_calendar, pattern=r'^(year|month|day):'))
    application.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r'^(09:00|12:00|15:00|18:00|custom_time)$'))
    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r'^(ru|en)$'))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d{2}:\d{2}$'), handle_custom_time))
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
