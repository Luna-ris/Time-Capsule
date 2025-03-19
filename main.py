import subprocess
import time
import sys
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler
)
from config import TELEGRAM_TOKEN, logger, celery_app
from handlers import (
    start, help_command, create_capsule_command, add_recipient_command,
    view_capsules_command, send_capsule_command, delete_capsule_command,
    edit_capsule_command, view_recipients_command, select_send_date,
    support_author, change_language, handle_language_selection,
    handle_date_buttons, handle_delete_confirmation, handle_text,
    handle_photo, handle_video, handle_audio, handle_document,
    handle_sticker, handle_voice
)
from utils import post_init, check_bot_permissions

def start_process(command: str, name: str) -> bool:
    """Запуск процесса с логированием."""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Процесс {name} запущен с PID {process.pid}")
        # Читаем первые строки вывода для проверки
        stdout, stderr = process.communicate(timeout=10)
        if stdout:
            logger.info(f"Вывод {name}: {stdout.decode().strip()}")
        if stderr:
            logger.error(f"Ошибка {name}: {stderr.decode().strip()}")
        return process.returncode == 0 or process.poll() is None
    except Exception as e:
        logger.error(f"Ошибка при запуске процесса {name}: {e}")
        return False

def main():
    """Основная функция запуска бота."""
    try:
        nest_asyncio.apply()
        
        # Запуск Celery worker в отдельном процессе
        if not start_process("celery -A config.celery_app worker --loglevel=info", "Celery Worker"):
            logger.error("Не удалось запустить Celery Worker")
            sys.exit(1)

        # Создание приложения Telegram
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("create_capsule", create_capsule_command))
        application.add_handler(CommandHandler("add_recipient", add_recipient_command))
        application.add_handler(CommandHandler("view_capsules", view_capsules_command))
        application.add_handler(CommandHandler("send_capsule", send_capsule_command))
        application.add_handler(CommandHandler("delete_capsule", delete_capsule_command))
        application.add_handler(CommandHandler("edit_capsule", edit_capsule_command))
        application.add_handler(CommandHandler("view_recipients", view_recipients_command))
        application.add_handler(CommandHandler("select_send_date", select_send_date))
        application.add_handler(CommandHandler("support_author", support_author))
        application.add_handler(CommandHandler("change_language", change_language))
        
        # Обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))
        application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
        application.add_handler(MessageHandler(filters.VOICE, handle_voice))
        
        # Обработчики callback-запросов
        application.add_handler(CallbackQueryHandler(handle_language_selection, pattern="^(ru|en|es|fr|de)$"))
        application.add_handler(CallbackQueryHandler(handle_date_buttons, pattern="^(week|month|custom)$"))
        application.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern="^(confirm_delete|cancel_delete)$"))

        # Пост-инициализация
        application.post_init = post_init
        
        # Проверка прав бота с небольшой задержкой
        application.job_queue.run_once(check_bot_permissions, 2)

        # Запуск бота
    logger.info("Запуск бота...")
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Ошибка в run_polling: {e}")
        raise  # Поднимем исключение для логирования
    finally:
        logger.info("Бот завершил работу")

if __name__ == "__main__":
    main()
