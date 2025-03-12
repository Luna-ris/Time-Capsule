from celery_config import celery_app
from telegram import Bot
import json
import logging
from datetime import datetime
import pytz
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from supabase import create_client, Client
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Преобразование ключа шифрования из строки в байты
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

def get_capsule_recipients(capsule_id: int):
    return fetch_data("recipients", {"capsule_id": capsule_id})

def get_chat_id(username: str):
    response = fetch_data("users", {"username": username})
    if response:
        return response[0]['chat_id']
    else:
        logger.error(f"Пользователь {username} не найден.")
        return None

@celery_app.task
def send_capsule_task(capsule_id: int):
    try:
        logger.info(f"Начало обработки капсулы {capsule_id}")

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
            recipient_username = recipient['recipient_username']
            chat_id = get_chat_id(recipient_username)
            if chat_id:
                try:
                    bot.send_message(
                        chat_id=chat_id,
                        text=
                        f"🎁 Вам пришла капсула времени от @{recipient_username}!"
                    )
                    for text in content.get('text', []):
                        bot.send_message(chat_id=chat_id, text=text)
                    for sticker in content.get('stickers', []):
                        bot.send_sticker(chat_id=chat_id, sticker=sticker)
                    for photo in content.get('photos', []):
                        bot.send_photo(chat_id=chat_id, photo=photo)
                    for document in content.get('documents', []):
                        bot.send_document(chat_id=chat_id, document=document)
                    for voice in content.get('voices', []):
                        bot.send_voice(chat_id=chat_id, voice=voice)
                    for video in content.get('videos', []):
                        bot.send_video(chat_id=chat_id, video=video)
                    for audio in content.get('audios', []):
                        bot.send_audio(chat_id=chat_id, audio=audio)

                    bot.send_message(
                        chat_id=chat_id,
                        text=
                        f"🎁 Вам пришла капсула времени от @{recipient_username}!"
                    )
                except Exception as e:
                    logger.error(
                        f"Не удалось отправить капсулу получателю @{recipient_username}: {str(e)}"
                    )
            else:
                logger.error(
                    f"Получатель @{recipient_username} не зарегистрирован в боте."
                )

        logger.info(f"Капсула {capsule_id} успешно обработана")
    except Exception as e:
        logger.error(f"Задача не выполнена: {str(e)}")
        raise
