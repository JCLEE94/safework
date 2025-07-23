"""User model builder for testing."""

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
from tests.builders.base_builder import BaseBuilder
from src.models.user import User


class UserBuilder(BaseBuilder[User]):
    """Builder for User model."""
    
    def _get_default_attrs(self) -> Dict[str, Any]:
        """Get default user attributes."""
        return {
            "username": "testuser",
            "email": "testuser@safework.test",
            "password_hash": self._hash_password("defaultpass123!"),
            "role": "worker",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password for testing."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def _create_instance(self, **attrs) -> User:
        """Create User instance."""
        user = User(**attrs)
        self.db.add(user)
        await self.db.flush()
        return user
    
    async def create_admin_user(
        self,
        username: str = "admin",
        email: str = "admin@safework.test",
        password: str = "admin123!"
    ) -> User:
        """Create admin user."""
        return await self.create(
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role="admin"
        )
    
    async def create_manager_user(
        self,
        username: str = "manager",
        email: str = "manager@safework.test",
        password: str = "manager123!",
        department: Optional[str] = None
    ) -> User:
        """Create manager user."""
        attrs = {
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "role": "manager"
        }
        if department:
            attrs["department"] = department
        
        return await self.create(**attrs)
    
    async def create_worker_user(
        self,
        username: str = "worker",
        email: str = "worker@safework.test",
        password: str = "worker123!",
        employee_number: Optional[str] = None
    ) -> User:
        """Create worker user."""
        attrs = {
            "username": username,
            "email": email,
            "password_hash": self._hash_password(password),
            "role": "worker"
        }
        if employee_number:
            attrs["employee_number"] = employee_number
        
        return await self.create(**attrs)
    
    async def create_inactive_user(
        self,
        username: str = "inactive",
        email: str = "inactive@safework.test"
    ) -> User:
        """Create inactive user for testing."""
        return await self.create(
            username=username,
            email=email,
            is_active=False
        )