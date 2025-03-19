import sys
import os
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import TELEGRAM_TOKEN, logger, celery_app, start_services
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

def main():
    """Основная функция запуска бота."""
    try:
        nest_asyncio.apply()
        start_services()

        app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

        # Регистрация обработчиков команд
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

        # Регистрация обработчиков callback-запросов
        app.add_handler(CallbackQueryHandler(handle_language_selection, pattern=r"^(ru|en|es|fr|de)$"))
        app.add_handler(CallbackQueryHandler(handle_date_buttons, pattern=r"^(week|month|custom)$"))
        app.add_handler(CallbackQueryHandler(handle_delete_confirmation, pattern=r"^(confirm_delete|cancel_delete)$"))

        # Регистрация обработчиков сообщений
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.VIDEO, handle_video))
        app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))

        # Проверка прав бота с небольшой задержкой
        app.job_queue.run_once(check_bot_permissions, 2)

        # Запуск бота
        logger.info("Запуск бота...")
        PORT = int(os.environ.get('PORT', '8443'))
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"https://{os.environ['DOMAIN']}/{TELEGRAM_TOKEN}"
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
