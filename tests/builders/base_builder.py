"""Base builder class for test data creation."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')


class BaseBuilder(Generic[T], ABC):
    """Base class for all test data builders."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.default_attrs = self._get_default_attrs()
    
    @abstractmethod
    def _get_default_attrs(self) -> Dict[str, Any]:
        """Get default attributes for the model."""
        pass
    
    @abstractmethod
    async def _create_instance(self, **attrs) -> T:
        """Create and save instance to database."""
        pass
    
    async def create(self, **overrides) -> T:
        """Create instance with optional attribute overrides."""
        attrs = {**self.default_attrs, **overrides}
        instance = await self._create_instance(**attrs)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    def with_attrs(self, **attrs) -> 'BaseBuilder[T]':
        """Return new builder with modified default attributes."""
        new_builder = self.__class__(self.db)
        new_builder.default_attrs = {**self.default_attrs, **attrs}
        return new_builder