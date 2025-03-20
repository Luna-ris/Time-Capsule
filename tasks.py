from celery import Celery
import os
import asyncio
import json
from datetime import datetime
from typing import List, Optional
import pytz
from telegram import Bot
from telegram.ext import Application
from config import logger, TELEGRAM_TOKEN, ENCRYPTION_KEY_BYTES, celery_app
from localization import t
from database import fetch_data, delete_capsule, get_capsule_recipients, get_chat_id, generate_unique_capsule_number
from crypto import decrypt_data_aes

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
            bot = Application.builder().token(TELEGRAM_TOKEN).build()
            await bot.initialize()
            creator = fetch_data("users", {"id": capsule[0]['creator_id']})
            sender_username = creator[0]['username'] if creator else "Unknown"
            for recipient in recipients:
                chat_id = get_chat_id(recipient['recipient_username'])
                if chat_id:
                    await bot.bot.send_message(
                        chat_id=chat_id,
                        text=t('capsule_received', sender=sender_username)
                    )
                    for item in content.get('text', []):
                        await bot.bot.send_message(chat_id, item)
                    for item in content.get('stickers', []):
                        await bot.bot.send_sticker(chat_id, item)
                    for item in content.get('photos', []):
                        await bot.bot.send_photo(chat_id, item)
                    for item in content.get('documents', []):
                        await bot.bot.send_document(chat_id, item)
                    for item in content.get('voices', []):
                        await bot.bot.send_voice(chat_id, item)
                    for item in content.get('videos', []):
                        await bot.bot.send_video(chat_id, item)
                    for item in content.get('audios', []):
                        await bot.bot.send_audio(chat_id, item)
                else:
                    logger.warning(f"Получатель {recipient['recipient_username']} не зарегистрирован")
            logger.info(f"Капсула {capsule_id} успешно отправлена")
            delete_capsule(capsule_id)
        except Exception as e:
            logger.error(f"Ошибка в задаче отправки капсулы {capsule_id}: {e}")

    asyncio.run(send_async())

