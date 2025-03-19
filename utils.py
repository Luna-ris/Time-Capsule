import json
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import CallbackContext, Application
from config import logger
from localization import t
from database import fetch_data

async def check_capsule_ownership(update: Update, capsule_id: int, query=None) -> bool:
    """Проверка владения капсулой."""
    user = fetch_data("users", {"telegram_id": update.effective_user.id})
    if not user:
        if query:
            await query.edit_message_text(t('not_registered'))
        else:
            await update.message.reply_text(t('not_registered'))
        return False
    capsule = fetch_data("capsules", {"id": capsule_id})
    if not capsule or capsule[0]['creator_id'] != user[0]['id']:
        if query:
            await query.edit_message_text(t('not_your_capsule'))
        else:
            await update.message.reply_text(t('not_your_capsule'))
        return False
    return True

def save_capsule_content(context: CallbackContext, capsule_id: int):
    """Сохранение содержимого капсулы."""
    content = context.user_data.get('capsule_content', {})
    json_str = json.dumps(content, ensure_ascii=False)
    from crypto import encrypt_data_aes
    encrypted = encrypt_data_aes(json_str)
    from database import update_data
    update_data("capsules", {"id": capsule_id}, {"content": encrypted})

def convert_to_utc(local_time_str: str, timezone: str = 'Europe/Moscow') -> datetime:
    """Конвертация местного времени в UTC."""
    local_tz = pytz.timezone(timezone)
    local_time = datetime.strptime(local_time_str, "%d.%m.%Y %H:%M:%S")
    local_time = local_tz.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    return utc_time

async def post_init(application: Application):
    """Инициализация задач после запуска бота."""
    logger.info("Начало инициализации задач")
    try:
        capsules = fetch_data("capsules")
        logger.info(f"Найдено {len(capsules)} капсул в базе данных")

        now = datetime.now(pytz.utc)
        logger.info(f"Текущее время UTC: {now}")

        from config import celery_app
        for capsule in capsules:
            if capsule.get('scheduled_at'):
                scheduled_at = datetime.fromisoformat(capsule['scheduled_at']).replace(tzinfo=pytz.utc)
                logger.info(f"Обработка капсулы {capsule['id']}, запланированной на {scheduled_at}")
                if scheduled_at > now:
                    logger.info(f"Добавление задачи для капсулы {capsule['id']} в Celery")
                    celery_app.send_task(
                        'tasks.send_capsule_task',
                        args=[capsule['id']],
                        eta=scheduled_at
                    )
                    logger.info(f"Задача для капсулы {capsule['id']} запланирована на {scheduled_at}")
                else:
                    logger.info(f"Капсула {capsule['id']} просрочена (scheduled_at: {scheduled_at})")
            else:
                logger.info(f"Капсула {capsule['id']} не имеет scheduled_at")
        logger.info("Инициализация задач завершена")
    except Exception as e:
        logger.error(f"Не удалось инициализировать задачи: {e}")

async def check_bot_permissions(context: CallbackContext):
    """Проверка прав бота."""
    try:
        me = await context.bot.get_me()
        logger.info(f"Бот запущен как @{me.username}")
        logger.info("Проверка прав бота завершена")
    except Exception as e:
        logger.error(f"Ошибка при проверке прав бота: {e}")
