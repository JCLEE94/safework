-- 건강진단 예약 관리 테이블 추가
-- Add health exam appointment management tables

-- 예약 상태 ENUM 타입
CREATE TYPE appointment_status AS ENUM (
    'scheduled',    -- 예약됨
    'confirmed',    -- 확정됨
    'completed',    -- 완료됨
    'cancelled',    -- 취소됨
    'no_show',      -- 미참석
    'rescheduled'   -- 일정변경
);

-- 알림 유형 ENUM 타입
CREATE TYPE notification_type AS ENUM (
    'sms',
    'email',
    'kakao',
    'app_push'
);

-- 건강진단 예약 테이블
CREATE TABLE IF NOT EXISTS health_exam_appointments (
    id SERIAL PRIMARY KEY,
    worker_id INTEGER NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    exam_type VARCHAR(50) NOT NULL,
    
    -- 예약 정보
    scheduled_date DATE NOT NULL,
    scheduled_time VARCHAR(10),
    medical_institution VARCHAR(200) NOT NULL,
    institution_address TEXT,
    institution_phone VARCHAR(20),
    
    -- 상태 관리
    status appointment_status DEFAULT 'scheduled' NOT NULL,
    confirmed_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT,
    
    -- 알림 설정
    reminder_days_before INTEGER DEFAULT 3,
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMP,
    notification_methods TEXT, -- JSON 형식
    
    -- 추가 정보
    special_instructions TEXT,
    exam_items TEXT, -- JSON 형식
    estimated_duration INTEGER,
    
    -- 이전 예약 연결
    previous_appointment_id INTEGER REFERENCES health_exam_appointments(id),
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- 예약 알림 기록 테이블
CREATE TABLE IF NOT EXISTS appointment_notifications (
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES health_exam_appointments(id) ON DELETE CASCADE,
    
    notification_type notification_type NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent',
    
    -- 알림 내용
    recipient VARCHAR(200),
    message_content TEXT,
    
    -- 응답 정보
    response_code VARCHAR(50),
    response_message TEXT,
    delivery_confirmed_at TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_appointments_worker_id ON health_exam_appointments(worker_id);
CREATE INDEX idx_appointments_scheduled_date ON health_exam_appointments(scheduled_date);
CREATE INDEX idx_appointments_status ON health_exam_appointments(status);
CREATE INDEX idx_appointments_institution ON health_exam_appointments(medical_institution);
CREATE INDEX idx_appointments_reminder ON health_exam_appointments(scheduled_date, reminder_sent) 
    WHERE status IN ('scheduled', 'confirmed');

CREATE INDEX idx_notifications_appointment_id ON appointment_notifications(appointment_id);
CREATE INDEX idx_notifications_type_sent ON appointment_notifications(notification_type, sent_at);

-- 트리거: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_appointment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_appointment_timestamp
    BEFORE UPDATE ON health_exam_appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_appointment_updated_at();

-- 샘플 데이터 (선택사항)
-- INSERT INTO health_exam_appointments (worker_id, exam_type, scheduled_date, scheduled_time, medical_institution, institution_address, institution_phone, notification_methods, special_instructions)
-- VALUES 
-- (1, '일반건강진단', CURRENT_DATE + INTERVAL '7 days', '09:00', '서울대학교병원', '서울특별시 종로구 대학로 101', '02-2072-2114', '["sms", "email"]', '검진 전 8시간 금식 필요'),
-- (2, '특수건강진단', CURRENT_DATE + INTERVAL '14 days', '10:30', '삼성서울병원', '서울특별시 강남구 일원로 81', '02-3410-2114', '["sms", "kakao"]', '소음 측정 검사 포함');