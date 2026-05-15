from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base

class CasbinRule(Base):
  __tablename__ = 'casbin_rule'
  
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  ptype: Mapped[str] = mapped_column(String(255))
  v0: Mapped[str] = mapped_column(String(255))
  v1: Mapped[str] = mapped_column(String(255))
  v2: Mapped[str] = mapped_column(String(255))
  v3: Mapped[str] = mapped_column(String(255))
  v4: Mapped[str] = mapped_column(String(255))
  v5: Mapped[str] = mapped_column(String(255))