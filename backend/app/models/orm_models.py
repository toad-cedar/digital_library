# ORM-модели
from sqlalchemy     import Column, Integer, String, Text, BigInteger, Boolean, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.config.database import Base

# --- Многие-ко-многим модели ---
document_tag_link = Table(
    'document_tag_link',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id'),      primary_key=True),
    Column('tag_id',      Integer, ForeignKey('document_tags.id'),  primary_key=True)
)
group_user = Table(
    'group_user',
    Base.metadata,
    Column('user_id',  Integer, ForeignKey('users.id'),           primary_key=True),
    Column('group_id', Integer, ForeignKey('learning_groups.id'), primary_key=True)
)
material_documents = Table(
    'material_documents',
    Base.metadata,
    Column('material_id', Integer, ForeignKey('group_materials.id'), primary_key=True),
    Column('document_id', Integer, ForeignKey('documents.id'),       primary_key=True)
)
roles_permissions = Table(
    'roles_permissions',
    Base.metadata,
    Column('role_id',       Integer, ForeignKey('roles.id'),       primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# --- ORM-модели ---
class Role(Base):
    __tablename__ = 'roles'
    id        = Column(Integer, primary_key=True, index=True)
    role_name = Column(String,  unique=True, nullable=False) # user, teacher, admin
    
    # Связи
    users       = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=roles_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = 'permissions'
    id              = Column(Integer, primary_key=True, index=True)
    permission_name = Column(String,  unique=True, nullable=False)
    permission_description = Column(Text)
    
    # Связи
    roles = relationship("Role", secondary=roles_permissions, back_populates="permissions")

class User(Base):
    __tablename__ = 'users'
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String,  unique=True, nullable=False) # CHECK: длина, формат
    email    = Column(String,  unique=True, nullable=False) # CHECK: формат
    password_hash  = Column(String,  nullable=False)        # CHECK: длина
    user_role_id   = Column(Integer, ForeignKey('roles.id'), nullable=False) # FK: roles
    current_status = Column(Boolean, nullable=False, default=True) # активен/заблокирован
    registration_date = Column(DateTime(timezone=True), default=datetime.now)

    role = relationship("Role", back_populates="users")
    # Другие связи определены ниже

class SupportedFormat(Base):
    __tablename__ = 'supported_formats'
    id          = Column(Integer, primary_key=True, index=True)
    format_name = Column(String,  unique=True, nullable=False) # CHECK: длина
    
    documents = relationship("Document", back_populates="format_obj")

class Document(Base):
    __tablename__ = 'documents'
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String,  nullable=False)       # CHECK: длина
    description  = Column(Text)
    author       = Column(String)                       # Автор текста (не загрузчик)
    upload_date  = Column(DateTime(timezone=True), default=datetime.now)
    publish_date = Column(DateTime(timezone=True), default=datetime.now)
    format_id    = Column(Integer, ForeignKey('supported_formats.id'), nullable=False) # FK: formats
    uploader_id  = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users
    minio_bucket = Column(String,  nullable=False)       # CHECK: длина имени бакета
    cover_bucket = Column(String)
    minio_object_path  = Column(String, nullable=False) # Путь к файлу в MinIO
    file_original_name = Column(String)                 # Оригинальное имя файла
    file_size = Column(BigInteger, nullable=False)      # Размер файла в байтах
    file_hash = Column(String,     nullable=False, unique=True) # CHECK: длина хеша (SHA-256)
    converted_to_pdf = Column(Boolean, default=False)
    status_id = Column(Integer,    ForeignKey('upload_statuses.id'), nullable=False) # Теперь это связано с upload_statuses
    cover_url = Column(String) # URL к обложке документа
    
    format_obj = relationship("SupportedFormat", back_populates="documents")
    uploader   = relationship("User", back_populates="documents_uploaded") # Загрузчик документа
    tags       = relationship("DocumentTag", secondary=document_tag_link, back_populates="documents")
    status_obj = relationship("UploadStatus",back_populates="documents")

class DocumentTag(Base):
    __tablename__ = 'document_tags'
    id       = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String,  unique=True, nullable=False) # CHECK: длина

    documents = relationship("Document", secondary=document_tag_link, back_populates="tags")

class UploadStatus(Base):
    __tablename__ = 'upload_statuses'
    id          = Column(Integer, primary_key=True, index=True)
    status_name = Column(String,  unique=True, nullable=False) # uploaded, processing, pending_review, approved, rejected

    requests  = relationship("UploadRequest", back_populates="status_obj")
    documents = relationship("Document",      back_populates="status_obj")

class UploadRequest(Base):
    __tablename__ = 'upload_request'
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users (кто загрузил)
    original_name = Column(String,  nullable=False)    # CHECK: длина
    minio_path    = Column(String,  nullable=False)    # Где лежит временный файл
    upload_date   = Column(DateTime(timezone=True), default=datetime.now)
    file_hash     = Column(String,  nullable=False)    # CHECK: длина
    status_id     = Column(Integer, ForeignKey('upload_statuses.id'), nullable=False, default=1) # FK: statuses; # ! default: uploaded
    moderator_id  = Column(Integer, ForeignKey('users.id')) # FK: users (модератор, может быть NULL)

    # Связь с пользователем, который *создал* заявку (загрузчик)
    user       = relationship("User", foreign_keys=[user_id], back_populates="uploads_created") # Кто загрузил (создатель заявки)
    # Связь с пользователем, который *модерировал* заявку
    moderator  = relationship("User", foreign_keys=[moderator_id], back_populates="uploads_moderated") # Кто модерировал (если назначен)
    status_obj = relationship("UploadStatus", back_populates="requests")
    

class LearningGroup(Base):
    __tablename__ = 'learning_groups'
    id         = Column(Integer, primary_key=True, index=True)
    group_name = Column(String,  nullable=False) # CHECK: длина
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users

    creator   = relationship("User", back_populates="groups_created") # Преподаватель, создавший группу
    members   = relationship("User", secondary=group_user, back_populates="groups_joined")
    materials = relationship("GroupMaterial", back_populates="group")

class GroupMaterial(Base):
    __tablename__ = 'group_materials'
    id        = Column(Integer, primary_key=True, index=True)
    group_id  = Column(Integer, ForeignKey('learning_groups.id'), nullable=False) # FK: groups
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users
    message   = Column(Text)
    sent_at   = Column(DateTime(timezone=True), default=datetime.now)
    # Связи
    group   = relationship("LearningGroup", back_populates="materials")
    sender  = relationship("User", back_populates="group_materials_sent") # Кто отправил
    documents_attached = relationship("Document", secondary=material_documents, back_populates="group_materials_sent_to")

class ViewHistory(Base):
    __tablename__ = 'view_history'
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False) # FK: documents
    viewed_at   = Column(DateTime(timezone=True), default=datetime.now)
    # Связи
    user     = relationship("User", back_populates="history")
    document = relationship("Document", back_populates="history")

class FavoriteFolder(Base):
    __tablename__ = 'favorite_folder'
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users
    folder_name = Column(String,  nullable=False) # CHECK: длина
    description = Column(Text) # CHECK: длина
    parent_folder_id = Column(Integer, ForeignKey('favorite_folder.id')) # Рекурсивная ссылка
    # Связи
    user          = relationship("User", back_populates="favorite_folders")
    parent_folder = relationship("FavoriteFolder", remote_side=[id])
    items         = relationship("FavoriteItem", back_populates="folder")

class FavoriteItem(Base):
    __tablename__ = 'favorite_item'
    id          = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False) # FK: documents
    folder_id   = Column(Integer, ForeignKey('favorite_folder.id'), nullable=False) # FK: folders
    # Связи
    document = relationship("Document", back_populates="favorite_items")
    folder   = relationship("FavoriteFolder", back_populates="items")

class OfflineFolder(Base):
    __tablename__ = 'offline_folder'
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey('users.id'), nullable=False) # FK: users
    folder_name = Column(String,  nullable=False) # CHECK: длина
    description = Column(Text) # CHECK: длина
    parent_folder_id = Column(Integer, ForeignKey('offline_folder.id')) # Рекурсивная ссылка
    # Связи
    user          = relationship("User", back_populates="offline_folders")
    parent_folder = relationship("OfflineFolder", remote_side=[id])
    items         = relationship("OfflineItem", back_populates="folder")

class OfflineItem(Base):
    __tablename__ = 'offline_item'
    id          = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False) # FK: documents
    folder_id   = Column(Integer, ForeignKey('offline_folder.id'), nullable=False) # FK: folders
    local_file_hash_checksum = Column(String, nullable=False) # Хеш локальной копии файла
    # Связи
    document = relationship("Document", back_populates="offline_items")
    folder   = relationship("OfflineFolder", back_populates="items")


# TODO: Добавить больше моделей, в ходе расширения структуры данных


# --- Добавление обратных связей для избежания циклических зависимостей ---
User.uploads_created      = relationship("UploadRequest", foreign_keys=[UploadRequest.user_id], back_populates="user") # Заявки, созданные пользователем
User.uploads_moderated    = relationship("UploadRequest", foreign_keys=[UploadRequest.moderator_id], back_populates="moderator") # Заявки, модерированные пользователем
User.documents_uploaded   = relationship("Document",      back_populates="uploader")
User.groups_created       = relationship("LearningGroup", back_populates="creator")
User.history              = relationship("ViewHistory",   back_populates="user")
User.favorite_folders     = relationship("FavoriteFolder",back_populates="user")
User.offline_folders      = relationship("OfflineFolder", back_populates="user")
User.group_materials_sent = relationship("GroupMaterial", back_populates="sender")
User.groups_joined        = relationship("LearningGroup", secondary=group_user, back_populates="members")

Document.history          = relationship("ViewHistory",  back_populates="document")
Document.favorite_items   = relationship("FavoriteItem", back_populates="document")
Document.offline_items    = relationship("OfflineItem",  back_populates="document")
Document.group_materials_sent_to = relationship("GroupMaterial", secondary=material_documents, back_populates="documents_attached")
