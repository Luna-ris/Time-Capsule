from celery import Celery
import asyncio
from datetime import datetime
import pytz
from telegram import Bot
from config import logger, TELEGRAM_TOKEN
from database import fetch_data, delete_capsule, get_capsule_recipients, get_chat_id
from crypto import decrypt_data_aes

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

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

            content = json.loads(decrypt_data_aes(capsule[0]['content']))
            recipients = get_capsule_recipients(capsule_id)
            if not recipients:
                logger.error(f"Нет получателей для капсулы {capsule_id}")
                return

            bot = Bot(token=TELEGRAM_TOKEN)
            for recipient in recipients:
                chat_id = get_chat_id(recipient['recipient_username'])
                if chat_id:
                    await bot.send_message(chat_id=chat_id, text=t('capsule_received'))
                    for item_type in ['text', 'stickers', 'photos', 'documents', 'voices', 'videos', 'audios']:
                        for item in content.get(item_type, []):
                            send_method = getattr(bot, f"send_{item_type[:-1]}")
                            await send_method(chat_id, item)
                    logger.info(f"Капсула {capsule_id} отправлена @{recipient['recipient_username']}")
                else:
                    logger.warning(f"Получатель @{recipient['recipient_username']} не зарегистрирован")

            logger.info(f"Капсула {capsule_id} успешно отправлена")
            delete_capsule(capsule_id)
        except Exception as e:
            logger.error(f"Ошибка в задаче отправки капсулы {capsule_id}: {e}")

    asyncio.run(send_async())
