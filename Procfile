web: python main.py
worker: celery -A tasks worker --loglevel=info --pool=solo
flower: celery -A tasks flower --loglevel=info
