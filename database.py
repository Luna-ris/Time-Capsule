from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
