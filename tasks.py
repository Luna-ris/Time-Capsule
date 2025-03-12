from celery_config import celery_app
from telegram import Bot
import json
import logging
from datetime import datetime
import pytz
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from supabase import create_client, Client
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

def fetch_data(table: str, query: dict = {}):
    response = supabase.table(table).select("*")
    for key, value in query.items():
        response = response.eq(key, value)
    response = response.execute()
    return response.data

def decrypt_data_aes(encrypted_hex: str, key: bytes) -> str:
    data = bytes.fromhex(encrypted_hex)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()
    return unpadded.decode('utf-8')

def get_capsule_recipients(capsule_id: int):
    return fetch_data("recipients", {"capsule_id": capsule_id})

def get_chat_id(username: str):
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

@celery_app.task
def send_capsule_task(capsule_id: int):
    try:
        capsule = fetch_data("capsules", {"id": capsule_id})
        if not capsule:
            logger.error(f"Капсула {capsule_id} не найдена")
            return
        encrypted_content = capsule[0]['content']
        decrypted = decrypt_data_aes(encrypted_content, ENCRYPTION_KEY_BYTES)
        content = json.loads(decrypted)
        recipients = get_capsule_recipients(capsule_id)
        if not recipients:
            logger.error(f"Нет получателей для капсулы {capsule_id}")
            return
        for recipient in recipients:
            chat_id = get_chat_id(recipient['recipient_username'])
            if chat_id:
                bot.send_message(chat_id=chat_id, text=f"🎁 Вам пришла капсула времени от @{recipient['recipient_username']}!")
                for item in content.get('text', []): bot.send_message(chat_id=chat_id, text=item)
                for item in content.get('photos', []): bot.send_photo(chat_id=chat_id, photo=item)
                for item in content.get('videos', []): bot.send_video(chat_id=chat_id, video=item)
                for item in content.get('audios', []): bot.send_audio(chat_id=chat_id, audio=item)
                for item in content.get('documents', []): bot.send_document(chat_id=chat_id, document=item)
                for item in content.get('stickers', []): bot.send_sticker(chat_id=chat_id, sticker=item)
                for item in content.get('voices', []): bot.send_voice(chat_id=chat_id, voice=item)
            else:
                logger.error(f"Получатель @{recipient['recipient_username']} не зарегистрирован.")
        logger.info(f"Капсула {capsule_id} успешно отправлена")
    except Exception as e:
        logger.error(f"Ошибка при отправке капсулы {capsule_id}: {e}")
