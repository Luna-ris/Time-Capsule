import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client
from celery import Celery
import redis

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
    check_redis_connection()
    check_celery_worker()
    logger.info("Сервисы успешно запущены.")

def check_redis_connection():
    try:
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        redis_client.ping()
        logger.info("Redis is running and accessible.")
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        sys.exit(1)

def check_celery_worker():
    try:
        # Проверка запуска Celery Worker
        result = celery_app.control.inspect().active()
        if result:
            logger.info("Celery Worker is running.")
        else:
            logger.error("Celery Worker is not running.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Celery Worker check error: {e}")
        sys.exit(1)
