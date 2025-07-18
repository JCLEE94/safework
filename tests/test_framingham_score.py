"""
Framingham Risk Score 계산 정확성 검증
Framingham Risk Score calculation accuracy test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.handlers.cardiovascular import calculate_cardiovascular_risk


def test_framingham_score():
    """Framingham Risk Score 계산 테스트"""
    print("="*60)
    print("Framingham Risk Score 계산 정확성 테스트")
    print("="*60)
    
    # 테스트 케이스 정의
    test_cases = [
        {
            "name": "젊은 남성, 위험요인 없음",
            "params": {
                "age": 30,
                "gender": "male",
                "systolic_bp": 110,
                "cholesterol": 170,
                "smoking": False,
                "diabetes": False,
                "hypertension": False
            },
            "expected": {
                "risk_level": "낮음",
                "ten_year_risk_range": (1, 5)
            }
        },
        {
            "name": "중년 여성, 경도 위험",
            "params": {
                "age": 45,
                "gender": "female",
                "systolic_bp": 130,
                "cholesterol": 210,
                "smoking": False,
                "diabetes": False,
                "hypertension": True
            },
            "expected": {
                "risk_level": "보통",
                "ten_year_risk_range": (5, 10)
            }
        },
        {
            "name": "중년 남성, 다중 위험요인",
            "params": {
                "age": 55,
                "gender": "male",
                "systolic_bp": 145,
                "cholesterol": 250,
                "smoking": True,
                "diabetes": False,
                "hypertension": True
            },
            "expected": {
                "risk_level": "높음",
                "ten_year_risk_range": (10, 20)
            }
        },
        {
            "name": "고령 남성, 고위험",
            "params": {
                "age": 65,
                "gender": "male",
                "systolic_bp": 160,
                "cholesterol": 280,
                "smoking": True,
                "diabetes": True,
                "hypertension": True
            },
            "expected": {
                "risk_level": "매우높음",
                "ten_year_risk_range": (20, 30)
            }
        },
        {
            "name": "젊은 여성, 낮은 위험",
            "params": {
                "age": 35,
                "gender": "female",
                "systolic_bp": 115,
                "cholesterol": 180,
                "smoking": False,
                "diabetes": False,
                "hypertension": False
            },
            "expected": {
                "risk_level": "낮음",
                "ten_year_risk_range": (1, 5)
            }
        }
    ]
    
    # 각 테스트 케이스 실행
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n테스트: {test['name']}")
        print("-" * 40)
        
        # 위험도 계산
        result = calculate_cardiovascular_risk(**test['params'])
        
        # 결과 출력
        print(f"입력 값:")
        print(f"  - 나이: {test['params']['age']}세")
        print(f"  - 성별: {'남성' if test['params']['gender'] == 'male' else '여성'}")
        print(f"  - 혈압: {test['params']['systolic_bp']} mmHg")
        print(f"  - 콜레스테롤: {test['params']['cholesterol']} mg/dL")
        print(f"  - 흡연: {'예' if test['params']['smoking'] else '아니오'}")
        print(f"  - 당뇨: {'예' if test['params']['diabetes'] else '아니오'}")
        print(f"  - 고혈압: {'예' if test['params']['hypertension'] else '아니오'}")
        
        print(f"\n계산 결과:")
        print(f"  - 위험도 점수: {result['risk_score']}")
        print(f"  - 위험도 수준: {result['risk_level']}")
        print(f"  - 10년 위험도: {result['ten_year_risk']}%")
        print(f"  - 다음 평가: {result['next_assessment_months']}개월 후")
        
        # 검증
        risk_level_correct = result['risk_level'] == test['expected']['risk_level']
        ten_year_risk_correct = (
            test['expected']['ten_year_risk_range'][0] <= 
            result['ten_year_risk'] <= 
            test['expected']['ten_year_risk_range'][1]
        )
        
        print(f"\n검증 결과:")
        print(f"  - 위험도 수준: {'✓' if risk_level_correct else '✗'} (예상: {test['expected']['risk_level']})")
        print(f"  - 10년 위험도: {'✓' if ten_year_risk_correct else '✗'} (예상 범위: {test['expected']['ten_year_risk_range'][0]}-{test['expected']['ten_year_risk_range'][1]}%)")
        
        if risk_level_correct and ten_year_risk_correct:
            print(f"  ✓ 테스트 통과")
            passed += 1
        else:
            print(f"  ✗ 테스트 실패")
            failed += 1
        
        # 권고사항 출력
        print(f"\n권고사항:")
        for i, rec in enumerate(result['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
    
    # 전체 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"총 테스트: {len(test_cases)}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")
    print(f"성공률: {(passed/len(test_cases)*100):.1f}%")
    
    # 위험도 계산 로직 설명
    print("\n" + "="*60)
    print("Framingham Risk Score 계산 로직")
    print("="*60)
    print("1. 기본 점수 (나이)")
    print("   - 남성: 30세 미만(-9) ~ 75세 이상(13)")
    print("   - 여성: 30세 미만(-7) ~ 75세 이상(16)")
    print("\n2. 콜레스테롤 점수")
    print("   - 160 미만: 0점")
    print("   - 160-199: 4점")
    print("   - 200-239: 7점")
    print("   - 240-279: 9점")
    print("   - 280 이상: 11점")
    print("\n3. 혈압 점수")
    print("   - 120 미만: 0점")
    print("   - 120-129: 1점")
    print("   - 130-139: 2점")
    print("   - 140-159: 3점")
    print("   - 160 이상: 4점")
    print("\n4. 위험요인 가산점")
    print("   - 흡연: +4점")
    print("   - 당뇨: +5점")
    print("   - 고혈압: +2점")
    print("\n5. 위험도 수준")
    print("   - 낮음: 10년 위험도 < 5%")
    print("   - 보통: 10년 위험도 5-10%")
    print("   - 높음: 10년 위험도 10-20%")
    print("   - 매우높음: 10년 위험도 ≥ 20%")
    
    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_framingham_score()
    sys.exit(0 if success else 1)