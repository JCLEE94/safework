"""
뇌심혈관계 관리 API 테스트 (인증 포함)
Cardiovascular management API tests with authentication
"""

import asyncio
import json
import httpx
from datetime import datetime, timedelta, date
from typing import Dict, Any
import sys

# Test configuration
BASE_URL = "http://localhost:3001"
API_BASE = f"{BASE_URL}/api/v1/cardiovascular"

# Sample test data
TEST_WORKER_ID = "test-worker-001"


async def get_auth_token():
    """인증 토큰 획득"""
    # In development mode, auth is bypassed
    # Return a dummy token or empty headers
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"
    }


async def test_api_health():
    """API 헬스 체크"""
    print("\n=== API 헬스 체크 ===")
    
    async with httpx.AsyncClient() as client:
        # Check if the server is running
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"서버 상태: {response.status_code}")
            if response.status_code == 200:
                print("✓ 서버 정상 작동")
                print(f"  응답: {response.json()}")
        except Exception as e:
            print(f"✗ 서버 연결 실패: {str(e)}")
            return False
        
        # Check if cardiovascular endpoints exist
        headers = await get_auth_token()
        try:
            # Try GET request first to check if endpoint exists
            response = await client.get(
                f"{API_BASE}/statistics",
                headers=headers
            )
            print(f"\n통계 엔드포인트 상태: {response.status_code}")
            if response.status_code == 200:
                print("✓ 뇌심혈관계 API 엔드포인트 확인됨")
            elif response.status_code == 401:
                print("! 인증이 필요합니다")
            elif response.status_code == 404:
                print("✗ 엔드포인트를 찾을 수 없습니다")
            else:
                print(f"! 예상치 못한 응답: {response.text}")
        except Exception as e:
            print(f"✗ API 확인 실패: {str(e)}")
            
    return True


async def test_risk_calculation():
    """위험도 계산 API 테스트"""
    print("\n\n=== 위험도 계산 API 테스트 ===")
    
    headers = await get_auth_token()
    
    # Test cases with expected results
    test_cases = [
        {
            "name": "저위험 케이스",
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
            "name": "중간위험 케이스",
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
            "name": "고위험 케이스",
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
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for test_case in test_cases[:1]:  # Test just one case first
            try:
                print(f"\n테스트: {test_case['name']}")
                print(f"  요청 데이터: {json.dumps(test_case['data'], indent=2)}")
                
                response = await client.post(
                    f"{API_BASE}/risk-calculation",
                    headers=headers,
                    json=test_case["data"]
                )
                
                print(f"  응답 코드: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ 위험도 계산 성공:")
                    print(f"  - 위험도 점수: {result.get('risk_score', 'N/A')}")
                    print(f"  - 위험도 수준: {result.get('risk_level', 'N/A')}")
                    print(f"  - 10년 위험도: {result.get('ten_year_risk', 'N/A')}%")
                    print(f"  - 예상 수준: {test_case['expected_risk_level']}")
                    if result.get('risk_level') == test_case['expected_risk_level']:
                        print(f"  - 결과 일치: ✓")
                    else:
                        print(f"  - 결과 불일치: ✗")
                elif response.status_code == 401:
                    print("✗ 인증 실패 (401)")
                elif response.status_code == 404:
                    print("✗ 엔드포인트를 찾을 수 없음 (404)")
                elif response.status_code == 405:
                    print("✗ 메소드가 허용되지 않음 (405)")
                    print(f"  상세: {response.text}")
                else:
                    print(f"✗ 오류 발생: {response.status_code}")
                    print(f"  상세: {response.text}")
                    
            except Exception as e:
                print(f"✗ 테스트 중 예외 발생: {str(e)}")


async def test_statistics():
    """통계 API 테스트"""
    print("\n\n=== 통계 API 테스트 ===")
    
    headers = await get_auth_token()
    
    async with httpx.AsyncClient() as client:
        print("\n통계 정보 조회 시도:")
        try:
            response = await client.get(
                f"{API_BASE}/statistics",
                headers=headers
            )
            
            print(f"응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print("✓ 통계 조회 성공")
                print(f"\n[데이터 구조 확인]")
                for key in stats.keys():
                    print(f"  - {key}: {type(stats[key]).__name__}")
                    
                if 'total_assessments' in stats:
                    print(f"\n[평가 통계]")
                    print(f"  - 총 평가 건수: {stats['total_assessments']}")
                    print(f"  - 고위험군: {stats.get('high_risk_count', 0)}")
                    print(f"  - 중간위험군: {stats.get('moderate_risk_count', 0)}")
                    print(f"  - 저위험군: {stats.get('low_risk_count', 0)}")
            elif response.status_code == 401:
                print("✗ 인증 실패")
                print(f"  상세: {response.text}")
            elif response.status_code == 404:
                print("✗ 엔드포인트를 찾을 수 없음")
                print(f"  요청 URL: {API_BASE}/statistics")
            else:
                print(f"✗ 예상치 못한 응답: {response.status_code}")
                print(f"  상세: {response.text}")
                
        except Exception as e:
            print(f"✗ 요청 중 예외 발생: {str(e)}")


async def test_create_assessment():
    """위험도 평가 생성 테스트"""
    print("\n\n=== 위험도 평가 생성 테스트 ===")
    
    headers = await get_auth_token()
    
    assessment_data = {
        "worker_id": TEST_WORKER_ID,
        "assessment_date": datetime.now().isoformat(),
        "age": 45,
        "gender": "male",
        "smoking": False,
        "diabetes": False,
        "hypertension": True,
        "family_history": False,
        "obesity": False,
        "systolic_bp": 135,
        "diastolic_bp": 85,
        "cholesterol": 210,
        "ldl_cholesterol": 130,
        "hdl_cholesterol": 50,
        "triglycerides": 150,
        "blood_sugar": 95,
        "bmi": 24.5,
        "notes": "정기 건강검진"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            print("\n평가 데이터:")
            print(f"  - 근로자 ID: {assessment_data['worker_id']}")
            print(f"  - 나이: {assessment_data['age']}")
            print(f"  - 혈압: {assessment_data['systolic_bp']}/{assessment_data['diastolic_bp']}")
            print(f"  - 콜레스테롤: {assessment_data['cholesterol']}")
            
            response = await client.post(
                f"{API_BASE}/assessments/",
                headers=headers,
                json=assessment_data
            )
            
            print(f"\n응답 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ 평가 생성 성공")
                print(f"  - ID: {result.get('id', 'N/A')}")
                print(f"  - 위험도 수준: {result.get('risk_level', 'N/A')}")
                print(f"  - 10년 위험도: {result.get('ten_year_risk', 'N/A')}%")
                print(f"  - 권고사항 수: {len(result.get('recommendations', []))}")
                return result.get('id')
            else:
                print(f"✗ 평가 생성 실패")
                print(f"  상세: {response.text}")
                
        except Exception as e:
            print(f"✗ 요청 중 예외 발생: {str(e)}")
            
    return None


async def main():
    """전체 테스트 실행"""
    print("="*60)
    print("뇌심혈관계 관리 시스템 API 테스트 (인증 포함)")
    print("="*60)
    
    try:
        # 1. API 헬스 체크
        if not await test_api_health():
            print("\n서버가 실행 중이 아닙니다. 테스트를 중단합니다.")
            sys.exit(1)
        
        # 2. 통계 API 테스트 (가장 간단한 GET 요청)
        await test_statistics()
        
        # 3. 위험도 계산 테스트
        await test_risk_calculation()
        
        # 4. 평가 생성 테스트
        await test_create_assessment()
        
        print("\n" + "="*60)
        print("테스트 완료")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())