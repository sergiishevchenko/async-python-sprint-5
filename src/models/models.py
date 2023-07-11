from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()

class Directory(Base):
    __tablename__ = 'directories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid1)
    path = Column(String(255), nullable=False, unique=True)


class File(Base):
    __tablename__ = 'files'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid1)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(125), nullable=False)
    path = Column(String(255), nullable=False, unique=True)
    size = Column(Integer, nullable=False)
    is_downloadable = Column(Boolean, default=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid1)
    username = Column(String(125), nullable=False, unique=True)
    password = Column(String(125), nullable=False)
    files = relationship('File', backref='user')
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
