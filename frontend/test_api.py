import requests
import json
from datetime import datetime

import os
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3001/api/v1")

def test_workers_api():
    print("=== Workers API Test ===")
    
    # 1. Create worker
    worker_data = {
        "name": "테스트 근로자",
        "employee_id": "2024001",
        "department": "건설부",
        "position": "작업반장",
        "phone": "010-1234-5678",
        "email": "test@example.com",
        "employment_type": "정규직",
        "work_type": "건설",
        "hire_date": "2024-01-01",
        "gender": "남성",
        "age": 35
    }
    
    response = requests.post(f"{BASE_URL}/workers/", json=worker_data)
    print(f"Create Worker: {response.status_code}")
    if response.status_code == 200:
        created_worker = response.json()
        worker_id = created_worker.get('id')
        print(f"Created worker ID: {worker_id}")
        
        # 2. Get workers list
        response = requests.get(f"{BASE_URL}/workers/")
        print(f"Get Workers List: {response.status_code}, Count: {len(response.json()['items'])}")
        
        # 3. Update worker
        if worker_id:
            update_data = {"position": "수석 작업반장"}
            response = requests.patch(f"{BASE_URL}/workers/{worker_id}", json=update_data)
            print(f"Update Worker: {response.status_code}")
        
        # 4. Delete worker
        if worker_id:
            response = requests.delete(f"{BASE_URL}/workers/{worker_id}")
            print(f"Delete Worker: {response.status_code}")
    else:
        print(f"Error: {response.text}")

def test_health_exams_api():
    print("\n=== Health Exams API Test ===")
    
    # First create a worker
    worker_data = {
        "name": "건강검진 테스트",
        "employee_id": "2024002",
        "department": "생산부",
        "position": "작업자",
        "employment_type": "정규직",
        "work_type": "용접"
    }
    
    worker_response = requests.post(f"{BASE_URL}/workers/", json=worker_data)
    if worker_response.status_code == 200:
        worker_id = worker_response.json()['id']
        
        # Create health exam
        exam_data = {
            "worker_id": worker_id,
            "exam_date": datetime.now().strftime("%Y-%m-%d"),
            "exam_type": "일반건강진단",
            "exam_result": "정상",
            "findings": "특이사항 없음",
            "next_exam_date": "2025-06-01"
        }
        
        response = requests.post(f"{BASE_URL}/health-exams/", json=exam_data)
        print(f"Create Health Exam: {response.status_code}")
        if response.status_code == 200:
            print(f"Created exam ID: {response.json()['id']}")
        else:
            print(f"Error: {response.text}")
            
        # Get health exams
        response = requests.get(f"{BASE_URL}/health-exams/")
        print(f"Get Health Exams: {response.status_code}, Count: {len(response.json())}")

def test_work_environments_api():
    print("\n=== Work Environments API Test ===")
    
    # Create measurement
    measurement_data = {
        "location": "작업장 테스트",
        "measurement_type": "소음",
        "measurement_date": datetime.now().strftime("%Y-%m-%d"),
        "measured_value": 85.5,
        "standard_value": 90.0,
        "unit": "dB",
        "measurement_result": "적정",
        "notes": "테스트 측정"
    }
    
    response = requests.post(f"{BASE_URL}/work-environments/", json=measurement_data)
    print(f"Create Measurement: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Created measurement: {response.json()}")
    else:
        print(f"Error: {response.text}")
    
    # Get measurements
    response = requests.get(f"{BASE_URL}/work-environments/")
    print(f"Get Measurements: {response.status_code}")

def test_education_api():
    print("\n=== Education API Test ===")
    
    # Create education
    education_data = {
        "education_date": datetime.now().strftime("%Y-%m-%d"),
        "education_type": "정기안전교육",
        "subject": "작업장 안전수칙",
        "instructor": "안전관리자",
        "duration_hours": 2,
        "participants": ["김철수", "이영희", "박민수"],
        "status": "완료"
    }
    
    response = requests.post(f"{BASE_URL}/educations/", json=education_data)
    print(f"Create Education: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Created education ID: {response.json().get('id')}")
    else:
        print(f"Error: {response.text}")

def test_chemicals_api():
    print("\n=== Chemicals API Test ===")
    
    # Create chemical
    chemical_data = {
        "name": "아세톤",
        "cas_number": "67-64-1",
        "danger_grade": "보통",
        "usage_amount": 100.5,
        "unit": "kg",
        "storage_location": "화학물질 보관소 A",
        "msds_available": True,
        "last_updated": datetime.now().strftime("%Y-%m-%d")
    }
    
    response = requests.post(f"{BASE_URL}/chemicals/", json=chemical_data)
    print(f"Create Chemical: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Created chemical ID: {response.json().get('id')}")
    else:
        print(f"Error: {response.text}")

def test_accidents_api():
    print("\n=== Accidents API Test ===")
    
    # Create accident
    accident_data = {
        "accident_date": datetime.now().strftime("%Y-%m-%d"),
        "accident_time": "14:30",
        "location": "작업장 B동",
        "victim_name": "테스트 피해자",
        "accident_type": "넘어짐",
        "injury_type": "타박상",
        "injury_severity": "경미",
        "cause": "바닥 미끄러움",
        "treatment": "응급처치 후 병원 이송",
        "reporter": "안전관리자"
    }
    
    response = requests.post(f"{BASE_URL}/accidents/", json=accident_data)
    print(f"Create Accident: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Created accident ID: {response.json().get('id')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_workers_api()
    test_health_exams_api()
    test_work_environments_api()
    test_education_api()
    test_chemicals_api()
    test_accidents_api()
EOF < /dev/null
