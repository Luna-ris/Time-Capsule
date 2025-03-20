import os
import sys
import logging
import redis
from dotenv import load_dotenv
from supabase import create_client
from celery import Celery

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

if not all([TELEGRAM_TOKEN, ENCRYPTION_KEY, SUPABASE_URL, SUPABASE_KEY, REDIS_URL]):
    logger.error("Не все обязательные переменные окружения заданы: TELEGRAM_TOKEN=%s, ENCRYPTION_KEY=%s, SUPABASE_URL=%s, SUPABASE_KEY=%s, REDIS_URL=%s",
                 TELEGRAM_TOKEN, ENCRYPTION_KEY, SUPABASE_URL, SUPABASE_KEY, REDIS_URL)
    sys.exit(1)

ENCRYPTION_KEY_BYTES = ENCRYPTION_KEY.encode('utf-8').ljust(32)[:32]

# Инициализация Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации Supabase: {e}")
    sys.exit(1)

# Настройка Celery
celery_app = Celery('tasks', broker=REDIS_URL)
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.timezone = 'UTC'
celery_app.conf.broker_connection_retry_on_startup = True

# Проверка подключения к Redis
def check_redis_connection():
    try:
        redis_client = redis.StrictRedis.from_url(REDIS_URL)
        redis_client.ping()
        logger.info("Redis успешно пингован и доступен по адресу: %s", REDIS_URL)
    except redis.ConnectionError as e:
        logger.error("Ошибка подключения к Redis по адресу %s: %s", REDIS_URL, e)
        sys.exit(1)
    except Exception as e:
        logger.error("Неизвестная ошибка при проверке Redis: %s", e)
        sys.exit(1)

def check_celery_worker():
    try:
        logger.info("Начало проверки активности Celery Worker")
        inspect = celery_app.control.inspect()
        logger.debug("Создан объект inspect для проверки Celery: %s", inspect)
        
        active_workers = inspect.active()
        logger.info("Результат проверки активных воркеров: %s", active_workers)
        
        if active_workers is None:
            logger.warning("Celery Worker не отвечает (inspect.active() вернул None). Воркер может не быть запущен, но продолжаем запуск бота для отладки")
            return False
        elif not active_workers:
            logger.warning("Celery Worker не запущен: список активных воркеров пуст. Проверьте логи воркера")
            return False
        else:
            logger.info("Celery Worker активен. Найденные воркеры: %s", list(active_workers.keys()))
            return True
    except Exception as e:
        logger.error("Ошибка при проверке Celery Worker: %s. Детали: %s", type(e).__name__, e)
        logger.warning("Продолжаем запуск бота без проверки воркера для отладки")
        return False

def start_services():
    """Запуск необходимых сервисов."""
    logger.info("Запуск проверки сервисов")
    check_redis_connection()
    logger.info("Redis успешно запущен и проверен")
    if check_celery_worker():
        logger.info("Celery Worker успешно проверен и запущен")
    else:
        logger.warning("Celery Worker не проверен успешно, но бот продолжает работу")
