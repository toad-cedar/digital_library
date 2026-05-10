from sqlalchemy     import String, Column, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.config.database import Base

documents_search_tags = Table(
  'documents_search_tags', Base.metadata,
  Column('document_id', Integer, ForeignKey('documents.id'),   primary_key=True),
  Column('tag_id',      Integer, ForeignKey('search_tags.id'), primary_key=True)
)

class SearchTag(Base):
  __tablename__ = 'search_tags'
  
  id:       Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  tag_name: Mapped[str] = mapped_column(String(50), unique=True, index=True) # ! CHECK: длина, Наименование тега

  documents = relationship("Document", secondary=documents_search_tags, back_populates="tags")
