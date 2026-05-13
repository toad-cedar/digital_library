from casbin_sqlalchemy_adapter import Adapter
from app.config.settings import get_settings


def get_casbin_adapter() -> Adapter:
  """Получает URL для синхронного подключения к БД

  Returns:
    `Adapter(get_settings().get_sync_db_url)`
  """  
  return Adapter(get_settings().get_sync_db_url)