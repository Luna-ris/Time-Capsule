import json
from datetime import datetime
from telegram.ext import Application, CallbackContext
from telegram import Update
from config import logger, celery_app
from database import (
    fetch_data,
    create_capsule,
    edit_capsule,
    delete_capsule,
    generate_unique_capsule_number,
    update_data
)
from localization import t
import pytz

CREATING_CAPSULE_TITLE = "creating_capsule_title"
CREATING_CAPSULE_CONTENT = "creating_capsule_content"
CREATING_CAPSULE_RECIPIENTS = "creating_capsule_recipients"
CREATING_CAPSULE_DATE = "creating_capsule_date"
SELECTING_CAPSULE = "selecting_capsule"
SELECTING_CAPSULE_FOR_RECIPIENTS = "selecting_capsule_for_recipients"

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
    from crypto import encrypt_data_aes
    content = context.user_data.get('capsule_content', {})
    json_str = json.dumps(content, ensure_ascii=False)
    encrypted = encrypt_data_aes(json_str)
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

        for capsule in capsules:
            if capsule.get('scheduled_at'):
                scheduled_at = datetime.fromisoformat(capsule['scheduled_at']).replace(tzinfo=pytz.utc)
                logger.info(f"Обработка капсулы {capsule['id']}, запланированной на {scheduled_at}")

                if scheduled_at > now:
                    logger.info(f"Добавление задачи для капсулы {capsule['id']} в Celery")
                    celery_app.send_task(
                        'main.send_capsule_task',
                        args=[capsule['id']],
                        eta=scheduled_at
                    )
                    logger.info(f"Задача для капсулы {capsule['id']} запланирована на {scheduled_at}")
        logger.info("Инициализация задач завершена")
    except Exception as e:
        logger.error(f"Не удалось инициализировать задачи: {e}")

async def check_bot_permissions(context: CallbackContext):
    """Проверка прав бота."""
    me = await context.bot.get_me()
    logger.info(f"Бот запущен как @{me.username}")

async def save_send_date(update: Update, context: CallbackContext, send_date: datetime, is_message: bool = False):
    try:
        capsule_id = context.user_data.get('selected_capsule_id') or context.user_data.get('current_capsule')
        if not capsule_id:
            if is_message:
                await update.message.reply_text(t('error_general'))
            else:
                await update.callback_query.edit_message_text(t('error_general'))
            return
        
        send_date = send_date.astimezone(pytz.utc)
        edit_capsule(capsule_id, scheduled_at=send_date)
        
        # Проверка существования задачи Celery
        from celery.result import AsyncResult
        task_id = f"send_capsule_task_{capsule_id}"
        existing_task = AsyncResult(task_id, app=celery_app)
        
        if existing_task.state in ['PENDING', 'STARTED']:
            logger.info(f"Задача для капсулы {capsule_id} уже существует")
        else:
            celery_app.send_task(
                'main.send_capsule_task',
                args=[capsule_id],
                eta=send_date,
                task_id=task_id
            )
            logger.info(f"Задача для капсулы {capsule_id} запланирована на {send_date}")
        
        message_text = t('date_set', date=send_date.astimezone(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M'))
        if is_message:
            await update.message.reply_text(message_text)
        else:
            await update.callback_query.edit_message_text(message_text)
            
        if context.user_data.get('state') != CREATING_CAPSULE_DATE:
            context.user_data['state'] = "idle"
    except Exception as e:
        logger.error(f"Ошибка при установке даты для капсулы {capsule_id}: {e}")
        if is_message:
            await update.message.reply_text(t('error_general'))
        else:
            await update.callback_query.edit_message_text(t('error_general'))
