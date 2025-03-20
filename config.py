import os
import sys
import logging
import redis
from dotenv import load_dotenv
from supabase import create_client
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

# Проверка подключения к Redis
def check_redis_connection():
    try:
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
        redis_client.ping()
        logger.info("Redis запущен и доступен.")
    except redis.ConnectionError as e:
        logger.error(f"Ошибка подключения к Redis: {e}")
        sys.exit(1)

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
    check_redis_connection()
    logger.info("Сервисы успешно запущены.")
