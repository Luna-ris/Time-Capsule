import asyncio
import json
from datetime import datetime
from typing import List
import pytz
from config import logger, TELEGRAM_TOKEN
from localization import t
from database import fetch_data, get_capsule_recipients, get_chat_id, delete_capsule
from crypto import decrypt_data_aes
from telegram.ext import Application

@celery_app.task(name='tasks.send_capsule_task')
def send_capsule_task(capsule_id: int):
    async def send_async():
        try:
            capsule = fetch_data("capsules", {"id": capsule_id})
            if not capsule:
                logger.error(f"Капсула {capsule_id} не найдена")
                return
            
            content = json.loads(decrypt_data_aes(capsule[0]['content']))
            recipients = get_capsule_recipients(capsule_id)
            if not recipients:
                logger.error(f"Нет получателей для капсулы {capsule_id}")
                return
            
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            await application.initialize()
            
            for recipient in recipients:
                chat_id = get_chat_id(recipient['recipient_username'])
                if chat_id:
                    bot = application.bot
                    await bot.send_message(chat_id=chat_id, text=t('capsule_received'))
                    
                    for item_type in ['text', 'stickers', 'photos', 'documents', 
                                     'voices', 'videos', 'audios']:
                        for item in content.get(item_type, []):
                            send_method = getattr(bot, f"send_{item_type[:-1]}")
                            await send_method(chat_id, item)
            
            delete_capsule(capsule_id)
            await application.shutdown()
        except Exception as e:
            logger.error(f"Ошибка в задаче отправки капсулы {capsule_id}: {e}")
    
    asyncio.run(send_async())
