from celery import Celery
import os

# Настройка Celery с использованием REDIS_URL от Railway
app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.timezone = 'UTC'
