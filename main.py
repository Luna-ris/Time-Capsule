import logging
import nest_asyncio
import os
import sys
import asyncio
from pathlib import Path
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from config import TELEGRAM_TOKEN
from handlers import (
    start, help_command, create_capsule_command, add_recipient_command, view_capsules_command,
    send_capsule_command, delete_capsule_command, edit_capsule_command, view_recipients_command,
    select_send_date, support_author, change_language, handle_language_selection, handle_capsule_selection,
    handle_date_buttons, handle_delete_confirmation, handle_text, handle_select_send_date, handle_create_capsule_steps,
    handle_recipient, handle_send_capsule_logic, handle_edit_capsule_content, handle_view_recipients_logic,
    handle_photo, handle_media, handle_video, handle_audio, handle_document, handle_sticker, handle_voice
)
from tasks import post_init
from celery_config import celery_app

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к файлу блокировки
LOCK_FILE = Path("/tmp/timecapsulebot.lock")

def acquire_lock():
    """Проверка и установка блокировки для предотвращения запуска нескольких экземпляров."""
    if LOCK_FILE.exists():
        logger.error("Другой экземпляр бота уже запущен. Завершаю работу.")
        sys.exit(1)
    with LOCK_FILE.open("w") as f:
        f.write(str(os.getpid()))
    logger.info("Блокировка установлена успешно.")

def release_lock():
    """Удаление файла блокировки при завершении работы."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    logger.info("Блокировка снята.")

def start_celery_worker():
    """Запуск Celery-воркера в отдельном потоке."""
    logger.info("Запуск Celery-воркера...")
    # Запускаем воркер с использованием argv для передачи параметров
    celery_app.worker_main(argv=["worker", "--loglevel=info", "--pool=eventlet"])
    logger.info("Celery-воркер завершен.")

# Инициализация приложения Telegram
app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

# Регистрация обработчиков
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("create_capsule", create_capsule_command))
app.add_handler(CommandHandler("add_recipient", add_recipient_command))
app.add_handler(CommandHandler("view_capsules", view_capsules_command))
app.add_handler(CommandHandler("send_capsule", send_capsule_command))
app.add_handler(CommandHandler("delete_capsule", delete_capsule_command))
app.add_handler(CommandHandler("edit_capsule", edit_capsule_command))
app.add_handler(CommandHandler("view_recipients", view_recipients_command))
app.add_handler(CommandHandler("select_send_date", select_send_date))
app.add_handler(CommandHandler("support_author", support_author))
app.add_handler(CommandHandler("change_language", change_language))

app.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r"^(ru|en|es|fr|de)$"))
app.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r"^(week|month|custom)$"))
app.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern=r"^(confirm_delete|cancel_delete)$"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

async def run_bot_and_worker():
    """Запуск бота и воркера в одном процессе."""
    # Установка блокировки
    acquire_lock()
    
    try:
        # Запуск Celery-воркера в отдельном потоке
        celery_thread = Thread(target=start_celery_worker, daemon=True)
        celery_thread.start()
        logger.info("Celery-воркер запущен в фоновом потоке.")

        # Применяем nest_asyncio для совместимости с асинхронным кодом
        nest_asyncio.apply()

        # Запуск Telegram-бота в режиме polling
        await app.initialize()
        await app.start()
        logger.info("Telegram-бот запущен.")
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=10)

        # Бесконечный цикл для удержания процесса
        while True:
            await asyncio.sleep(3600)  # Спим 1 час, чтобы не нагружать процессор

    except Exception as e:
        logger.error(f"Ошибка при запуске бота или воркера: {e}")
        raise
    finally:
        # Остановка бота и снятие блокировки
        await app.stop()
        await app.shutdown()
        release_lock()

if __name__ == "__main__":
    # Запуск асинхронной функции
    asyncio.run(run_bot_and_worker())import logging
import nest_asyncio
import os
import sys
import asyncio
from pathlib import Path
from threading import Thread
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from config import TELEGRAM_TOKEN
from handlers import (
    start, help_command, create_capsule_command, add_recipient_command, view_capsules_command,
    send_capsule_command, delete_capsule_command, edit_capsule_command, view_recipients_command,
    select_send_date, support_author, change_language, handle_language_selection, handle_capsule_selection,
    handle_date_buttons, handle_delete_confirmation, handle_text, handle_select_send_date, handle_create_capsule_steps,
    handle_recipient, handle_send_capsule_logic, handle_edit_capsule_content, handle_view_recipients_logic,
    handle_photo, handle_media, handle_video, handle_audio, handle_document, handle_sticker, handle_voice
)
from tasks import post_init
from celery_config import celery_app

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к файлу блокировки
LOCK_FILE = Path("/tmp/timecapsulebot.lock")

def acquire_lock():
    """Проверка и установка блокировки для предотвращения запуска нескольких экземпляров."""
    if LOCK_FILE.exists():
        logger.error("Другой экземпляр бота уже запущен. Завершаю работу.")
        sys.exit(1)
    with LOCK_FILE.open("w") as f:
        f.write(str(os.getpid()))
    logger.info("Блокировка установлена успешно.")

def release_lock():
    """Удаление файла блокировки при завершении работы."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    logger.info("Блокировка снята.")

def start_celery_worker():
    """Запуск Celery-воркера в отдельном потоке."""
    logger.info("Запуск Celery-воркера...")
    # Запускаем воркер с использованием argv для передачи параметров
    celery_app.worker_main(argv=["worker", "--loglevel=info", "--pool=eventlet"])
    logger.info("Celery-воркер завершен.")

# Инициализация приложения Telegram
app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

# Регистрация обработчиков
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("create_capsule", create_capsule_command))
app.add_handler(CommandHandler("add_recipient", add_recipient_command))
app.add_handler(CommandHandler("view_capsules", view_capsules_command))
app.add_handler(CommandHandler("send_capsule", send_capsule_command))
app.add_handler(CommandHandler("delete_capsule", delete_capsule_command))
app.add_handler(CommandHandler("edit_capsule", edit_capsule_command))
app.add_handler(CommandHandler("view_recipients", view_recipients_command))
app.add_handler(CommandHandler("select_send_date", select_send_date))
app.add_handler(CommandHandler("support_author", support_author))
app.add_handler(CommandHandler("change_language", change_language))

app.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r"^(ru|en|es|fr|de)$"))
app.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r"^(week|month|custom)$"))
app.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern=r"^(confirm_delete|cancel_delete)$"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

async def run_bot_and_worker():
    """Запуск бота и воркера в одном процессе."""
    # Установка блокировки
    acquire_lock()
    
    try:
        # Запуск Celery-воркера в отдельном потоке
        celery_thread = Thread(target=start_celery_worker, daemon=True)
        celery_thread.start()
        logger.info("Celery-воркер запущен в фоновом потоке.")

        # Применяем nest_asyncio для совместимости с асинхронным кодом
        nest_asyncio.apply()

        # Запуск Telegram-бота в режиме polling
        await app.initialize()
        await app.start()
        logger.info("Telegram-бот запущен.")
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=10)

        # Бесконечный цикл для удержания процесса
        while True:
            await asyncio.sleep(3600)  # Спим 1 час, чтобы не нагружать процессор

    except Exception as e:
        logger.error(f"Ошибка при запуске бота или воркера: {e}")
        raise
    finally:
        # Остановка бота и снятие блокировки
        await app.stop()
        await app.shutdown()
        release_lock()

if __name__ == "__main__":
    # Запуск асинхронной функции
    asyncio.run(run_bot_and_worker())
