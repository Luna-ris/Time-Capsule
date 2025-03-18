import os
from celery import Celery


# Настройка Celery с использованием REDIS_URL от Railway
app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

# Конфигурация Celery
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.timezone = 'UTC'
app.conf.broker_connection_retry_on_startup = True
