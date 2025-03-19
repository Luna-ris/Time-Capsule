import json
from datetime import datetime

import pytz
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram import Update
from telegram.ext import CallbackContext
import os

# Загрузка переменных окружения
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def decrypt_data_aes(encrypted_hex: str, key: bytes) -> str:
    """Дешифрование данных с помощью AES."""
    data = bytes.fromhex(encrypted_hex)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()
    return unpadded.decode('utf-8')

def fetch_data(table: str, query: dict = {}):
    """Получение данных из Supabase."""
    response = supabase.table(table).select("*")
    for key, value in query.items():
        response = response.eq(key, value)
    return response.execute().data

def get_capsule_recipients(capsule_id: int):
    """Получение списка получателей капсулы."""
    return fetch_data("recipients", {"capsule_id": capsule_id})

def get_chat_id(username: str):
    """Получение chat_id по имени пользователя."""
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

async def send_capsule_job(application, capsule_id: int, update: Update):
    """Отправка капсулы всем получателям."""
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule:
        raise ValueError(f"Капсула {capsule_id} не найдена")

    content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
    recipients = get_capsule_recipients(capsule_id)
    if not recipients:
        raise ValueError(f"Нет получателей для капсулы {capsule_id}")

    for recipient in recipients:
        chat_id = get_chat_id(recipient['recipient_username'])
        if chat_id:
            await application.bot.send_message(
                chat_id=chat_id,
                text=f"🎁 Вам пришла капсула времени от @{update.message.from_user.username}!"
            )
            for item in content.get('text', []):
                await application.bot.send_message(chat_id, item)
            for item in content.get('stickers', []):
                await application.bot.send_sticker(chat_id, item)
            for item in content.get('photos', []):
                await application.bot.send_photo(chat_id, item)
            for item in content.get('documents', []):
                await application.bot.send_document(chat_id, item)
            for item in content.get('voices', []):
                await application.bot.send_voice(chat_id, item)
            for item in content.get('videos', []):
                await application.bot.send_video(chat_id, item)
            for item in content.get('audios', []):
                await application.bot.send_audio(chat_id, item)
