-- SafeWork Pro 샘플 데이터 생성 스크립트
-- 시스템 100% 완성도를 위한 기본 데이터

-- 1. 추가 근로자 데이터 (10명)
INSERT INTO workers (name, employee_id, gender, department, position, employment_type, work_type, hire_date, birth_date, phone, emergency_contact, health_status, is_active)
VALUES 
('김철수', 'EMP001', '남성', '건설팀', '팀장', '정규직', '건설', '2020-03-15', '1980-05-20', '010-1111-2222', '010-1111-3333', 'normal', true),
('이영희', 'EMP002', '여성', '안전팀', '대리', '정규직', '안전관리', '2021-06-01', '1985-08-15', '010-2222-3333', '010-2222-4444', 'normal', true),
('박민수', 'EMP003', '남성', '전기팀', '사원', '정규직', '전기', '2022-01-10', '1990-03-25', '010-3333-4444', '010-3333-5555', 'normal', true),
('정수진', 'EMP004', '여성', '관리팀', '과장', '정규직', '사무', '2019-09-01', '1982-12-10', '010-4444-5555', '010-4444-6666', 'normal', true),
('홍길동', 'EMP005', '남성', '배관팀', '기술자', '계약직', '배관', '2023-03-01', '1988-07-30', '010-5555-6666', '010-5555-7777', 'caution', true),
('김미경', 'EMP006', '여성', '도장팀', '반장', '정규직', '도장', '2020-11-15', '1983-04-18', '010-6666-7777', '010-6666-8888', 'normal', true),
('이준호', 'EMP007', '남성', '용접팀', '기술자', '정규직', '용접', '2021-08-20', '1987-09-05', '010-7777-8888', '010-7777-9999', 'normal', true),
('박서연', 'EMP008', '여성', '품질팀', '주임', '정규직', '품질관리', '2022-05-10', '1992-02-28', '010-8888-9999', '010-8888-0000', 'normal', true),
('최동욱', 'EMP009', '남성', '철근팀', '작업자', '일용직', '철근', '2024-01-15', '1995-11-12', '010-9999-0000', '010-9999-1111', 'normal', true),
('강민지', 'EMP010', '여성', '환경팀', '대리', '정규직', '환경관리', '2021-04-01', '1989-06-22', '010-0000-1111', '010-0000-2222', 'normal', true)
ON CONFLICT (employee_id) DO NOTHING;

-- 2. 건강진단 데이터 (20건)
INSERT INTO health_exams (worker_id, exam_date, exam_type, exam_agency, exam_result, blood_pressure_high, blood_pressure_low, blood_sugar, cholesterol, bmi, vision_left, vision_right, hearing_left, hearing_right, special_findings, recommendations, next_exam_date)
SELECT 
    w.id,
    CURRENT_DATE - INTERVAL '30 days' * (ROW_NUMBER() OVER ()) AS exam_date,
    CASE WHEN ROW_NUMBER() OVER () % 3 = 0 THEN '특수건강진단' ELSE '일반건강진단' END,
    '대한산업보건협회',
    CASE WHEN ROW_NUMBER() OVER () % 10 = 0 THEN '요관찰' ELSE '정상' END,
    120 + (RANDOM() * 20)::INT,
    70 + (RANDOM() * 15)::INT,
    90 + (RANDOM() * 30)::INT,
    180 + (RANDOM() * 40)::INT,
    20 + (RANDOM() * 8)::FLOAT,
    0.8 + (RANDOM() * 0.4)::FLOAT,
    0.8 + (RANDOM() * 0.4)::FLOAT,
    20 + (RANDOM() * 10)::INT,
    20 + (RANDOM() * 10)::INT,
    CASE WHEN ROW_NUMBER() OVER () % 5 = 0 THEN '경미한 이상 소견' ELSE NULL END,
    '규칙적인 운동 권장, 금연 권고',
    CURRENT_DATE + INTERVAL '365 days'
FROM workers w
LIMIT 20;

-- 3. 화학물질 데이터 (15건)
INSERT INTO chemical_substances (name, cas_number, classification, hazard_type, usage_area, exposure_limit, health_effects, safety_measures, msds_file_path, is_carcinogen, is_active)
VALUES 
('벤젠', '71-43-2', '유기용제', '발암물질', 'A구역 도장작업', '1 ppm', '백혈병, 중추신경계 장애', '방독마스크 착용, 환기 필수', '/msds/benzene.pdf', true, true),
('톨루엔', '108-88-3', '유기용제', '신경독성', 'B구역 도장작업', '50 ppm', '중추신경계 억제, 간독성', '방독마스크 착용, 피부보호', '/msds/toluene.pdf', false, true),
('포름알데히드', '50-00-0', '알데히드류', '발암물질', 'C구역 접착작업', '0.5 ppm', '비인두암, 백혈병', '전면형 방독마스크 착용', '/msds/formaldehyde.pdf', true, true),
('황산', '7664-93-9', '무기산', '부식성', '배터리실', '1 mg/m³', '화상, 호흡기 손상', '내화학장갑, 보안경 착용', '/msds/sulfuric_acid.pdf', false, true),
('암모니아', '7664-41-7', '무기화합물', '자극성', '냉동창고', '25 ppm', '호흡기 자극, 화상', '가스마스크, 환기', '/msds/ammonia.pdf', false, true),
('메탄올', '67-56-1', '알코올류', '독성', '세척작업', '200 ppm', '시신경 손상, 대사성산증', '방독마스크, 보안경', '/msds/methanol.pdf', false, true),
('이소프로필알코올', '67-63-0', '알코올류', '인화성', '소독작업', '400 ppm', '중추신경 억제', '환기, 화기엄금', '/msds/ipa.pdf', false, true),
('아세톤', '67-64-1', '케톤류', '인화성', '세척작업', '750 ppm', '중추신경 억제', '방폭설비, 환기', '/msds/acetone.pdf', false, true),
('크롬산', '7738-94-5', '무기산', '발암물질', '도금작업', '0.05 mg/m³', '폐암, 비중격 천공', '전면형 방독마스크', '/msds/chromic_acid.pdf', true, true),
('납', '7439-92-1', '중금속', '생식독성', '용접작업', '0.05 mg/m³', '신경독성, 빈혈', '방진마스크, 혈중납농도 검사', '/msds/lead.pdf', false, true),
('카드뮴', '7440-43-9', '중금속', '발암물질', '도금작업', '0.005 mg/m³', '신장손상, 골연화증', '방진마스크, 생물학적 모니터링', '/msds/cadmium.pdf', true, true),
('석면', '1332-21-4', '광물성분진', '발암물질', '해체작업', '0.1 개/cm³', '폐암, 중피종', '석면작업 특별안전수칙 준수', '/msds/asbestos.pdf', true, true),
('실리카', '14808-60-7', '광물성분진', '발암물질', '시멘트작업', '0.05 mg/m³', '규폐증, 폐암', '방진마스크, 습식작업', '/msds/silica.pdf', true, true),
('일산화탄소', '630-08-0', '가스', '질식성', '밀폐공간', '30 ppm', '산소결핍, 중독', '가스검지기, 환기', '/msds/co.pdf', false, true),
('황화수소', '7783-06-4', '가스', '독성', '하수처리장', '10 ppm', '호흡마비, 의식상실', '가스검지기, 송기마스크', '/msds/h2s.pdf', false, true);

-- 4. 사고보고 데이터 (10건)
INSERT INTO accident_reports (
    worker_id, accident_datetime, accident_type, accident_location, 
    injury_type, injury_body_part, severity, work_process, 
    accident_cause, accident_description, witness_names, 
    treatment_type, hospital_name, lost_work_days, 
    is_reportable, report_status
)
SELECT 
    w.id,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (ROW_NUMBER() OVER () * 30),
    CASE (ROW_NUMBER() OVER () % 5)
        WHEN 0 THEN '추락'
        WHEN 1 THEN '전도'
        WHEN 2 THEN '충돌'
        WHEN 3 THEN '협착'
        ELSE '기타'
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN 'A구역 2층'
        WHEN 1 THEN 'B구역 작업장'
        WHEN 2 THEN 'C구역 창고'
        ELSE '옥외작업장'
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN '타박상'
        WHEN 1 THEN '찰과상'
        WHEN 2 THEN '골절'
        ELSE '염좌'
    END,
    CASE (ROW_NUMBER() OVER () % 6)
        WHEN 0 THEN '머리'
        WHEN 1 THEN '팔'
        WHEN 2 THEN '다리'
        WHEN 3 THEN '허리'
        WHEN 4 THEN '손'
        ELSE '발'
    END,
    CASE (ROW_NUMBER() OVER () % 10)
        WHEN 0 THEN '중대재해'
        WHEN 1 THEN '중상'
        WHEN 2 THEN '중상'
        ELSE '경상'
    END,
    '철골 조립 작업 중',
    '안전수칙 미준수',
    '작업 중 부주의로 인한 사고 발생',
    '김철수, 이영희',
    CASE (ROW_NUMBER() OVER () % 3)
        WHEN 0 THEN '응급처치'
        WHEN 1 THEN '통원치료'
        ELSE '입원치료'
    END,
    '서울대학교병원',
    CASE (ROW_NUMBER() OVER () % 10)
        WHEN 0 THEN 30
        WHEN 1 THEN 14
        WHEN 2 THEN 7
        ELSE 0
    END,
    CASE WHEN ROW_NUMBER() OVER () % 5 = 0 THEN true ELSE false END,
    CASE (ROW_NUMBER() OVER () % 3)
        WHEN 0 THEN '보고완료'
        WHEN 1 THEN '조사중'
        ELSE '작성중'
    END
FROM workers w
LIMIT 10;

-- 5. 작업환경 측정 데이터 (30건)
INSERT INTO work_environments (
    measurement_date, area, hazard_type, hazard_name,
    measurement_value, unit, standard_value, result,
    measurement_method, equipment_used, measurer_name,
    improvement_measures, next_measurement_date
)
SELECT 
    CURRENT_DATE - INTERVAL '1 month' * (ROW_NUMBER() OVER () % 6),
    CASE (ROW_NUMBER() OVER () % 5)
        WHEN 0 THEN 'A구역'
        WHEN 1 THEN 'B구역'
        WHEN 2 THEN 'C구역'
        WHEN 3 THEN 'D구역'
        ELSE '옥외작업장'
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN '소음'
        WHEN 1 THEN '분진'
        WHEN 2 THEN '유기용제'
        ELSE '중금속'
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN '작업장 소음'
        WHEN 1 THEN '용접흄'
        WHEN 2 THEN '톨루엔'
        ELSE '납'
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN 85 + (RANDOM() * 10)::FLOAT
        WHEN 1 THEN 3 + (RANDOM() * 2)::FLOAT
        WHEN 2 THEN 40 + (RANDOM() * 20)::FLOAT
        ELSE 0.03 + (RANDOM() * 0.02)::FLOAT
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN 'dB(A)'
        WHEN 1 THEN 'mg/m³'
        WHEN 2 THEN 'ppm'
        ELSE 'mg/m³'
    END,
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN 90
        WHEN 1 THEN 5
        WHEN 2 THEN 50
        ELSE 0.05
    END,
    CASE WHEN RANDOM() > 0.3 THEN '기준이하' ELSE '기준초과' END,
    'NIOSH 공정시험법',
    'GilAir-5 개인시료채취기',
    '한국산업안전보건공단',
    CASE WHEN RANDOM() > 0.3 THEN '현재 수준 유지' ELSE '국소배기장치 설치 권고' END,
    CURRENT_DATE + INTERVAL '6 months'
FROM generate_series(1, 30);

-- 6. 건강교육 데이터 (15건)
INSERT INTO health_educations (
    title, education_date, duration_hours, educator_name,
    education_type, target_audience, participants_count,
    content_summary, materials_used, evaluation_score
)
VALUES 
('근골격계질환 예방교육', CURRENT_DATE - INTERVAL '10 days', 2, '김강사', '집합교육', '전체 근로자', 45, '올바른 작업자세, 스트레칭 방법', 'PPT, 동영상', 4.5),
('화학물질 안전취급 교육', CURRENT_DATE - INTERVAL '20 days', 3, '이전문가', '집합교육', '화학물질 취급자', 20, 'MSDS 이해, 보호구 착용법', '실습재료, 교재', 4.7),
('심폐소생술 교육', CURRENT_DATE - INTERVAL '30 days', 4, '대한적십자사', '실습교육', '안전관리자', 15, 'CPR 실습, AED 사용법', '마네킹, AED', 4.8),
('밀폐공간 작업안전', CURRENT_DATE - INTERVAL '40 days', 2, '박안전관리자', '집합교육', '밀폐공간 작업자', 25, '가스농도 측정, 환기방법', '가스측정기', 4.6),
('소음성난청 예방교육', CURRENT_DATE - INTERVAL '50 days', 1, '산업보건의', '집합교육', '소음작업자', 30, '청력보호구 착용, 청력관리', '청력보호구', 4.4),
('직무스트레스 관리', CURRENT_DATE - INTERVAL '60 days', 2, '심리상담사', '집합교육', '전체 근로자', 50, '스트레스 관리기법', '워크북', 4.3),
('뇌심혈관질환 예방', CURRENT_DATE - INTERVAL '70 days', 2, '산업의학전문의', '집합교육', '40세 이상', 35, '생활습관 개선, 위험요인 관리', 'PPT, 책자', 4.6),
('호흡보호구 착용교육', CURRENT_DATE - INTERVAL '80 days', 1, '안전보건관리자', '실습교육', '분진작업자', 20, '올바른 착용법, 밀착도 검사', '각종 마스크', 4.7),
('응급처치 교육', CURRENT_DATE - INTERVAL '90 days', 3, '응급구조사', '실습교육', '현장관리자', 18, '외상처치, 응급상황 대응', '응급처치 키트', 4.8),
('위험성평가 이해', CURRENT_DATE - INTERVAL '100 days', 2, '안전전문가', '집합교육', '관리감독자', 12, '위험성평가 절차, 개선방안', '사례집', 4.5),
('고소작업 안전교육', CURRENT_DATE - INTERVAL '110 days', 3, '안전관리자', '실습교육', '고소작업자', 22, '안전대 착용, 추락방지', '안전대, 안전모', 4.7),
('전기안전 교육', CURRENT_DATE - INTERVAL '120 days', 2, '전기안전기술사', '집합교육', '전기작업자', 15, '감전예방, 접지의 중요성', '전기안전 장비', 4.6),
('유해광선 예방교육', CURRENT_DATE - INTERVAL '130 days', 1, '산업위생관리자', '집합교육', '용접작업자', 18, '보안경 착용, 피부보호', '보호구 샘플', 4.4),
('중량물 취급요령', CURRENT_DATE - INTERVAL '140 days', 2, '물리치료사', '실습교육', '중량물 취급자', 28, '올바른 들기 자세', '모형, 실습도구', 4.5),
('산업안전보건법 이해', CURRENT_DATE - INTERVAL '150 days', 3, '노무사', '집합교육', '전체 근로자', 60, '법규 이해, 근로자 권리', '법령집', 4.2);

-- 7. 심혈관계 평가 샘플 데이터 (근로자별 1건씩)
INSERT INTO cardiovascular_risk_assessments (
    worker_id, assessment_date, age, gender, 
    systolic_bp, diastolic_bp, total_cholesterol, hdl_cholesterol,
    smoking_status, diabetes_status, hypertension_medication,
    risk_score, risk_level, ten_year_risk,
    recommendations, next_assessment_date
)
SELECT 
    w.id,
    CURRENT_DATE - INTERVAL '1 month',
    DATE_PART('year', AGE(w.birth_date)),
    w.gender,
    120 + (RANDOM() * 40)::INT,
    70 + (RANDOM() * 20)::INT,
    180 + (RANDOM() * 60)::INT,
    40 + (RANDOM() * 20)::INT,
    CASE WHEN RANDOM() > 0.7 THEN true ELSE false END,
    CASE WHEN RANDOM() > 0.8 THEN true ELSE false END,
    CASE WHEN RANDOM() > 0.9 THEN true ELSE false END,
    RANDOM() * 30,
    CASE 
        WHEN RANDOM() < 0.4 THEN '낮음'
        WHEN RANDOM() < 0.7 THEN '보통'
        WHEN RANDOM() < 0.9 THEN '높음'
        ELSE '매우높음'
    END,
    RANDOM() * 30,
    '규칙적인 운동, 저염식, 금연 권고',
    CURRENT_DATE + INTERVAL '1 year'
FROM workers w
WHERE NOT EXISTS (
    SELECT 1 FROM cardiovascular_risk_assessments cra 
    WHERE cra.worker_id = w.id
);

-- 8. QR 등록 토큰 샘플 (활성 토큰 5개)
INSERT INTO qr_registration_tokens (
    token, worker_data, department, position,
    expires_at, created_by, status
)
VALUES 
('DEMO-TOKEN-001', '{"name": "신규직원1", "phone": "010-1234-0001"}', '건설팀', '신입', CURRENT_TIMESTAMP + INTERVAL '24 hours', 'admin', 'pending'),
('DEMO-TOKEN-002', '{"name": "신규직원2", "phone": "010-1234-0002"}', '전기팀', '기술자', CURRENT_TIMESTAMP + INTERVAL '48 hours', 'admin', 'pending'),
('DEMO-TOKEN-003', '{"name": "신규직원3", "phone": "010-1234-0003"}', '안전팀', '관리자', CURRENT_TIMESTAMP + INTERVAL '72 hours', 'admin', 'pending'),
('DEMO-TOKEN-004', '{"name": "신규직원4", "phone": "010-1234-0004"}', '관리팀', '사무직', CURRENT_TIMESTAMP + INTERVAL '24 hours', 'admin', 'pending'),
('DEMO-TOKEN-005', '{"name": "신규직원5", "phone": "010-1234-0005"}', '품질팀', '검사원', CURRENT_TIMESTAMP + INTERVAL '48 hours', 'admin', 'pending')
ON CONFLICT (token) DO NOTHING;

-- 9. 밀폐공간 샘플 데이터
INSERT INTO confined_spaces (
    name, location, type, size, 
    hazard_types, ventilation_type, entry_procedure,
    emergency_procedure, last_inspection_date, next_inspection_date,
    status, responsible_person
)
VALUES 
('지하 저수조 A', 'A동 지하 2층', '저수조', '10m x 8m x 3m', '산소결핍, 유독가스', '강제환기', '가스측정 후 2인 1조 진입', '비상용 송기마스크 준비, 구조팀 대기', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '60 days', '정상', '안전관리팀장'),
('맨홀 B-1', 'B구역 도로', '맨홀', '직경 1.2m, 깊이 5m', '산소결핍, 황화수소', '자연환기', '가스측정, 안전벨트 착용', '긴급구조 로프 설치', CURRENT_DATE - INTERVAL '45 days', CURRENT_DATE + INTERVAL '45 days', '정상', '시설관리팀'),
('정화조 C', 'C동 지하', '정화조', '5m x 4m x 3m', '메탄가스, 황화수소', '강제환기', '완전환기 후 진입', '가스검지기 상시 작동', CURRENT_DATE - INTERVAL '20 days', CURRENT_DATE + INTERVAL '70 days', '주의', '환경관리팀'),
('배관 터널 D', 'D구역 지하', '터널', '길이 50m, 직경 2m', '산소결핍', '강제환기', '조명확보, 통신장비 휴대', '비상탈출로 확보', CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE + INTERVAL '30 days', '정상', '배관팀장'),
('저장탱크 E-1', 'E구역 옥외', '탱크', '직경 5m, 높이 6m', '유기용제 증기', '국소배기', '방폭장비 사용, 정전기 방지', '소화설비 준비', CURRENT_DATE - INTERVAL '15 days', CURRENT_DATE + INTERVAL '75 days', '정상', '화학물질관리자');

-- 결과 확인
SELECT '✅ 샘플 데이터 생성 완료' as status;
SELECT '근로자' as category, COUNT(*) as count FROM workers
UNION ALL
SELECT '건강진단' as category, COUNT(*) FROM health_exams
UNION ALL
SELECT '화학물질' as category, COUNT(*) FROM chemical_substances
UNION ALL
SELECT '사고보고' as category, COUNT(*) FROM accident_reports
UNION ALL
SELECT '작업환경측정' as category, COUNT(*) FROM work_environments
UNION ALL
SELECT '건강교육' as category, COUNT(*) FROM health_educations
UNION ALL
SELECT '심혈관평가' as category, COUNT(*) FROM cardiovascular_risk_assessments
UNION ALL
SELECT 'QR토큰' as category, COUNT(*) FROM qr_registration_tokens WHERE status = 'pending'
UNION ALL
SELECT '밀폐공간' as category, COUNT(*) FROM confined_spaces;