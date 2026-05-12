from sqlalchemy import String, Column, Integer, DateTime, ForeignKey, Table, Enum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.config.database import Base, InvitationEnum

groups_users = Table(
  'groups_users', Base.metadata,
  Column('user_id', Integer, ForeignKey('users.id',   ondelete='CASCADE'), primary_key=True),
  Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)
)

group_material_documents = Table(
  'group_material_documents', Base.metadata,
  Column('material_id', Integer, ForeignKey('group_materials.id', ondelete='CASCADE'), primary_key=True),
  Column('document_id', Integer, ForeignKey('documents.id',       ondelete='CASCADE'), primary_key=True)
)

class Group(Base):
  __tablename__ = 'groups'
  
  id:         Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  group_name: Mapped[str] = mapped_column(String(100), unique=True) # ! CHECK: длина Название
  creator_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

  creator   = relationship("User", back_populates="groups_created")
  members   = relationship("User", secondary=groups_users, back_populates="groups_joined")
  materials = relationship("GroupMaterial", back_populates="group")
  invitations  = relationship("GroupInvitation", back_populates="group")


class GroupMaterial(Base):
  __tablename__ = 'group_materials'
  
  id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  group_id:    Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), index=True) # Группа
  sent_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  sender_id:   Mapped[int] = mapped_column(ForeignKey('users.id',  ondelete='SET NULL'), index=True)
  
  group   = relationship("Group", back_populates="materials")
  sender  = relationship("User",  back_populates="group_materials_sent")
  documents_attached = relationship("Document", secondary=group_material_documents, back_populates="group_materials")


class GroupInvitation(Base):
  __tablename__ = 'group_invitations'
  
  id:             Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  group_id:       Mapped[int] = mapped_column(ForeignKey('groups.id', ondelete='CASCADE'), index=True) # Группа
  invited_email:  Mapped[str] = mapped_column(String(255)) # Email приглашённого
  token:          Mapped[str] = mapped_column(String(64), unique=True) # Одноразовый токен
  expires_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True))
  invitation_status: Mapped[InvitationEnum] = mapped_column(Enum(InvitationEnum, name='invitation_enum', native_enum=True), default=InvitationEnum.PENDING) # InvitationEnum(pending / accepted / expired / revoked)
  created_by:     Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True) # Cоздатель
  
  group   = relationship("Group", back_populates="invitations")
  creator = relationship("User", foreign_keys=[created_by], back_populates="invitations_created") 