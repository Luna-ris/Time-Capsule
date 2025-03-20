import sys
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext
)
from config import TELEGRAM_TOKEN, logger, celery_app, start_services
from handlers import (
    start, help_command, create_capsule_command, add_recipient_command,
    view_capsules_command, send_capsule_command, delete_capsule_command,
    edit_capsule_command, view_recipients_command, select_send_date,
    support_author, change_language, handle_language_selection,
    handle_date_buttons, handle_delete_confirmation, handle_text,
    handle_photo, handle_video, handle_audio, handle_document,
    handle_sticker, handle_voice, handle_inline_selection,
    handle_content_buttons, handle_send_confirmation
)
from utils import post_init, check_bot_permissions

# Обработчик ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик ошибок для Telegram бота."""
    logger.error(f"Произошла ошибка: {context.error}")
    
    # Проверяем, есть ли сообщение (update.message)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте снова позже.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {e}")
    # Если это callback-запрос (update.callback_query)
    elif update and update.callback_query:
        try:
            await update.callback_query.edit_message_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте снова.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке через callback: {e}")

def main():
    """Основная функция запуска бота."""
    try:
        nest_asyncio.apply()
        start_services()

        # Создание приложения Telegram
        logger.info("Инициализация приложения Telegram...")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

        # Регистрация обработчика ошибок
        app.add_error_handler(error_handler)

        # Регистрация обработчиков команд
        logger.info("Регистрация обработчиков команд...")
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
        app.add_handler(CallbackQueryHandler(handle_inline_selection, pattern=r"^(add_recipient|send_capsule|delete_capsule|edit_capsule|view_recipients|select_send_date|view|add_recipient_page|send_capsule_page|delete_capsule_page|edit_capsule_page|view_recipients_page|view_page)_\d+$"))
        app.add_handler(CallbackQueryHandler(handle_content_buttons, pattern=r"^(finish_capsule|add_more)$"))
        app.add_handler(CallbackQueryHandler(handle_send_confirmation, pattern=r"^(confirm_send|cancel_send)$"))
        app.add_handler(CallbackQueryHandler(handle_edit_content_buttons, pattern=r"^(delete_text|delete_photo|delete_video|delete_audio|delete_document|delete_sticker|delete_voice|add_new_content|save_edit)"))
        
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
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
