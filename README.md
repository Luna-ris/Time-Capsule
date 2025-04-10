# TimeCapsuleBot

Привет! Это **TimeCapsuleBot** — мой проект, созданный для конкурса Международной олимпиады "IT-Планета 2025". Этот Telegram-бот позволяет создавать "капсулы времени" — сообщения с текстом, фото, видео, аудио и другими файлами, которые можно отправить себе или друзьям в будущем. Я постарался сделать его удобным, безопасным и функциональным, используя современные инструменты и технологии.

## Что это за проект?

TimeCapsuleBot — это бот, который я разработал, чтобы показать, как можно сделать отложенную отправку сообщений в Telegram. Идея простая: ты создаёшь капсулу, добавляешь в неё текст, фото или видео, указываешь, кому её отправить, и выбираешь дату, когда она должна быть доставлена. Бот всё сделает сам! Проект был создан для конкурса "IT-Планета 2025", и я постарался сделать его максимально полезным и интересным.

Вот что умеет бот:
- Создавать капсулы времени с текстом, фото, видео, аудио, стикерами, документами и голосовыми сообщениями.
- Отправлять капсулы в заданное время (например, через неделю или в любой другой день).
- Шифровать содержимое капсул с помощью AES, чтобы данные были в безопасности.
- Поддерживать несколько языков: русский, английский, испанский, французский и немецкий.
- Управлять капсулами: просматривать, редактировать, удалять их, а также добавлять новых получателей.

Я разместил серверную часть на Railway, и бот использует только бесплатные API.

## Что может бот?

- **Создание капсул**: Добавляй текст, медиафайлы, указывай получателей.
- **Отложенная отправка**: Выбирай, когда капсула будет отправлена, с помощью Celery.
- **Безопасность**: Все данные в капсулах шифруются через AES.
- **Многоязычность**: Интерфейс доступен на 5 языках (ru, en, es, fr, de).
- **Управление**: Просматривай, редактируй, удаляй капсулы, добавляй новых получателей.
- **Пагинация**: Удобный интерфейс для просмотра списка капсул с разбивкой по страницам.

## Какие технологии я использовал?

- **Python 3.9+**: Основной язык, на котором написан бот.
- **python-telegram-bot**: Для работы с Telegram API.
- **Celery**: Для отложенной отправки капсул.
- **Redis**: Брокер для Celery.
- **Supabase**: База данных, где хранятся пользователи, капсулы и получатели.
- **cryptography**: Для шифрования данных с помощью AES.
- **Flask**: На случай, если захочу добавить веб-интерфейс.
- **apscheduler**: Альтернатива Celery для планирования задач (если вдруг понадобится).
- **pytz**: Для работы с часовыми поясами.
- **Railway**: Платформа, где я разместил серверную часть.

## Как установить и запустить?

### Что нужно для начала?

Убедись, что у тебя есть:
- Python 3.9 или новее.
- Redis (для Celery).
- Аккаунт на Supabase.
- Аккаунт на Railway (если хочешь развернуть бот на сервере).

### Установка

1. Склонируй репозиторий:
   ```bash
   git clone https://github.com/Luna-ris/Time-Capsule
   cd Time-Capsule
   ```

2. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настрой переменные окружения (подробности ниже) в файле `.env`:
   ```plaintext
   TELEGRAM_TOKEN=your_telegram_token
   ENCRYPTION_KEY=your_encryption_key
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_key
   REDIS_URL=redis://localhost:6379/0
   DONATIONALERTS_TOKEN=your_donationalerts_token
   ```

4. Запусти бота:
   ```bash
   python main.py
   ```

5. Чтобы отложенная отправка работала, запусти Celery-воркер:
- Открой вторую командную строку.
- Перейди в директорию с ботом:
    ```bash
   cd путь/к/Time-Capsule
   ```
- Выполни команду:
   ```bash
   celery -A config.celery_app worker --loglevel=info
   ```

### Развёртывание на Railway

1. Создай проект на Railway.
2. Подключи свой репозиторий GitHub к Railway.
3. Настрой переменные окружения в настройках проекта (точно так же, как в `.env`).
4. Убедись, что Redis и Supabase доступны для твоего приложения.
5. Разверни проект — Railway сам запустит `main.py`.
6. Чтобы отложенная отправка работала, запусти Celery-воркер.Cоздай Empty Service и в Custom Start Command пропиши:
Чтобы отложенная отправка работала, запусти Celery-воркер
   ```bash
  celery -A tasks worker --loglevel=info --pool=solo
   ```

## Как настроить переменные окружения?

Для работы бота нужно задать несколько переменных окружения. Вот как их получить:

### 1. `TELEGRAM_TOKEN`

Это токен твоего Telegram-бота. Чтобы его получить:
1. Открой Telegram, найди @BotFather.
2. Напиши `/start`, а затем `/newbot`.
3. Следуй инструкциям: придумай имя бота (например, `TimeCapsuleBot`) и username (например, `@TimeCapsulee_Bot`).
4. @BotFather даст тебе токен, например: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`.
5. Скопируй его и добавь в `.env`:
   ```plaintext
   TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```

### 2. `ENCRYPTION_KEY`

Это ключ для шифрования данных. Он должен быть длиной 32 байта (в шестнадцатеричном формате — 64 символа). Я написал скрипт, чтобы сгенерировать его:

1. Сохрани этот код в файл `generate_key.py`:
   ```python
   import os

   def generate_encryption_key():
       key = os.urandom(32)
       encryption_key = key.hex()
       return encryption_key

   if __name__ == "__main__":
       encryption_key = generate_encryption_key()
       print(f"Сгенерированный ключ шифрования: {encryption_key}")
   ```

2. Запусти скрипт:
   ```bash
   python generate_key.py
   ```
   Он выведет что-то вроде:
   ```
   Сгенерированный ключ шифрования: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
   ```

3. Скопируй ключ и добавь в `.env`:
   ```plaintext
   ENCRYPTION_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
   ```

### 3. `SUPABASE_URL` и `SUPABASE_KEY`

Эти переменные нужны для подключения к базе данных Supabase:
1. Зарегистрируйся на [Supabase](https://supabase.com/) и создай новый проект.
2. Зайди в **Settings** → **Data-API**.
3. Скопируй:
   - **URL** (например, `https://your-project-id.supabase.co`).
   - **Anon Key** (это публичный ключ API).
4. Добавь их в `.env`:
   ```plaintext
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-key
   ```

### 4. `REDIS_URL`

Это адрес для подключения к Redis, который нужен для Celery:
1. Если работаешь локально:
   - Установи Redis.
   - По умолчанию Redis работает на `localhost:6379`, так что:
     ```plaintext
     REDIS_URL=redis://localhost:6379/0
     ```
2. Если используешь Railway:
   - Railway сам предоставит Redis. Зайди в настройки проекта, найди сервис Redis и скопируй его URL, например:
     ```plaintext
     REDIS_URL=redis://default:password@redis-1234.railway.app:6379
     ```

### 5. `DONATIONALERTS_TOKEN`

Это токен для DonationAlerts, чтобы принимать донаты (я добавил такую возможность в функцию поддержки автора):
1. Зарегистрируйся на [DonationAlerts](https://www.donationalerts.com/).
2. Зайди в раздел **API** или **Настройки интеграции**.
3. Создай приложение или виджет и получи токен (например, `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`).
4. Добавь его в `.env`:
   ```plaintext
   DONATIONALERTS_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
Если донаты тебе не нужны, можешь пропустить этот шаг — бот будет работать и без этой переменной.

## Как пользоваться ботом?

1. Запусти бота и напиши `/start`.
2. Создай капсулу с помощью `/create_capsule`.
3. Добавь в неё текст, фото, видео или другие файлы.
4. Укажи получателей (например, `@Friend1 @Friend2`).
5. Выбери дату отправки через `/select_send_date` или отправь капсулу сразу с помощью `/send_capsule`.
6. Управляй капсулами: смотри их список (`/view_capsules`), удаляй (`/delete_capsule`), добавляй новых получателей (`/add_recipient`).

## Что внутри проекта?

- `main.py`: Точка входа, где запускается бот и регистрируются все обработчики.
- `utils.py`: Полезные функции, например, проверка прав, работа с датами и планирование задач.
- `tasks.py`: Задачи для Celery, которые отвечают за отложенную отправку капсул.
- `requirements.txt`: Список всех зависимостей.
- `localization.py`: Поддержка нескольких языков.
- `handlers.py`: Обработчики команд и сообщений от пользователей.
- `database.py`: Функции для работы с Supabase (создание, чтение, обновление, удаление данных).
- `crypto.py`: Шифрование и дешифрование данных с помощью AES.
- `config.py`: Настройки бота, включая переменные окружения, логирование и Celery.
