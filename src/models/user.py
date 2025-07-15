"""
사용자 모델
User model for authentication and authorization
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from ..config.database import Base


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100))
    role = Column(
        String(50), nullable=False, default="user"
    )  # admin, manager, user, guest

    # Security fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))

    # Additional security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))

    # Profile
    phone = Column(String(20))
    profile_image = Column(Text)

    # Preferences
    language = Column(String(10), default="ko")
    timezone = Column(String(50), default="Asia/Seoul")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
