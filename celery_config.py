from celery import Celery

# Создаем экземпляр Celery
celery_app = Celery(
    'my_bot',
    broker='redis://localhost:6379/0',  # Используем Redis в качестве брокера
    backend=
    'redis://localhost:6379/0'  # Используем Redis для хранения результатов
)

# Настройки Celery
celery_app.conf.update(
    result_expires=3600,
    timezone='UTC',
    enable_utc=True,
)
