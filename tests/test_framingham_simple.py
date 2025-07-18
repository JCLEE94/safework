"""
Framingham Risk Score 계산 정확성 검증 (단순화 버전)
Framingham Risk Score calculation accuracy test (simplified)
"""

def calculate_cardiovascular_risk(
    age: int,
    gender: str,
    systolic_bp: int,
    cholesterol: float,
    smoking: bool = False,
    diabetes: bool = False,
    hypertension: bool = False
) -> dict:
    """Framingham Risk Score를 기반으로 한 심혈관 위험도 계산"""
    
    # 기본 점수 (나이)
    if gender.lower() == "male":
        if age < 35:
            age_score = -9
        elif age < 40:
            age_score = -4
        elif age < 45:
            age_score = 0
        elif age < 50:
            age_score = 3
        elif age < 55:
            age_score = 6
        elif age < 60:
            age_score = 8
        elif age < 65:
            age_score = 10
        elif age < 70:
            age_score = 11
        elif age < 75:
            age_score = 12
        else:
            age_score = 13
    else:  # female
        if age < 35:
            age_score = -7
        elif age < 40:
            age_score = -3
        elif age < 45:
            age_score = 0
        elif age < 50:
            age_score = 3
        elif age < 55:
            age_score = 6
        elif age < 60:
            age_score = 8
        elif age < 65:
            age_score = 10
        elif age < 70:
            age_score = 12
        elif age < 75:
            age_score = 14
        else:
            age_score = 16
    
    # 콜레스테롤 점수
    if cholesterol < 160:
        chol_score = 0
    elif cholesterol < 200:
        chol_score = 4
    elif cholesterol < 240:
        chol_score = 7
    elif cholesterol < 280:
        chol_score = 9
    else:
        chol_score = 11
    
    # 혈압 점수
    if systolic_bp < 120:
        bp_score = 0
    elif systolic_bp < 130:
        bp_score = 1
    elif systolic_bp < 140:
        bp_score = 2
    elif systolic_bp < 160:
        bp_score = 3
    else:
        bp_score = 4
    
    # 위험 요인 점수
    risk_score = age_score + chol_score + bp_score
    if smoking:
        risk_score += 4
    if diabetes:
        risk_score += 5
    if hypertension:
        risk_score += 2
    
    # 10년 위험도 계산 (근사치)
    if risk_score < 0:
        ten_year_risk = 1
    elif risk_score < 5:
        ten_year_risk = 2
    elif risk_score < 10:
        ten_year_risk = 5
    elif risk_score < 15:
        ten_year_risk = 10
    elif risk_score < 20:
        ten_year_risk = 20
    else:
        ten_year_risk = 30
    
    # 위험도 수준 결정 (Korean string values directly)
    if ten_year_risk < 5:
        risk_level = "낮음"
    elif ten_year_risk < 10:
        risk_level = "보통"
    elif ten_year_risk < 20:
        risk_level = "높음"
    else:
        risk_level = "매우높음"
    
    # 권고사항 생성
    recommendations = []
    if smoking:
        recommendations.append("금연")
    if systolic_bp >= 140:
        recommendations.append("혈압 관리")
    if cholesterol >= 240:
        recommendations.append("콜레스테롤 관리")
    if diabetes:
        recommendations.append("혈당 관리")
    
    recommendations.extend([
        "규칙적인 운동",
        "건강한 식단 유지",
        "정기적인 건강검진"
    ])
    
    # 다음 평가까지 기간 (개월)
    if risk_level == "매우높음":
        next_assessment_months = 3
    elif risk_level == "높음":
        next_assessment_months = 6
    else:
        next_assessment_months = 12
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ten_year_risk": ten_year_risk,
        "recommendations": recommendations,
        "next_assessment_months": next_assessment_months
    }


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
        print(f"계산 결과:")
        print(f"  - 위험도 점수: {result['risk_score']}")
        print(f"  - 위험도 수준: {result['risk_level']}")
        print(f"  - 10년 위험도: {result['ten_year_risk']}%")
        
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
    
    # 전체 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"총 테스트: {len(test_cases)}")
    print(f"통과: {passed}")
    print(f"실패: {failed}")
    print(f"성공률: {(passed/len(test_cases)*100):.1f}%")
    
    return passed == len(test_cases)


if __name__ == "__main__":
    import sys
    success = test_framingham_score()
    sys.exit(0 if success else 1)