"""Worker model builder for testing."""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from tests.builders.base_builder import BaseBuilder
from src.models.worker import Worker


class WorkerBuilder(BaseBuilder[Worker]):
    """Builder for Worker model."""
    
    def __init__(self, db_session, counter_start: int = 1):
        super().__init__(db_session)
        self._counter = counter_start
    
    def _get_default_attrs(self) -> Dict[str, Any]:
        """Get default worker attributes."""
        counter = getattr(self, '_counter', 1)
        return {
            "name": f"테스트직원{counter}",
            "employee_number": f"EMP{counter:04d}",
            "department": "건설부",
            "position": "직원",
            "employment_type": "정규직",
            "hire_date": date.today(),
            "birth_date": date(1990, 1, 1),
            "gender": "남성",
            "phone": "010-1234-5678",
            "email": f"worker{counter}@safework.test",
            "address": "서울시 강남구 테스트로 123",
            "emergency_contact": "010-9876-5432",
            "emergency_contact_relation": "가족",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    async def _create_instance(self, **attrs) -> Worker:
        """Create Worker instance."""
        if 'employee_number' not in attrs:
            attrs['employee_number'] = f"EMP{self._counter:04d}"
        
        worker = Worker(**attrs)
        self.db.add(worker)
        await self.db.flush()
        
        self._counter += 1
        return worker
    
    async def create_with_health_data(
        self,
        name: str = "건강데이터직원",
        **kwargs
    ) -> Worker:
        """Create worker with associated health data."""
        worker = await self.create(name=name, **kwargs)
        
        # Add related health data (will be created by other builders)
        # This is a placeholder for composition with other builders
        
        return worker
    
    async def create_construction_worker(
        self,
        name: str = "건설직원",
        **kwargs
    ) -> Worker:
        """Create construction worker with appropriate settings."""
        construction_attrs = {
            "department": "건설부",
            "position": "건설작업자",
            "employment_type": "정규직",
        }
        construction_attrs.update(kwargs)
        
        return await self.create(name=name, **construction_attrs)
    
    async def create_safety_manager(
        self,
        name: str = "안전관리자",
        **kwargs
    ) -> Worker:
        """Create safety manager."""
        manager_attrs = {
            "department": "안전관리부",
            "position": "안전관리자",
            "employment_type": "정규직",
        }
        manager_attrs.update(kwargs)
        
        return await self.create(name=name, **manager_attrs)
    
    async def create_temporary_worker(
        self,
        name: str = "임시직원",
        **kwargs
    ) -> Worker:
        """Create temporary worker."""
        temp_attrs = {
            "employment_type": "임시직",
            "hire_date": date.today()
        }
        temp_attrs.update(kwargs)
        
        return await self.create(name=name, **temp_attrs)
    
    async def create_multiple(
        self,
        count: int = 5,
        name_prefix: str = "직원",
        **common_attrs
    ) -> List[Worker]:
        """Create multiple workers."""
        workers = []
        for i in range(count):
            worker_attrs = {
                "name": f"{name_prefix}{i+1}",
                **common_attrs
            }
            worker = await self.create(**worker_attrs)
            workers.append(worker)
        
        return workers
    
    async def create_with_specific_department(
        self,
        department: str,
        count: int = 3
    ) -> List[Worker]:
        """Create workers in specific department."""
        return await self.create_multiple(
            count=count,
            name_prefix=f"{department}직원",
            department=department
        )
    
    async def create_inactive_worker(
        self,
        name: str = "퇴직직원",
        **kwargs
    ) -> Worker:
        """Create inactive worker."""
        return await self.create(
            name=name,
            is_active=False,
            **kwargs
        )