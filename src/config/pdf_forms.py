"""
PDF 양식 좌표 설정 및 필드 정보
PDF form coordinates and field information
Enhanced with validation and field types
"""

# PDF 양식별 필드 좌표 정의 (x, y 좌표 - A4 용지 기준)
# 좌표는 왼쪽 하단(0,0)에서 시작하는 PDF 좌표계 사용
# A4 크기: 595.27 x 841.89 포인트
PDF_FORM_COORDINATES = {
    "유소견자_관리대장": {
        # 실제 양식의 좌표를 매핑 (동적으로 조정 가능)
        "fields": {
            "company_name": {"x": 80, "y": 750, "label": "사업장명"},
            "department": {"x": 300, "y": 750, "label": "부서명"},
            "year": {"x": 500, "y": 750, "label": "년도"},
            "worker_name": {"x": 85, "y": 680, "label": "근로자명"},
            "employee_id": {"x": 165, "y": 680, "label": "사번"},
            "position": {"x": 220, "y": 680, "label": "직책"},
            "exam_date": {"x": 275, "y": 680, "label": "검진일"},
            "exam_agency": {"x": 350, "y": 680, "label": "검진기관"},
            "exam_result": {"x": 425, "y": 680, "label": "검진결과"},
            "opinion": {"x": 480, "y": 680, "label": "의학적 소견"},
            "manager_signature": {"x": 100, "y": 120, "label": "관리책임자 서명"},
            "creation_date": {"x": 400, "y": 120, "label": "작성일"},
        }
    },
    "MSDS_관리대장": {
        "fields": {
            "company_name": {"x": 100, "y": 780, "label": "사업장명"},
            "department": {"x": 350, "y": 780, "label": "부서명"},
            "manager": {"x": 500, "y": 780, "label": "관리책임자"},
            "chemical_name": {"x": 70, "y": 700, "label": "화학물질명"},
            "manufacturer": {"x": 150, "y": 700, "label": "제조업체"},
            "cas_number": {"x": 240, "y": 700, "label": "CAS 번호"},
            "usage": {"x": 320, "y": 700, "label": "용도"},
            "quantity": {"x": 380, "y": 700, "label": "사용량"},
            "storage_location": {"x": 440, "y": 700, "label": "보관장소"},
            "hazard_class": {"x": 500, "y": 700, "label": "유해성 분류"},
            "msds_date": {"x": 100, "y": 600, "label": "MSDS 작성일"},
            "msds_version": {"x": 250, "y": 600, "label": "버전"},
            "update_date": {"x": 400, "y": 600, "label": "갱신일"},
            "safety_measures": {"x": 80, "y": 450, "label": "안전조치사항"},
            "emergency_procedures": {"x": 80, "y": 350, "label": "응급조치방법"},
            "prepared_by": {"x": 100, "y": 150, "label": "작성자"},
            "approved_by": {"x": 300, "y": 150, "label": "승인자"},
            "date": {"x": 450, "y": 150, "label": "작성일"},
        }
    },
    "건강관리_상담방문_일지": {
        "fields": {
            "visit_date": {"x": 120, "y": 720, "label": "방문일자"},
            "site_name": {"x": 280, "y": 720, "label": "현장명"},
            "weather": {"x": 450, "y": 720, "label": "날씨"},
            "counselor": {"x": 120, "y": 690, "label": "상담자"},
            "work_type": {"x": 280, "y": 690, "label": "작업종류"},
            "worker_count": {"x": 450, "y": 690, "label": "작업인원수"},
            "participant_1": {"x": 80, "y": 640, "label": "참여자 1"},
            "participant_2": {"x": 200, "y": 640, "label": "참여자 2"},
            "participant_3": {"x": 320, "y": 640, "label": "참여자 3"},
            "participant_4": {"x": 440, "y": 640, "label": "참여자 4"},
            "counseling_topic": {"x": 80, "y": 580, "label": "상담 주제"},
            "health_issues": {"x": 80, "y": 520, "label": "건강문제"},
            "work_environment": {"x": 80, "y": 460, "label": "작업환경"},
            "improvement_suggestions": {"x": 80, "y": 400, "label": "개선사항"},
            "immediate_actions": {"x": 80, "y": 320, "label": "즉시 조치사항"},
            "follow_up_actions": {"x": 80, "y": 280, "label": "추후 조치사항"},
            "next_visit_plan": {"x": 80, "y": 240, "label": "다음 방문 계획"},
            "counselor_signature": {"x": 100, "y": 150, "label": "상담자 서명"},
            "manager_signature": {"x": 300, "y": 150, "label": "관리자 서명"},
            "signature_date": {"x": 450, "y": 150, "label": "서명일"},
        }
    },
    "특별관리물질_취급일지": {
        "fields": {
            "work_date": {"x": 120, "y": 750, "label": "작업일자"},
            "department": {"x": 300, "y": 750, "label": "부서"},
            "weather": {"x": 450, "y": 750, "label": "날씨"},
            "chemical_name": {"x": 120, "y": 710, "label": "특별관리물질명"},
            "manufacturer": {"x": 300, "y": 710, "label": "제조업체"},
            "cas_number": {"x": 450, "y": 710, "label": "CAS 번호"},
            "work_location": {"x": 120, "y": 670, "label": "작업장소"},
            "work_content": {"x": 280, "y": 670, "label": "작업내용"},
            "work_method": {"x": 440, "y": 670, "label": "작업방법"},
            "worker_name": {"x": 120, "y": 630, "label": "작업자명"},
            "worker_id": {"x": 220, "y": 630, "label": "사번"},
            "work_experience": {"x": 320, "y": 630, "label": "작업경력"},
            "health_status": {"x": 420, "y": 630, "label": "건강상태"},
            "start_time": {"x": 120, "y": 590, "label": "시작시간"},
            "end_time": {"x": 200, "y": 590, "label": "종료시간"},
            "duration": {"x": 280, "y": 590, "label": "작업시간"},
            "quantity_used": {"x": 380, "y": 590, "label": "사용량"},
            "concentration": {"x": 460, "y": 590, "label": "농도"},
            "respiratory_protection": {"x": 120, "y": 520, "label": "호흡보호구"},
            "hand_protection": {"x": 220, "y": 520, "label": "손 보호구"},
            "eye_protection": {"x": 320, "y": 520, "label": "눈 보호구"},
            "body_protection": {"x": 420, "y": 520, "label": "신체 보호구"},
            "ventilation_status": {"x": 80, "y": 460, "label": "환기시설"},
            "emergency_equipment": {"x": 80, "y": 420, "label": "비상장비"},
            "safety_procedures": {"x": 80, "y": 380, "label": "안전절차"},
            "waste_disposal": {"x": 80, "y": 340, "label": "폐기물 처리"},
            "special_notes": {"x": 80, "y": 280, "label": "특이사항"},
            "corrective_actions": {"x": 80, "y": 240, "label": "시정조치"},
            "health_symptoms": {"x": 80, "y": 200, "label": "건강이상"},
            "worker_signature": {"x": 100, "y": 120, "label": "작업자 서명"},
            "supervisor_signature": {"x": 250, "y": 120, "label": "감독자 서명"},
            "manager_signature": {"x": 400, "y": 120, "label": "관리자 서명"},
            "signature_date": {"x": 500, "y": 120, "label": "서명일"},
        }
    },
}

# 사용 가능한 PDF 양식 목록
AVAILABLE_PDF_FORMS = [
    {
        "id": "유소견자_관리대장",
        "name": "유소견자 관리대장",
        "name_korean": "유소견자 관리대장",
        "description": "근로자 건강검진 유소견자 관리 양식",
        "category": "관리대장",
        "source_file": "003_유소견자_관리대장.xlsx",
        "source_path": "03-관리대장/003_유소견자_관리대장.xlsx",
    },
    {
        "id": "MSDS_관리대장",
        "name": "MSDS 관리대장",
        "name_korean": "MSDS 관리대장",
        "description": "화학물질 안전보건자료 관리 양식",
        "category": "관리대장",
        "source_file": "001_MSDS_관리대장.xls",
        "source_path": "03-관리대장/001_MSDS_관리대장.xls",
    },
    {
        "id": "건강관리_상담방문_일지",
        "name": "건강관리 상담방문 일지",
        "name_korean": "건강관리 상담방문 일지",
        "description": "근로자 건강관리 상담 방문 기록 양식",
        "category": "건강관리",
        "source_file": "002_건강관리_상담방문_일지.xls",
        "source_path": "03-관리대장/002_건강관리_상담방문_일지.xls",
    },
    {
        "id": "특별관리물질_취급일지",
        "name": "특별관리물질 취급일지",
        "name_korean": "특별관리물질 취급일지",
        "description": "특별관리물질 취급 작업 기록 양식",
        "category": "특별관리물질",
        "source_file": "003_특별관리물질_취급일지_A형.docx",
        "source_path": "07-특별관리물질/003_특별관리물질_취급일지_A형.docx",
    },
]

# 필드 라벨 매핑
FIELD_LABELS = {
    "worker_name": "근로자명",
    "employee_id": "사번",
    "exam_date": "검진일",
    "exam_agency": "검진기관",
    "exam_result": "검진결과",
    "opinion": "의학적 소견",
    "work_fitness": "작업적합성",
    "action_taken": "사후조치",
    "follow_up_date": "추적관리일정",
    "counselor": "상담자",
    "date": "작성일",
    "chemical_name": "화학물질명",
    "manufacturer": "제조업체",
    "cas_number": "CAS번호",
    "usage": "용도",
    "quantity": "사용량",
    "storage_location": "보관장소",
    "hazard_class": "유해성분류",
    "safety_measures": "안전조치",
    "msds_date": "MSDS작성일",
    "manager": "관리책임자",
    "update_date": "갱신일",
    "visit_date": "방문일자",
    "site_name": "현장명",
    "weather": "날씨",
    "work_type": "작업종류",
    "worker_count": "작업인원",
    "counseling_content": "상담내용",
    "action_items": "조치사항",
    "next_visit": "다음방문예정",
    "counselor_name": "상담자명",
    "signature_date": "서명일",
    "work_location": "작업장소",
    "work_content": "작업내용",
    "start_time": "시작시간",
    "end_time": "종료시간",
    "quantity_used": "사용량",
    "protective_equipment": "보호구착용",
    "signature": "서명",
    "company_name": "사업장명",
    "department": "부서명",
    "year": "년도",
    "position": "직책",
    "creation_date": "작성일",
    "manager_signature": "관리책임자 서명",
    "msds_version": "버전",
    "emergency_procedures": "응급조치방법",
    "prepared_by": "작성자",
    "approved_by": "승인자",
    "participant_1": "참여자 1",
    "participant_2": "참여자 2",
    "participant_3": "참여자 3",
    "participant_4": "참여자 4",
    "counseling_topic": "상담 주제",
    "health_issues": "건강문제",
    "work_environment": "작업환경",
    "improvement_suggestions": "개선사항",
    "immediate_actions": "즉시 조치사항",
    "follow_up_actions": "추후 조치사항",
    "next_visit_plan": "다음 방문 계획",
    "counselor_signature": "상담자 서명",
    "work_method": "작업방법",
    "worker_id": "사번",
    "work_experience": "작업경력",
    "health_status": "건강상태",
    "duration": "작업시간",
    "concentration": "농도",
    "respiratory_protection": "호흡보호구",
    "hand_protection": "손 보호구",
    "eye_protection": "눈 보호구",
    "body_protection": "신체 보호구",
    "ventilation_status": "환기시설",
    "emergency_equipment": "비상장비",
    "safety_procedures": "안전절차",
    "waste_disposal": "폐기물 처리",
    "special_notes": "특이사항",
    "corrective_actions": "시정조치",
    "health_symptoms": "건강이상",
    "worker_signature": "작업자 서명",
    "supervisor_signature": "감독자 서명",
}

# 필드 타입 정의
FIELD_TYPES = {
    # 날짜 타입 필드
    "visit_date": "date",
    "exam_date": "date",
    "msds_date": "date",
    "update_date": "date",
    "creation_date": "date",
    "date": "date",
    # 숫자 타입 필드
    "worker_count": "number",
    "quantity": "number",
    "concentration": "number",
    "duration": "number",
    "year": "number",
    # 서명 타입 필드
    "counselor_signature": "signature",
    "manager_signature": "signature",
    "prepared_by": "signature",
    "approved_by": "signature",
    "worker_signature": "signature",
    "supervisor_signature": "signature",
    # 텍스트 영역 필드
    "health_issues": "textarea",
    "work_environment": "textarea",
    "improvement_suggestions": "textarea",
    "immediate_actions": "textarea",
    "follow_up_actions": "textarea",
    "next_visit_plan": "textarea",
    "safety_measures": "textarea",
    "emergency_procedures": "textarea",
    "opinion": "textarea",
    "corrective_actions": "textarea",
    "special_notes": "textarea",
}

# 필드 옵션 정의
FIELD_OPTIONS = {
    "work_type": [
        "건설",
        "전기",
        "배관",
        "도장",
        "용접",
        "철근",
        "콘크리트",
        "조적",
        "타일",
        "방수",
    ],
    "hazard_class": ["1급(고위험)", "2급(중위험)", "3급(저위험)", "해당없음"],
    "exam_result": ["정상", "주의", "관찰", "치료", "업무전환"],
    "health_status": ["양호", "보통", "주의", "이상"],
    "ventilation_status": ["양호", "보통", "불량", "해당없음"],
}

# 사용 가능한 PDF 양식 목록
AVAILABLE_PDF_FORMS = [
    {
        "form_id": "유소견자_관리대장",
        "name": "유소견자 관리대장",
        "category": "register",
        "description": "건강진단 유소견자 관리",
        "template_path": "03-관리대장/003_유소견자_관리대장.xlsx",
    },
    {
        "form_id": "MSDS_관리대장",
        "name": "MSDS 관리대장",
        "category": "register",
        "description": "화학물질 안전보건자료 관리",
        "template_path": "03-관리대장/001_MSDS_관리대장.xls",
    },
    {
        "form_id": "건강관리_상담방문_일지",
        "name": "건강관리 상담방문 일지",
        "category": "register",
        "description": "보건관리자의 정기 상담방문 기록",
        "template_path": "03-관리대장/002_건강관리_상담방문_일지.xls",
    },
]


# PDF 좌표 유효성 검사
def validate_coordinates(form_id: str) -> bool:
    """PDF 양식 좌표의 유효성을 검사합니다."""
    if form_id not in PDF_FORM_COORDINATES:
        return False

    form_data = PDF_FORM_COORDINATES[form_id]

    # A4 크기 기준 좌표 범위 검사 (595 x 842 points)
    max_width = 595
    max_height = 842

    for field_name, field_info in form_data["fields"].items():
        if isinstance(field_info, dict):
            x, y = field_info.get("x", 0), field_info.get("y", 0)
        else:
            x, y = field_info

        if not (0 <= x <= max_width and 0 <= y <= max_height):
            print(
                f"경고: {form_id}의 {field_name} 필드 좌표가 범위를 벗어남: ({x}, {y})"
            )
            return False

    return True


# 모든 양식 좌표 검증
def validate_all_coordinates() -> dict:
    """모든 PDF 양식 좌표를 검증합니다."""
    results = {}

    for form_id in PDF_FORM_COORDINATES.keys():
        results[form_id] = validate_coordinates(form_id)

    return results


# 필드 정보 통합 반환
def get_field_info(form_id: str, field_name: str) -> dict:
    """특정 필드의 전체 정보를 반환합니다."""
    if form_id not in PDF_FORM_COORDINATES:
        return None

    if field_name not in PDF_FORM_COORDINATES[form_id]["fields"]:
        return None

    field_data = PDF_FORM_COORDINATES[form_id]["fields"][field_name]

    if isinstance(field_data, dict):
        x, y = field_data.get("x", 0), field_data.get("y", 0)
        label = field_data.get("label", FIELD_LABELS.get(field_name, field_name))
    else:
        x, y = field_data
        label = FIELD_LABELS.get(field_name, field_name)

    return {
        "name": field_name,
        "label": label,
        "coordinates": {"x": x, "y": y},
        "type": FIELD_TYPES.get(field_name, "text"),
        "options": FIELD_OPTIONS.get(field_name, []),
        "required": field_name in ["company_name", "date", "manager"],  # 필수 필드
    }


# 양식별 전체 필드 정보 반환
def get_form_fields(form_id: str) -> list:
    """특정 양식의 모든 필드 정보를 반환합니다."""
    if form_id not in PDF_FORM_COORDINATES:
        return []

    fields = []
    for field_name in PDF_FORM_COORDINATES[form_id]["fields"].keys():
        field_info = get_field_info(form_id, field_name)
        if field_info:
            fields.append(field_info)

    return fields
