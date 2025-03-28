# TimeCapsuleBot

**TimeCapsuleBot** — это Telegram-бот, который позволяет пользователям создавать "капсулы времени" с текстом, фото, видео, аудио, стикерами и документами, чтобы отправить их себе или друзьям в будущем. Бот поддерживает многоязычный интерфейс, шифрование данных и планирование отправки через Celery.

## Основные возможности

- **Создание капсул времени**: Добавляйте текст, изображения, видео, аудио, стикеры и документы в свои капсулы.
- **Планирование отправки**: Устанавливайте дату и время для автоматической отправки капсул получателям.
- **Многоязычная поддержка**: Доступные языки — русский, английский, испанский, французский и немецкий.
- **Шифрование данных**: Все содержимое капсул шифруется с использованием AES для безопасности.
- **Управление капсулами**: Просматривайте, редактируйте, удаляйте капсулы и добавляйте получателей.
- **Асинхронная работа**: Использует `python-telegram-bot` и `Celery` для надежной обработки задач.

## Как работает бот

1. **Создание капсулы**:
   - Используйте команду `/create_capsule`, чтобы начать создание.
   - Укажите название, добавьте контент (текст, медиа) и выберите получателей (Telegram-имена через пробел, например, `@Friend1 @Friend2`).
   - Установите дату отправки (через неделю, месяц или выберите свою дату) или оставьте капсулу в черновиках.

2. **Управление капсулами**:
   - `/view_capsules` — просмотр списка ваших капсул.
   - `/add_recipient` — добавление новых получателей.
   - `/send_capsule` — немедленная отправка капсулы.
   - `/delete_capsule` — удаление капсулы.
   - `/view_recipients` — просмотр списка получателей.
   - `/select_send_date` — установка даты отправки.

3. **Отправка**:
   - Если дата отправки установлена, Celery автоматически отправит капсулу в указанное время.
   - Без даты капсула отправляется вручную через `/send_capsule`.

4. **Локализация**:
   - Смените язык интерфейса с помощью `/change_language`.

## Требования

- Python 3.9 или выше
- Redis (для брокера Celery)
- Supabase (для базы данных)
- Telegram API токен

## Установка

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/username/timecapsulebot.git
   cd timecapsulebot
   ```

2. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте переменные окружения**:
   Создайте файл `.env` в корневой директории и добавьте следующие переменные:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   ENCRYPTION_KEY=your_encryption_key_in_hex
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   REDIS_URL=redis://your_redis_host:6379/0
   ```

4. **Настройте Supabase**:
   - Создайте таблицы `users`, `capsules` и `recipients` в Supabase с соответствующими полями (см. `database.py`).

5. **Запустите Redis**:
   Убедитесь, что Redis работает на указанном в `REDIS_URL` хосте.

6. **Запустите бота**:
   ```bash
   python main.py
   ```

7. **Запустите Celery**:
   В отдельном терминале выполните:
   ```bash
   celery -A tasks worker --loglevel=info
   ```

## Использование

- Начните с команды `/start` в Telegram, чтобы зарегистрироваться и увидеть меню.
- Следуйте инструкциям бота для создания и управления капсулами.
- Получатели должны быть зарегистрированы в боте, чтобы получать капсулы.

## Пример

1. Создайте капсулу:
   ```
   /create_capsule
   Название: Моя капсула
   Текст: Привет из прошлого!
   Получатели: @Friend1 @Friend2
   Дата: 25.12.2025 12:00:00
   ```
2. Бот сохранит капсулу и отправит её 25 декабря 2025 года в 12:00 по UTC.

## Структура проекта

```
timecapsulebot/
├── main.py          # Основной файл запуска бота
├── utils.py         # Утилитарные функции
├── tasks.py         # Задачи Celery
├── handlers.py      # Обработчики команд и сообщений
├── database.py      # Взаимодействие с Supabase
├── crypto.py        # Шифрование/дешифрование
├── config.py        # Конфигурация и настройка
├── localization.py  # Локализация
├── celery_config.py # Отдельная конфигурация Celery
├── capsule_job.py   # Логика отправки капсул
├── requirements.txt # Зависимости
└── README.md        # Этот файл
```

## Зависимости

См. `requirements.txt` для полного списка. Основные:
- `python-telegram-bot` — взаимодействие с Telegram API
- `celery` — асинхронные задачи
- `redis` — брокер для Celery
- `supabase` — клиент для базы данных
- `cryptography` — шифрование данных
