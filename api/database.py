from supabase import create_client, Client
from api.config import get_settings

settings = get_settings()

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


def get_db():
    """Dependency for getting database client"""
    return supabase
