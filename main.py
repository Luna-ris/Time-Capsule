import subprocess
import time
import sys
import nest_asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, Update
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
