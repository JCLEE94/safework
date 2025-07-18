"""
뇌심혈관계 관리 API 테스트
Cardiovascular management API tests
"""

import asyncio
import json
import httpx
from datetime import datetime, timedelta, date
from typing import Dict, Any
import sys

# Test configuration
BASE_URL = "http://localhost:3001/api/v1/cardiovascular"
HEADERS = {
    "Content-Type": "application/json"
}

# Sample test data
TEST_WORKER_ID = "test-worker-001"


async def test_risk_calculation():
    """위험도 계산 API 테스트"""
    print("\n=== 위험도 계산 API 테스트 ===")
    
    # Test cases with expected results
    test_cases = [
        {
            "name": "Low risk case",
            "data": {
                "age": 30,
                "gender": "male",
                "systolic_bp": 115,
                "cholesterol": 150,
                "smoking": False,
                "diabetes": False,
                "hypertension": False
            },
            "expected_risk_level": "낮음"
        },
        {
            "name": "Moderate risk case",
            "data": {
                "age": 45,
                "gender": "male",
                "systolic_bp": 135,
                "cholesterol": 220,
                "smoking": False,
                "diabetes": False,
                "hypertension": True
            },
            "expected_risk_level": "보통"
        },
        {
            "name": "High risk case",
            "data": {
                "age": 55,
                "gender": "male",
                "systolic_bp": 145,
                "cholesterol": 260,
                "smoking": True,
                "diabetes": False,
                "hypertension": True
            },
            "expected_risk_level": "높음"
        },
        {
            "name": "Very high risk case",
            "data": {
                "age": 65,
                "gender": "male",
                "systolic_bp": 165,
                "cholesterol": 300,
                "smoking": True,
                "diabetes": True,
                "hypertension": True
            },
            "expected_risk_level": "매우높음"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            try:
                response = await client.post(
                    f"{BASE_URL}/risk-calculation",
                    headers=HEADERS,
                    json=test_case["data"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"\n✓ {test_case['name']}:")
                    print(f"  - Risk score: {result['risk_score']}")
                    print(f"  - Risk level: {result['risk_level']}")
                    print(f"  - 10-year risk: {result['ten_year_risk']}%")
                    print(f"  - Expected: {test_case['expected_risk_level']}")
                    print(f"  - Match: {'✓' if result['risk_level'] == test_case['expected_risk_level'] else '✗'}")
                    print(f"  - Recommendations: {', '.join(result['recommendations'][:3])}")
                else:
                    print(f"\n✗ {test_case['name']} failed: {response.status_code}")
                    print(f"  Error: {response.text}")
                    
            except Exception as e:
                print(f"\n✗ {test_case['name']} error: {str(e)}")


async def test_risk_assessment_crud():
    """위험도 평가 CRUD 테스트"""
    print("\n\n=== 위험도 평가 CRUD 테스트 ===")
    
    assessment_data = {
        "worker_id": TEST_WORKER_ID,
        "assessment_date": datetime.now().isoformat(),
        "age": 50,
        "gender": "male",
        "smoking": True,
        "diabetes": False,
        "hypertension": True,
        "family_history": True,
        "obesity": False,
        "systolic_bp": 140,
        "diastolic_bp": 90,
        "cholesterol": 230,
        "ldl_cholesterol": 140,
        "hdl_cholesterol": 45,
        "triglycerides": 180,
        "blood_sugar": 105,
        "bmi": 26.5,
        "notes": "정기 건강검진 시 평가"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Create assessment
        print("\n1. 위험도 평가 생성:")
        response = await client.post(
            f"{BASE_URL}/assessments/",
            headers=HEADERS,
            json=assessment_data
        )
        
        if response.status_code == 200:
            created_assessment = response.json()
            assessment_id = created_assessment["id"]
            print(f"✓ 평가 생성 성공 (ID: {assessment_id})")
            print(f"  - 위험도 수준: {created_assessment['risk_level']}")
            print(f"  - 10년 위험도: {created_assessment['ten_year_risk']}%")
            print(f"  - 권고사항 수: {len(created_assessment['recommendations'])}")
            
            # 2. Get assessment
            print("\n2. 평가 조회:")
            response = await client.get(f"{BASE_URL}/assessments/{assessment_id}")
            if response.status_code == 200:
                print("✓ 평가 조회 성공")
                assessment = response.json()
                print(f"  - Worker ID: {assessment['worker_id']}")
                print(f"  - Risk level: {assessment['risk_level']}")
            else:
                print(f"✗ 평가 조회 실패: {response.status_code}")
            
            # 3. List assessments
            print("\n3. 평가 목록 조회:")
            response = await client.get(
                f"{BASE_URL}/assessments/",
                params={"worker_id": TEST_WORKER_ID, "limit": 10}
            )
            if response.status_code == 200:
                assessments = response.json()
                print(f"✓ 목록 조회 성공 (총 {len(assessments)}건)")
                for idx, assess in enumerate(assessments[:3]):
                    print(f"  [{idx+1}] {assess['assessment_date'][:10]} - {assess['risk_level']}")
            else:
                print(f"✗ 목록 조회 실패: {response.status_code}")
            
            # 4. Update assessment
            print("\n4. 평가 수정:")
            update_data = {
                "notes": "정기 건강검진 시 평가 - 혈압 재측정 완료",
                "systolic_bp": 135
            }
            response = await client.put(
                f"{BASE_URL}/assessments/{assessment_id}",
                headers=HEADERS,
                json=update_data
            )
            if response.status_code == 200:
                print("✓ 평가 수정 성공")
                updated = response.json()
                print(f"  - 수정된 메모: {updated['notes']}")
            else:
                print(f"✗ 평가 수정 실패: {response.status_code}")
                
        else:
            print(f"✗ 평가 생성 실패: {response.status_code}")
            print(f"  Error: {response.text}")


async def test_monitoring_management():
    """모니터링 관리 테스트"""
    print("\n\n=== 모니터링 관리 테스트 ===")
    
    monitoring_data = {
        "worker_id": TEST_WORKER_ID,
        "monitoring_type": "혈압측정",
        "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "location": "사무실 건강관리실",
        "equipment_used": "자동혈압계"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Create monitoring schedule
        print("\n1. 모니터링 스케줄 생성:")
        response = await client.post(
            f"{BASE_URL}/monitoring/",
            headers=HEADERS,
            json=monitoring_data
        )
        
        if response.status_code == 200:
            created_monitoring = response.json()
            monitoring_id = created_monitoring["id"]
            print(f"✓ 스케줄 생성 성공 (ID: {monitoring_id})")
            print(f"  - 모니터링 유형: {created_monitoring['monitoring_type']}")
            print(f"  - 예정일: {created_monitoring['scheduled_date'][:10]}")
            
            # 2. Update monitoring with results
            print("\n2. 모니터링 결과 업데이트:")
            update_data = {
                "is_completed": True,
                "systolic_bp": 138,
                "diastolic_bp": 88,
                "heart_rate": 72,
                "is_normal": False,
                "abnormal_findings": "경계성 고혈압 관찰됨",
                "action_required": True,
                "next_monitoring_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = await client.put(
                f"{BASE_URL}/monitoring/{monitoring_id}",
                headers=HEADERS,
                json=update_data
            )
            
            if response.status_code == 200:
                updated = response.json()
                print("✓ 모니터링 업데이트 성공")
                print(f"  - 완료 여부: {updated['is_completed']}")
                print(f"  - 이상 소견: {updated['abnormal_findings']}")
                print(f"  - 조치 필요: {updated['action_required']}")
            else:
                print(f"✗ 모니터링 업데이트 실패: {response.status_code}")
            
            # 3. List monitoring schedules
            print("\n3. 모니터링 목록 조회:")
            response = await client.get(
                f"{BASE_URL}/monitoring/",
                params={"worker_id": TEST_WORKER_ID}
            )
            
            if response.status_code == 200:
                schedules = response.json()
                print(f"✓ 목록 조회 성공 (총 {len(schedules)}건)")
                for idx, schedule in enumerate(schedules[:3]):
                    status = "완료" if schedule['is_completed'] else "대기"
                    print(f"  [{idx+1}] {schedule['monitoring_type']} - {status}")
            else:
                print(f"✗ 목록 조회 실패: {response.status_code}")
                
        else:
            print(f"✗ 스케줄 생성 실패: {response.status_code}")
            print(f"  Error: {response.text}")


async def test_emergency_response():
    """응급상황 대응 테스트"""
    print("\n\n=== 응급상황 대응 테스트 ===")
    
    emergency_data = {
        "worker_id": TEST_WORKER_ID,
        "incident_datetime": datetime.now().isoformat(),
        "incident_location": "3층 작업장",
        "incident_description": "작업 중 흉통 호소",
        "symptoms": ["흉통", "호흡곤란", "발한"],
        "vital_signs": {
            "blood_pressure": "160/100",
            "heart_rate": 110,
            "respiratory_rate": 24,
            "oxygen_saturation": 94
        },
        "consciousness_level": "의식 명료",
        "first_aid_provided": True,
        "first_aid_details": "안정 자세 유지, 산소 공급, 아스피린 투여",
        "emergency_call_made": True,
        "hospital_transport": True,
        "hospital_name": "서울대학교병원",
        "response_team": ["안전관리자", "보건관리자", "응급구조사"],
        "primary_responder": "김보건",
        "response_time": 5
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Create emergency response
        print("\n1. 응급상황 기록 생성:")
        response = await client.post(
            f"{BASE_URL}/emergency/",
            headers=HEADERS,
            json=emergency_data
        )
        
        if response.status_code == 200:
            created_response = response.json()
            response_id = created_response["id"]
            print(f"✓ 응급상황 기록 생성 성공 (ID: {response_id})")
            print(f"  - 발생 장소: {created_response['incident_location']}")
            print(f"  - 상태: {created_response['status']}")
            print(f"  - 대응 시간: {created_response['response_time']}분")
            
            # 2. List emergency responses
            print("\n2. 응급상황 목록 조회:")
            response = await client.get(
                f"{BASE_URL}/emergency/",
                params={"worker_id": TEST_WORKER_ID}
            )
            
            if response.status_code == 200:
                responses = response.json()
                print(f"✓ 목록 조회 성공 (총 {len(responses)}건)")
                for idx, resp in enumerate(responses[:3]):
                    print(f"  [{idx+1}] {resp['incident_datetime'][:16]} - {resp['incident_location']}")
            else:
                print(f"✗ 목록 조회 실패: {response.status_code}")
                
        else:
            print(f"✗ 응급상황 기록 생성 실패: {response.status_code}")
            print(f"  Error: {response.text}")


async def test_prevention_education():
    """예방 교육 테스트"""
    print("\n\n=== 예방 교육 테스트 ===")
    
    education_data = {
        "title": "뇌심혈관질환 예방 교육",
        "description": "고혈압, 당뇨병 관리 및 생활습관 개선 교육",
        "target_audience": "고위험군 근로자",
        "education_type": "집합교육",
        "scheduled_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "duration_minutes": 60,
        "location": "본사 대회의실",
        "curriculum": [
            "뇌심혈관질환의 이해",
            "위험요인 관리",
            "생활습관 개선방법",
            "응급상황 대처법"
        ],
        "materials": ["교육자료.pdf", "실습키트"],
        "learning_objectives": [
            "뇌심혈관질환 위험요인 인지",
            "자가관리 방법 습득",
            "응급상황 대처능력 향상"
        ],
        "target_participants": 30,
        "instructor": "김건강 산업보건의",
        "organizer": "보건관리팀"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Create education program
        print("\n1. 교육 프로그램 생성:")
        response = await client.post(
            f"{BASE_URL}/education/",
            headers=HEADERS,
            json=education_data
        )
        
        if response.status_code == 200:
            created_education = response.json()
            education_id = created_education["id"]
            print(f"✓ 교육 프로그램 생성 성공 (ID: {education_id})")
            print(f"  - 교육명: {created_education['title']}")
            print(f"  - 예정일: {created_education['scheduled_date'][:10]}")
            print(f"  - 목표 인원: {created_education['target_participants']}명")
            
            # 2. List education programs
            print("\n2. 교육 프로그램 목록 조회:")
            response = await client.get(
                f"{BASE_URL}/education/",
                params={"is_completed": False}
            )
            
            if response.status_code == 200:
                programs = response.json()
                print(f"✓ 목록 조회 성공 (총 {len(programs)}건)")
                for idx, program in enumerate(programs[:3]):
                    status = "완료" if program['is_completed'] else "예정"
                    print(f"  [{idx+1}] {program['title']} - {status}")
            else:
                print(f"✗ 목록 조회 실패: {response.status_code}")
                
        else:
            print(f"✗ 교육 프로그램 생성 실패: {response.status_code}")
            print(f"  Error: {response.text}")


async def test_statistics():
    """통계 API 테스트"""
    print("\n\n=== 통계 API 테스트 ===")
    
    async with httpx.AsyncClient() as client:
        print("\n통계 정보 조회:")
        response = await client.get(f"{BASE_URL}/statistics")
        
        if response.status_code == 200:
            stats = response.json()
            print("✓ 통계 조회 성공")
            print(f"\n[전체 평가 통계]")
            print(f"  - 총 평가 건수: {stats['total_assessments']}")
            print(f"  - 고위험군: {stats['high_risk_count']}")
            print(f"  - 중간위험군: {stats['moderate_risk_count']}")
            print(f"  - 저위험군: {stats['low_risk_count']}")
            
            print(f"\n[모니터링 통계]")
            print(f"  - 진행중인 모니터링: {stats['active_monitoring']}")
            print(f"  - 지연된 모니터링: {stats['overdue_monitoring']}")
            print(f"  - 이달 완료: {stats['completed_this_month']}")
            
            print(f"\n[응급상황 통계]")
            print(f"  - 이달 응급상황: {stats['emergency_cases_this_month']}")
            if stats['emergency_response_time_avg']:
                print(f"  - 평균 대응시간: {stats['emergency_response_time_avg']}분")
            
            print(f"\n[교육 통계]")
            print(f"  - 예정된 교육: {stats['scheduled_education']}")
            print(f"  - 완료된 교육: {stats['completed_education']}")
            if stats['education_effectiveness_avg']:
                print(f"  - 평균 효과성: {stats['education_effectiveness_avg']:.1f}")
            
            print(f"\n[위험도별 분포]")
            for level, count in stats['by_risk_level'].items():
                print(f"  - {level}: {count}명")
                
        else:
            print(f"✗ 통계 조회 실패: {response.status_code}")
            print(f"  Error: {response.text}")


async def main():
    """전체 테스트 실행"""
    print("="*60)
    print("뇌심혈관계 관리 시스템 API 테스트")
    print("="*60)
    
    try:
        # Run all tests
        await test_risk_calculation()
        await test_risk_assessment_crud()
        await test_monitoring_management()
        await test_emergency_response()
        await test_prevention_education()
        await test_statistics()
        
        print("\n" + "="*60)
        print("✓ 모든 API 테스트 완료")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 테스트 중 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())