-- Create enum types
CREATE TYPE confinedspacetype AS ENUM (
    '탱크', '맨홀', '배관', '피트', '사일로', 
    '터널', '보일러', '용광로', '용기', '기타'
);

CREATE TYPE hazardtype AS ENUM (
    '산소결핍', '유독가스', '가연성가스', '익사', '매몰',
    '고온', '저온', '감전', '기계적위험', '기타'
);

CREATE TYPE workpermitstatus AS ENUM (
    '작성중', '제출됨', '승인됨', '작업중', 
    '완료됨', '취소됨', '만료됨'
);

-- Create confined_spaces table
CREATE TABLE confined_spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    type confinedspacetype NOT NULL,
    description TEXT,
    
    -- 공간 특성
    volume FLOAT,
    depth FLOAT,
    entry_points INTEGER DEFAULT 1,
    ventilation_type VARCHAR(50),
    
    -- 위험 요인
    hazards JSON,
    oxygen_level_normal FLOAT,
    
    -- 관리 정보
    responsible_person VARCHAR(50),
    last_inspection_date TIMESTAMP,
    inspection_cycle_days INTEGER DEFAULT 30,
    
    -- 상태
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(50)
);

-- Create confined_space_work_permits table
CREATE TABLE confined_space_work_permits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permit_number VARCHAR(50) UNIQUE NOT NULL,
    confined_space_id UUID NOT NULL REFERENCES confined_spaces(id),
    
    -- 작업 정보
    work_description TEXT NOT NULL,
    work_purpose VARCHAR(200),
    contractor VARCHAR(100),
    
    -- 작업 일정
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    
    -- 작업자 정보
    supervisor_name VARCHAR(50) NOT NULL,
    supervisor_contact VARCHAR(20),
    workers JSON,
    
    -- 안전 조치
    hazard_assessment JSON,
    safety_measures JSON,
    required_ppe JSON,
    
    -- 가스 측정
    gas_test_required BOOLEAN DEFAULT TRUE,
    gas_test_interval_minutes INTEGER DEFAULT 60,
    gas_test_results JSON,
    
    -- 비상 대응
    emergency_contact VARCHAR(20),
    emergency_procedures TEXT,
    rescue_equipment JSON,
    
    -- 승인 정보
    status workpermitstatus DEFAULT '작성중',
    submitted_by VARCHAR(50),
    submitted_at TIMESTAMP,
    approved_by VARCHAR(50),
    approved_at TIMESTAMP,
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create confined_space_gas_measurements table
CREATE TABLE confined_space_gas_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_permit_id UUID NOT NULL REFERENCES confined_space_work_permits(id),
    
    -- 측정 정보
    measurement_time TIMESTAMP NOT NULL DEFAULT NOW(),
    measurement_location VARCHAR(100),
    measured_by VARCHAR(50) NOT NULL,
    
    -- 측정값
    oxygen_level FLOAT,
    carbon_monoxide FLOAT,
    hydrogen_sulfide FLOAT,
    methane FLOAT,
    other_gases JSON,
    
    -- 판정
    is_safe BOOLEAN NOT NULL,
    remarks TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create confined_space_safety_checklists table
CREATE TABLE confined_space_safety_checklists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    confined_space_id UUID NOT NULL REFERENCES confined_spaces(id),
    
    -- 점검 정보
    inspection_date TIMESTAMP NOT NULL DEFAULT NOW(),
    inspector_name VARCHAR(50) NOT NULL,
    
    -- 체크리스트 항목
    checklist_items JSON NOT NULL,
    
    -- 전체 평가
    overall_status VARCHAR(20),
    corrective_actions JSON,
    
    -- 서명
    inspector_signature TEXT,
    reviewer_name VARCHAR(50),
    reviewer_signature TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_confined_spaces_active ON confined_spaces(is_active);
CREATE INDEX idx_confined_spaces_location ON confined_spaces(location);
CREATE INDEX idx_work_permits_space_id ON confined_space_work_permits(confined_space_id);
CREATE INDEX idx_work_permits_status ON confined_space_work_permits(status);
CREATE INDEX idx_work_permits_scheduled ON confined_space_work_permits(scheduled_start, scheduled_end);
CREATE INDEX idx_gas_measurements_permit_id ON confined_space_gas_measurements(work_permit_id);
CREATE INDEX idx_safety_checklists_space_id ON confined_space_safety_checklists(confined_space_id);

-- Add comments
COMMENT ON TABLE confined_spaces IS '밀폐공간 정보';
COMMENT ON TABLE confined_space_work_permits IS '밀폐공간 작업 허가서';
COMMENT ON TABLE confined_space_gas_measurements IS '밀폐공간 가스 측정 기록';
COMMENT ON TABLE confined_space_safety_checklists IS '밀폐공간 안전 점검 체크리스트';