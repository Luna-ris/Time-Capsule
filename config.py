import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client
from celery import Celery

# Настройка логирования с поддержкой дополнительных данных
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - UserID: %(user_id)s - Command: %(command)s - Message: %(message)s',
    handlers=[logging.StreamHandler()]
)

class ContextualFilter(logging.Filter):
    def filter(self, record):
        record.user_id = getattr(record, 'user_id', None)
        record.command = getattr(record, 'command', None)
        record.message = getattr(record, 'message', None)
        return True

logger.addFilter(ContextualFilter())

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

# Инициализация Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error(f"Ошибка инициализации Supabase: {e}")
    sys.exit(1)

# Настройка Celery
celery_app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.timezone = 'UTC'
celery_app.conf.broker_connection_retry_on_startup = True

# Функция запуска сервисов
def start_services():
    """Запуск необходимых сервисов."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.error("Переменная REDIS_URL не задана.")
        sys.exit(1)
    logger.info("Сервисы успешно запущены.")
