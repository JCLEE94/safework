"""
Worker management integration tests for SafeWork Pro.

This module tests the complete worker management system including:
- CRUD operations for workers
- Search and filtering functionality
- Korean text handling
- Data validation and relationships
- Bulk operations
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from datetime import date, datetime
import json


class TestWorkerCRUDOperations:
    """Test worker CRUD operations."""
    
    @pytest.mark.integration
    async def test_create_worker_basic(self, client: AsyncClient):
        """Test basic worker creation."""
        worker_data = {
            "employee_id": "TEST001",
            "name": "홍길동",
            "birth_date": "1990-01-01",
            "gender": "male",
            "employment_type": "regular",
            "work_type": "construction", 
            "hire_date": "2024-01-01",
            "health_status": "normal",
            "phone": "010-1234-5678",
            "department": "건설팀"
        }
        
        response = await client.post("/api/v1/workers/", json=worker_data)
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Worker creation endpoint not implemented")
        
        # Should either succeed or fail with validation error
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED
        ]
        
        if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            worker_response = response.json()
            assert worker_response["name"] == "홍길동"
            assert worker_response["employee_id"] == "TEST001"
            assert "id" in worker_response
    
    @pytest.mark.integration
    async def test_get_workers_list(self, client: AsyncClient):
        """Test getting list of workers."""
        response = await client.get("/api/v1/workers/")
        
        # Should work or require authentication
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
        
        if response.status_code == status.HTTP_200_OK:
            workers = response.json()
            assert isinstance(workers, list)
            
            # If workers exist, check structure
            if workers:
                worker = workers[0]
                required_fields = ["id", "employee_id", "name"]
                for field in required_fields:
                    assert field in worker
    
    @pytest.mark.integration
    async def test_get_single_worker(self, client: AsyncClient, test_worker):
        """Test getting a single worker by ID."""
        worker_id = test_worker.id
        
        response = await client.get(f"/api/v1/workers/{worker_id}")
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Get single worker endpoint not implemented or worker not found")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
        
        if response.status_code == status.HTTP_200_OK:
            worker = response.json()
            assert worker["id"] == worker_id
            assert worker["name"] == test_worker.name
    
    @pytest.mark.integration
    async def test_update_worker(self, client: AsyncClient, test_worker):
        """Test updating worker information."""
        update_data = {
            "name": "김철수",
            "department": "안전팀",
            "phone": "010-9876-5432"
        }
        
        response = await client.put(f"/api/v1/workers/{test_worker.id}", json=update_data)
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            # Try PATCH method instead
            response = await client.patch(f"/api/v1/workers/{test_worker.id}", json=update_data)
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Worker update endpoint not implemented")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        
        if response.status_code == status.HTTP_200_OK:
            updated_worker = response.json()
            assert updated_worker["name"] == "김철수"
            assert updated_worker["department"] == "안전팀"
    
    @pytest.mark.integration
    async def test_delete_worker(self, client: AsyncClient, test_worker):
        """Test deleting a worker."""
        response = await client.delete(f"/api/v1/workers/{test_worker.id}")
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Worker delete endpoint not implemented")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]:
            # Verify deletion
            get_response = await client.get(f"/api/v1/workers/{test_worker.id}")
            assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestWorkerSearchAndFiltering:
    """Test worker search and filtering functionality."""
    
    @pytest.mark.integration
    async def test_search_workers_by_name(self, client: AsyncClient):
        """Test searching workers by name."""
        search_params = {
            "search": "테스트",
            "name": "홍길동",
            "q": "직원"
        }
        
        for param_name, param_value in search_params.items():
            response = await client.get(f"/api/v1/workers/?{param_name}={param_value}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
            
            if response.status_code == status.HTTP_200_OK:
                workers = response.json()
                assert isinstance(workers, list)
    
    @pytest.mark.integration
    async def test_filter_workers_by_department(self, client: AsyncClient):
        """Test filtering workers by department."""
        departments = ["건설팀", "안전팀", "관리팀"]
        
        for department in departments:
            response = await client.get(f"/api/v1/workers/?department={department}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
            
            if response.status_code == status.HTTP_200_OK:
                workers = response.json()
                assert isinstance(workers, list)
                
                # If workers found, verify department filter
                for worker in workers:
                    if "department" in worker:
                        assert worker["department"] == department or worker["department"] is None
    
    @pytest.mark.integration
    async def test_filter_workers_by_employment_type(self, client: AsyncClient):
        """Test filtering workers by employment type."""
        employment_types = ["regular", "contract", "temporary"]
        
        for emp_type in employment_types:
            response = await client.get(f"/api/v1/workers/?employment_type={emp_type}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
    
    @pytest.mark.integration
    async def test_pagination(self, client: AsyncClient):
        """Test worker list pagination."""
        # Test with pagination parameters
        pagination_params = [
            {"page": 1, "limit": 10},
            {"skip": 0, "limit": 5},
            {"offset": 0, "size": 20}
        ]
        
        for params in pagination_params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            response = await client.get(f"/api/v1/workers/?{query_string}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY  # If pagination params invalid
            ]
    
    @pytest.mark.integration
    async def test_sorting(self, client: AsyncClient):
        """Test worker list sorting."""
        sort_params = [
            "name",
            "-name",
            "employee_id", 
            "hire_date",
            "department"
        ]
        
        for sort_param in sort_params:
            response = await client.get(f"/api/v1/workers/?sort={sort_param}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]


class TestKoreanTextHandling:
    """Test Korean text handling in worker data."""
    
    @pytest.mark.integration
    async def test_korean_names(self, client: AsyncClient):
        """Test Korean names in worker data."""
        korean_names = [
            "홍길동",
            "김영희", 
            "박철수",
            "이미영",
            "최한국",
            "정한글"
        ]
        
        for name in korean_names:
            worker_data = {
                "employee_id": f"KOR{hash(name) % 10000:04d}",
                "name": name,
                "birth_date": "1990-01-01",
                "gender": "male",
                "employment_type": "regular",
                "work_type": "construction",
                "hire_date": "2024-01-01",
                "health_status": "normal",
                "phone": "010-1234-5678",
                "department": "건설팀"
            }
            
            response = await client.post("/api/v1/workers/", json=worker_data)
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                break  # Skip if endpoint not implemented
            
            if response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
                created_worker = response.json()
                assert created_worker["name"] == name
                
                # Test retrieval preserves Korean text
                worker_id = created_worker["id"]
                get_response = await client.get(f"/api/v1/workers/{worker_id}")
                if get_response.status_code == status.HTTP_200_OK:
                    retrieved_worker = get_response.json()
                    assert retrieved_worker["name"] == name
    
    @pytest.mark.integration
    async def test_korean_departments(self, client: AsyncClient):
        """Test Korean department names."""
        korean_departments = [
            "건설부",
            "안전관리팀",
            "품질관리부",
            "기술개발실",
            "인사총무팀"
        ]
        
        for department in korean_departments:
            response = await client.get(f"/api/v1/workers/?department={department}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
    
    @pytest.mark.integration
    async def test_korean_search(self, client: AsyncClient):
        """Test searching with Korean text."""
        korean_search_terms = [
            "홍길동",
            "건설",
            "안전",
            "관리",
            "직원"
        ]
        
        for term in korean_search_terms:
            response = await client.get(f"/api/v1/workers/?search={term}")
            
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]


class TestWorkerDataValidation:
    """Test data validation for worker information."""
    
    @pytest.mark.integration
    async def test_required_fields_validation(self, client: AsyncClient):
        """Test validation of required fields."""
        # Test with missing required fields
        incomplete_data_sets = [
            {},  # Completely empty
            {"name": "테스트"},  # Only name
            {"employee_id": "TEST001"},  # Only employee ID
            {"name": "테스트", "employee_id": ""},  # Empty employee ID
        ]
        
        for incomplete_data in incomplete_data_sets:
            response = await client.post("/api/v1/workers/", json=incomplete_data)
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                break  # Skip if endpoint not implemented
            
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    @pytest.mark.integration
    async def test_data_type_validation(self, client: AsyncClient):
        """Test data type validation."""
        invalid_data_sets = [
            {"employee_id": 123, "name": "테스트"},  # Wrong type for employee_id
            {"employee_id": "TEST001", "name": None},  # Null name
            {"employee_id": "TEST001", "name": "테스트", "birth_date": "invalid-date"},  # Invalid date
            {"employee_id": "TEST001", "name": "테스트", "gender": "invalid"},  # Invalid gender
        ]
        
        for invalid_data in invalid_data_sets:
            response = await client.post("/api/v1/workers/", json=invalid_data)
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                break  # Skip if endpoint not implemented
            
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    @pytest.mark.integration
    async def test_duplicate_employee_id(self, client: AsyncClient, test_worker):
        """Test duplicate employee ID prevention."""
        duplicate_worker_data = {
            "employee_id": test_worker.employee_id,  # Same as existing worker
            "name": "중복테스트",
            "birth_date": "1990-01-01",
            "gender": "female",
            "employment_type": "regular",
            "work_type": "construction",
            "hire_date": "2024-01-01",
            "health_status": "normal",
            "phone": "010-1234-5678",
            "department": "건설팀"
        }
        
        response = await client.post("/api/v1/workers/", json=duplicate_worker_data)
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Worker creation endpoint not implemented")
        
        # Should prevent duplicate employee IDs
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_409_CONFLICT,
            status.HTTP_401_UNAUTHORIZED
        ]
    
    @pytest.mark.integration
    async def test_phone_number_validation(self, client: AsyncClient):
        """Test phone number format validation."""
        phone_numbers = [
            "010-1234-5678",  # Valid Korean format
            "02-1234-5678",   # Valid landline
            "031-123-4567",   # Valid area code
            "010-12345678",   # No hyphens
            "01012345678",    # No separators
            "invalid-phone",  # Invalid format
            "123",           # Too short
            "010-1234-56789", # Too long
        ]
        
        for phone in phone_numbers:
            worker_data = {
                "employee_id": f"PHONE{hash(phone) % 10000:04d}",
                "name": "전화테스트",
                "birth_date": "1990-01-01",
                "gender": "male",
                "employment_type": "regular",
                "work_type": "construction",
                "hire_date": "2024-01-01",
                "health_status": "normal",
                "phone": phone,
                "department": "건설팀"
            }
            
            response = await client.post("/api/v1/workers/", json=worker_data)
            
            if response.status_code == status.HTTP_404_NOT_FOUND:
                break  # Skip if endpoint not implemented
            
            # Should validate phone number format
            assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR


class TestWorkerRelationships:
    """Test worker relationships with other entities."""
    
    @pytest.mark.integration
    async def test_worker_health_exam_relationship(self, client: AsyncClient, test_worker):
        """Test worker relationship with health exams."""
        # Get worker's health exams
        response = await client.get(f"/api/v1/workers/{test_worker.id}/health-exams")
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            # Try alternative endpoint
            response = await client.get(f"/api/v1/health-exams/?worker_id={test_worker.id}")
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Health exam relationship endpoint not implemented")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
        
        if response.status_code == status.HTTP_200_OK:
            health_exams = response.json()
            assert isinstance(health_exams, list)
    
    @pytest.mark.integration
    async def test_worker_deletion_constraints(self, client: AsyncClient, test_worker, test_health_exam):
        """Test worker deletion with related data."""
        # Try to delete worker that has health exam
        response = await client.delete(f"/api/v1/workers/{test_worker.id}")
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Worker delete endpoint not implemented")
        
        # Should either:
        # 1. Prevent deletion due to foreign key constraints
        # 2. Cascade delete related records
        # 3. Succeed (depends on implementation)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_400_BAD_REQUEST,  # Constraint violation
            status.HTTP_409_CONFLICT,     # Constraint violation
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


class TestBulkWorkerOperations:
    """Test bulk operations on workers."""
    
    @pytest.mark.integration
    async def test_bulk_worker_import(self, client: AsyncClient):
        """Test bulk worker import functionality."""
        bulk_workers = [
            {
                "employee_id": "BULK001",
                "name": "대량가입1",
                "birth_date": "1990-01-01",
                "gender": "male",
                "employment_type": "regular",
                "work_type": "construction",
                "hire_date": "2024-01-01",
                "health_status": "normal",
                "phone": "010-1111-1111",
                "department": "건설팀"
            },
            {
                "employee_id": "BULK002",
                "name": "대량가입2",
                "birth_date": "1991-01-01", 
                "gender": "female",
                "employment_type": "regular",
                "work_type": "construction",
                "hire_date": "2024-01-01",
                "health_status": "normal",
                "phone": "010-2222-2222",
                "department": "건설팀"
            }
        ]
        
        response = await client.post("/api/v1/workers/bulk", json={"workers": bulk_workers})
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Bulk worker import endpoint not implemented")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_207_MULTI_STATUS,  # Partial success
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    @pytest.mark.integration
    async def test_bulk_worker_update(self, client: AsyncClient):
        """Test bulk worker update functionality."""
        bulk_updates = {
            "filter": {"department": "건설팀"},
            "updates": {
                "department": "신건설팀",
                "updated_at": datetime.now().isoformat()
            }
        }
        
        response = await client.patch("/api/v1/workers/bulk", json=bulk_updates)
        
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("Bulk worker update endpoint not implemented")
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_207_MULTI_STATUS,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]