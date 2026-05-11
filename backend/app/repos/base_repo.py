from typing import TypeVar, Generic, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.config.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class GenericRepository(Generic[ModelType]):
  def __init__(self, db_session: AsyncSession, model: Type[ModelType]):
    self.db_session = db_session
    self.model = model

  async def get_by_id(self, obj_id: int) -> Optional[ModelType]:
    stmt = select(self.model).where(self.model.id == obj_id)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def create(self, instance: ModelType) -> ModelType:
    self.db_session.add(instance)
    await self.db_session.flush()
    return instance

  async def update(self, obj_id: int, update_data: dict) -> Optional[ModelType]:
    stmt = update(self.model).where(self.model.id == obj_id).values(**update_data).returning(self.model)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def delete(self, obj_id: int) -> bool:
    stmt = delete(self.model).where(self.model.id == obj_id)
    result = await self.db_session.execute(stmt)
    return result.rowcount > 0