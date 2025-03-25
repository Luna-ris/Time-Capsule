from typing import Optional, List
from config import supabase, logger
from datetime import datetime

def fetch_data(table: str, query: dict = {}) -> list:
    """Получение данных из Supabase."""
    try:
        response = supabase.table(table).select("*")
        for key, value in query.items():
            response = response.eq(key, value)
        return response.execute().data
    except Exception as e:
        logger.error(f"Ошибка Supabase: {e}")
        return []

def post_data(table: str, data: dict) -> list:
    """Добавление данных в Supabase."""
    try:
        return supabase.table(table).insert(data).execute().data
    except Exception as e:
        logger.error(f"Ошибка записи в Supabase: {e}")
        return []

def update_data(table: str, query: dict, data: dict) -> list:
    """Обновление данных в Supabase."""
    try:
        query_builder = supabase.table(table).update(data)
        for key, value in query.items():
            query_builder = query_builder.eq(key, value)
        return query_builder.execute().data
    except Exception as e:
        logger.error(f"Ошибка обновления в Supabase: {e}")
        return []

def delete_data(table: str, query: dict) -> list:
    """Удаление данных из Supabase."""
    try:
        return (
            supabase.table(table)
            .delete()
            .eq(next(iter(query)), query[next(iter(query))])
            .execute()
            .data
        )
    except Exception as e:
        logger.error(f"Ошибка удаления в Supabase: {e}")
        return []

def get_chat_id(username: str) -> Optional[int]:
    """Получение chat_id по имени пользователя."""
    response = fetch_data("users", {"username": username})
    return response[0]['chat_id'] if response else None

def add_user(username: str, telegram_id: int, chat_id: int):
    """Добавление пользователя в базу данных."""
    if not fetch_data("users", {"telegram_id": telegram_id}):
        post_data("users", {
            "telegram_id": telegram_id,
            "username": username,
            "chat_id": chat_id
        })

def generate_unique_capsule_number(creator_id: int) -> int:
    """Генерация уникального номера капсулы для пользователя."""
    return len(fetch_data("capsules", {"creator_id": creator_id})) + 1

def create_capsule(
    creator_id: int,
    title: str,
    content: str,
    user_capsule_number: int,
    scheduled_at: Optional[datetime] = None
) -> int:
    """Создание новой капсулы."""
    from crypto import encrypt_data_aes
    encrypted_content = encrypt_data_aes(content)
    data = {
        "creator_id": creator_id,
        "title": title,
        "content": encrypted_content,
        "user_capsule_number": user_capsule_number,
        "is_sent": False
    }
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.isoformat()
    response = post_data("capsules", data)
    return response[0]['id'] if response else -1

def add_recipient(capsule_id: int, recipient_username: str):
    """Добавление получателя к капсуле."""
    post_data("recipients", {
        "capsule_id": capsule_id,
        "recipient_username": recipient_username
    })

def delete_capsule(capsule_id: int):
    """Удаление капсулы и связанных данных."""
    delete_data("recipients", {"capsule_id": capsule_id})
    delete_data("capsules", {"id": capsule_id})

def edit_capsule(capsule_id: int, title: Optional[str] = None, content: Optional[str] = None, scheduled_at: Optional[datetime] = None):
    """Редактирование капсулы."""
    from crypto import encrypt_data_aes
    data = {}
    if title:
        data["title"] = title
    if content:
        data["content"] = encrypt_data_aes(content)
    if scheduled_at:
        data["scheduled_at"] = scheduled_at.isoformat()
        data["is_sent"] = False
    if data:
        update_data("capsules", {"id": capsule_id}, data)

def get_user_capsules(telegram_id: int) -> list:
    """Получение списка капсул пользователя."""
    user = fetch_data("users", {"telegram_id": telegram_id})
    return fetch_data("capsules", {"creator_id": user[0]['id']}) if user else []

def get_capsule_recipients(capsule_id: int) -> list:
    """Получение списка получателей капсулы."""
    return fetch_data("recipients", {"capsule_id": capsule_id})
