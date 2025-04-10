import os
import sys
import logging
import redis
from dotenv import load_dotenv
from supabase import create_client
from celery import Celery
from tasks import send_capsule_task

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

if not all([TELEGRAM_TOKEN, ENCRYPTION_KEY, SUPABASE_URL, SUPABASE_KEY, REDIS_URL]):
    logger.error("Не все обязательные переменные окружения заданы")
    sys.exit(1)

ENCRYPTION_KEY_BYTES = ENCRYPTION_KEY.encode('utf-8').ljust(32)[:32]

# Инициализация Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error("Ошибка инициализации Supabase: %s", e)
    sys.exit(1)

# Настройка Celery
celery_app = Celery('tasks', broker=REDIS_URL)
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    broker_connection_retry_on_startup=True
)

# Проверка подключения к Redis
def check_redis_connection():
    try:
        redis_client = redis.StrictRedis.from_url(REDIS_URL)
        redis_client.ping()
    except redis.ConnectionError as e:
        logger.error("Ошибка подключения к Redis: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Неизвестная ошибка при проверке Redis: %s", e)
        sys.exit(1)

def check_celery_worker():
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if not active_workers:
            logger.warning("Celery Worker не запущен")
            return False
        return True
    except Exception as e:
        logger.error("Ошибка при проверке Celery Worker: %s", e)
        return False

def start_services():
    """Запуск необходимых сервисов."""
    check_redis_connection()
    if not check_celery_worker():
        logger.warning("Celery Worker не проверен успешно, но бот продолжает работу")
