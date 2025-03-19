import os
import sys
import logging
import subprocess
import time
from dotenv import load_dotenv
from celery import Celery

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([TELEGRAM_TOKEN, ENCRYPTION_KEY, SUPABASE_URL, SUPABASE_KEY]):
    logger.error("Не все обязательные переменные окружения заданы.")
    sys.exit(1)

ENCRYPTION_KEY_BYTES = ENCRYPTION_KEY.encode('utf-8').ljust(32)[:32]

# Настройка Celery
celery_app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.timezone = 'UTC'
celery_app.conf.broker_connection_retry_on_startup = True

# Функции запуска сервисов
def start_process(command: str, name: str) -> bool:
    """Запуск процесса с логированием."""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"{name} запущен с PID: {process.pid}")
        time.sleep(2)
        if process.poll() is None:
            logger.info(f"{name} успешно запущен.")
            return True
        else:
            error = process.stderr.read().decode()
            logger.error(f"Ошибка запуска {name}: {error}")
            return False
    except Exception as e:
        logger.error(f"Не удалось запустить {name}: {e}")
        return False

def start_services():
    """Запуск необходимых сервисов."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.error("Переменная REDIS_URL не задана.")
        sys.exit(1)
    celery_command = "celery -A config.celery_app worker --loglevel=info --pool=solo"
    if not start_process(celery_command, "Celery"):
        logger.error("Не удалось запустить Celery.")
        sys.exit(1)
