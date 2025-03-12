# capsule_job.py

import json
from datetime import datetime
import pytz
from supabase import create_client, Client
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Инициализация клиентов
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not ENCRYPTION_KEY:
    raise ValueError("Отсутствуют необходимые переменные окружения.")

# Преобразование ключа шифрования из строки в байты
ENCRYPTION_KEY_BYTES = bytes.fromhex(ENCRYPTION_KEY)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def get_capsule_recipients(capsule_id: int):
    return fetch_data("recipients", {"capsule_id": capsule_id})

async def send_capsule_job(capsule_id: int, update: Update,
                           context: CallbackContext):
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule:
        raise ValueError(f"Капсула {capsule_id} не найдена")

    encrypted_content = capsule[0]['content']
    decrypted = decrypt_data_aes(encrypted_content, ENCRYPTION_KEY_BYTES)
    content = json.loads(decrypted)

    recipients = get_capsule_recipients(capsule_id)
    if not recipients:
        raise ValueError(f"Нет получателей для капсулы {capsule_id}")

    for recipient in recipients:
        recipient_username = recipient['recipient_username']
        chat_id = get_chat_id(recipient_username)
        if chat_id:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=
                    f"🎁 Вам пришла капсула времени от @{update.message.from_user.username}!"
                )
                for text in content.get('text', []):
                    await context.bot.send_message(chat_id=chat_id, text=text)
                for sticker in content.get('stickers', []):
                    await context.bot.send_sticker(chat_id=chat_id,
                                                   sticker=sticker)
                for photo in content.get('photos', []):
                    await context.bot.send_photo(chat_id=chat_id, photo=photo)
                for document in content.get('documents', []):
                    await context.bot.send_document(chat_id=chat_id,
                                                    document=document)
                for voice in content.get('voices', []):
                    await context.bot.send_voice(chat_id=chat_id, voice=voice)
                for video in content.get('videos', []):
                    await context.bot.send_video(chat_id=chat_id, video=video)
                for audio in content.get('audios', []):
                    await context.bot.send_audio(chat_id=chat_id, audio=audio)
            except Exception as e:
                raise ValueError(
                    f"Не удалось отправить капсулу получателю @{recipient_username}: {str(e)}"
                )
        else:
            raise ValueError(
                f"Получатель @{recipient_username} не зарегистрирован в боте.")
