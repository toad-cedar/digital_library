from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import get_settings

# Движок
engine = create_async_engine(
  get_settings().DATABASE_URL, 
  pool_pre_ping=True, # Проверка соединения
  echo=False # Откл. вывод SQL-запросов в консось
)

# Создание сессии 
async_session_maker = async_sessionmaker(engine, expire_on_commit=False) 

class Base(AsyncAttrs, DeclarativeBase):
  pass
  # __abstract__ = True
  
  # @declared_attr.directive
  # def __tablename__(cls) -> str:
  #   return f"{cls.__name__.lower()}s"

async def get_db_session():
  async with async_session_maker() as session:
    yield session 