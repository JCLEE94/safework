-- 뇌심혈관계 관리 테이블 생성 스크립트
-- Cardiovascular management tables creation script

-- 위험도 수준 enum
CREATE TYPE risk_level AS ENUM ('낮음', '보통', '높음', '매우높음');

-- 모니터링 유형 enum
CREATE TYPE monitoring_type AS ENUM ('혈압측정', '심박수', '심전도', '혈액검사', '스트레스검사', '상담');

-- 응급상황 대응 상태 enum
CREATE TYPE emergency_response_status AS ENUM ('대기', '활성화', '진행중', '완료', '취소');

-- 뇌심혈관계 위험도 평가 테이블
CREATE TABLE cardiovascular_risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id VARCHAR(50) NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 기본 정보
    age INTEGER,
    gender VARCHAR(10),
    
    -- 위험 요인
    smoking BOOLEAN DEFAULT FALSE,
    diabetes BOOLEAN DEFAULT FALSE,
    hypertension BOOLEAN DEFAULT FALSE,
    family_history BOOLEAN DEFAULT FALSE,
    obesity BOOLEAN DEFAULT FALSE,
    
    -- 측정값
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    cholesterol FLOAT,
    ldl_cholesterol FLOAT,
    hdl_cholesterol FLOAT,
    triglycerides FLOAT,
    blood_sugar FLOAT,
    bmi FLOAT,
    
    -- 위험도 평가
    risk_score FLOAT,
    risk_level risk_level,
    ten_year_risk FLOAT,
    
    -- 권고사항
    recommendations JSONB,
    follow_up_date TIMESTAMP,
    
    -- 관리 정보
    assessed_by VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 뇌심혈관계 모니터링 스케줄 및 기록 테이블
CREATE TABLE cardiovascular_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_assessment_id UUID REFERENCES cardiovascular_risk_assessments(id),
    worker_id VARCHAR(50) NOT NULL,
    
    -- 모니터링 정보
    monitoring_type monitoring_type NOT NULL,
    scheduled_date TIMESTAMP NOT NULL,
    actual_date TIMESTAMP,
    
    -- 측정값
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    measurement_values JSONB,
    
    -- 상태 및 결과
    is_completed BOOLEAN DEFAULT FALSE,
    is_normal BOOLEAN,
    abnormal_findings TEXT,
    action_required BOOLEAN DEFAULT FALSE,
    
    -- 관리 정보
    monitored_by VARCHAR(50),
    location VARCHAR(100),
    equipment_used VARCHAR(100),
    notes TEXT,
    
    -- 다음 예약
    next_monitoring_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 응급상황 대응 기록 테이블
CREATE TABLE cardiovascular_emergency_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitoring_id UUID REFERENCES cardiovascular_monitoring(id),
    worker_id VARCHAR(50) NOT NULL,
    
    -- 응급상황 정보
    incident_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    incident_location VARCHAR(200),
    incident_description TEXT,
    
    -- 증상 및 징후
    symptoms JSONB,
    vital_signs JSONB,
    consciousness_level VARCHAR(50),
    
    -- 대응 조치
    first_aid_provided BOOLEAN DEFAULT FALSE,
    first_aid_details TEXT,
    emergency_call_made BOOLEAN DEFAULT FALSE,
    hospital_transport BOOLEAN DEFAULT FALSE,
    hospital_name VARCHAR(100),
    
    -- 대응팀 정보
    response_team JSONB,
    primary_responder VARCHAR(50),
    response_time INTEGER,
    
    -- 결과 및 후속조치
    outcome VARCHAR(100),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_plan TEXT,
    lesson_learned TEXT,
    
    -- 상태
    status emergency_response_status DEFAULT '대기',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50)
);

-- 예방 교육 프로그램 테이블
CREATE TABLE cardiovascular_prevention_education (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 교육 정보
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_audience VARCHAR(100),
    education_type VARCHAR(50),
    
    -- 일정 정보
    scheduled_date TIMESTAMP NOT NULL,
    duration_minutes INTEGER,
    location VARCHAR(100),
    
    -- 교육 내용
    curriculum JSONB,
    materials JSONB,
    learning_objectives JSONB,
    
    -- 참석자 관리
    target_participants INTEGER,
    actual_participants INTEGER,
    participant_list JSONB,
    
    -- 평가 및 피드백
    evaluation_method VARCHAR(100),
    evaluation_results JSONB,
    participant_feedback JSONB,
    effectiveness_score FLOAT,
    
    -- 관리 정보
    instructor VARCHAR(50),
    organizer VARCHAR(50),
    is_completed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_cardiovascular_risk_assessments_worker_id ON cardiovascular_risk_assessments(worker_id);
CREATE INDEX idx_cardiovascular_risk_assessments_date ON cardiovascular_risk_assessments(assessment_date);
CREATE INDEX idx_cardiovascular_risk_assessments_risk_level ON cardiovascular_risk_assessments(risk_level);

CREATE INDEX idx_cardiovascular_monitoring_worker_id ON cardiovascular_monitoring(worker_id);
CREATE INDEX idx_cardiovascular_monitoring_date ON cardiovascular_monitoring(scheduled_date);
CREATE INDEX idx_cardiovascular_monitoring_type ON cardiovascular_monitoring(monitoring_type);
CREATE INDEX idx_cardiovascular_monitoring_completed ON cardiovascular_monitoring(is_completed);

CREATE INDEX idx_cardiovascular_emergency_worker_id ON cardiovascular_emergency_responses(worker_id);
CREATE INDEX idx_cardiovascular_emergency_date ON cardiovascular_emergency_responses(incident_datetime);
CREATE INDEX idx_cardiovascular_emergency_status ON cardiovascular_emergency_responses(status);

CREATE INDEX idx_cardiovascular_education_date ON cardiovascular_prevention_education(scheduled_date);
CREATE INDEX idx_cardiovascular_education_completed ON cardiovascular_prevention_education(is_completed);

-- 트리거 함수 생성 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 적용
CREATE TRIGGER update_cardiovascular_risk_assessments_updated_at 
    BEFORE UPDATE ON cardiovascular_risk_assessments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cardiovascular_monitoring_updated_at 
    BEFORE UPDATE ON cardiovascular_monitoring 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cardiovascular_emergency_updated_at 
    BEFORE UPDATE ON cardiovascular_emergency_responses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cardiovascular_education_updated_at 
    BEFORE UPDATE ON cardiovascular_prevention_education 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 코멘트 추가
COMMENT ON TABLE cardiovascular_risk_assessments IS '뇌심혈관계 위험도 평가';
COMMENT ON TABLE cardiovascular_monitoring IS '뇌심혈관계 모니터링 스케줄 및 기록';
COMMENT ON TABLE cardiovascular_emergency_responses IS '응급상황 대응 기록';
COMMENT ON TABLE cardiovascular_prevention_education IS '예방 교육 프로그램';

COMMENT ON COLUMN cardiovascular_risk_assessments.worker_id IS '근로자 ID';
COMMENT ON COLUMN cardiovascular_risk_assessments.risk_score IS '위험도 점수';
COMMENT ON COLUMN cardiovascular_risk_assessments.ten_year_risk IS '10년 위험도(%)';

COMMENT ON COLUMN cardiovascular_monitoring.monitoring_type IS '모니터링 유형';
COMMENT ON COLUMN cardiovascular_monitoring.is_normal IS '정상 여부';
COMMENT ON COLUMN cardiovascular_monitoring.action_required IS '조치 필요 여부';

COMMENT ON COLUMN cardiovascular_emergency_responses.response_time IS '대응시간(분)';
COMMENT ON COLUMN cardiovascular_emergency_responses.follow_up_required IS '후속조치 필요 여부';

COMMENT ON COLUMN cardiovascular_prevention_education.effectiveness_score IS '효과성 점수';