import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

import pytz
from celery_config import celery_app
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
from supabase import create_client, Client
from telegram import Bot
import os
from config import SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN, ENCRYPTION_KEY_BYTES, REDIS_URL

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_data(table: str, query: dict = {}) -> List[dict]:
    """Получение данных из Supabase."""
    response = supabase.table(table).select("*")
    for key, value in query.items():
        response = response.eq(key, value)
    return response.execute().data

def delete_data(table: str, query: dict) -> List[dict]:
    """Удаление данных из Supabase."""
    response = supabase.table(table).delete()
    for key, value in query.items():
        response = response.eq(key, value)
    return response.execute().data

def decrypt_data_aes(encrypted_hex: str, key: bytes) -> str:
    """Дешифрование данных с помощью AES."""
    data = bytes.fromhex(encrypted_hex)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(decrypted) + unpadder.finalize().decode('utf-8')

def get_capsule_recipients(capsule_id: int) -> List[dict]:
    """Получение списка получателей капсулы."""
    return fetch_data("recipients", {"capsule_id": capsule_id})

def get_chat_id(username: str) -> Optional[int]:
    """Получение chat_id по имени пользователя."""
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

def delete_capsule(capsule_id: int):
    """Удаление капсулы и связанных данных."""
    delete_data("recipients", {"capsule_id": capsule_id})
    delete_data("capsules", {"id": capsule_id})

@celery_app.task(name='main.send_capsule_task')
def send_capsule_task(capsule_id: int):
    """Задача Celery для отправки капсулы."""
    async def send_async():
        try:
            logger.info(f"Начинаю отправку капсулы {capsule_id}")
            capsule = fetch_data("capsules", {"id": capsule_id})
            if not capsule:
                logger.error(f"Капсула {capsule_id} не найдена")
                return

            content = json.loads(decrypt_data_aes(capsule[0]['content'], ENCRYPTION_KEY_BYTES))
            recipients = get_capsule_recipients(capsule_id)
            if not recipients:
                logger.error(f"Нет получателей для капсулы {capsule_id}")
                return

            bot = Bot(token=TELEGRAM_TOKEN)
            creator = fetch_data("users", {"id": capsule[0]['creator_id']})
            sender_username = creator[0]['username'] if creator else "Unknown"

            for recipient in recipients:
                chat_id = get_chat_id(recipient['recipient_username'])
                if chat_id:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"🎉 Вы получили капсулу времени от @{sender_username}!\nВот её содержимое:"
                    )
                    for item in content.get('text', []):
                        await bot.send_message(chat_id, item)
                    for item in content.get('stickers', []):
                        await bot.send_sticker(chat_id, item)
                    for item in content.get('photos', []):
                        await bot.send_photo(chat_id, item)
                    for item in content.get('documents', []):
                        await bot.send_document(chat_id, item)
                    for item in content.get('voices', []):
                        await bot.send_voice(chat_id, item)
                    for item in content.get('videos', []):
                        await bot.send_video(chat_id, item)
                    for item in content.get('audios', []):
                        await bot.send_audio(chat_id, item)
                    logger.info(f"Капсула {capsule_id} отправлена @{recipient['recipient_username']}")
                else:
                    logger.warning(f"Получатель @{recipient['recipient_username']} не зарегистрирован")
            logger.info(f"Капсула {capsule_id} успешно отправлена")
            delete_capsule(capsule_id)
        except Exception as e:
            logger.error(f"Ошибка в задаче отправки капсулы {capsule_id}: {e}")

    asyncio.run(send_async())

async def post_init(application):
    """Функция для инициализации приложения."""
    pass
