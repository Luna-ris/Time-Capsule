import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from celery import Celery

# Загрузка переменных окружения
load_dotenv()

# Логирование
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Константы
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([TELEGRAM_TOKEN, ENCRYPTION_KEY, SUPABASE_URL, SUPABASE_KEY]):
    logger.error("Не все обязательные переменные окружения заданы.")
    sys.exit(1)

ENCRYPTION_KEY_BYTES = ENCRYPTION_KEY.encode('utf-8').ljust(32)[:32]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Состояния
CREATING_CAPSULE = "creating_capsule"
SELECTING_CAPSULE = "selecting_capsule"
SELECTING_CAPSULE_FOR_RECIPIENTS = "selecting_capsule_for_recipients"

# Настройка Celery
celery_app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.timezone = 'UTC'
celery_app.conf.broker_connection_retry_on_startup = True
