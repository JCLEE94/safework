-- 근로자 테이블에 새 필드 추가
ALTER TABLE workers 
ADD COLUMN IF NOT EXISTS company_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS work_category VARCHAR(100),
ADD COLUMN IF NOT EXISTS emergency_relationship VARCHAR(50),
ADD COLUMN IF NOT EXISTS safety_education_cert TEXT,
ADD COLUMN IF NOT EXISTS visa_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS visa_cert TEXT;

-- 기존 데이터에 대한 기본값 설정
UPDATE workers 
SET company_name = COALESCE(company_name, '미지정'),
    work_category = COALESCE(work_category, '일반'),
    address = COALESCE(address, ''),
    department = COALESCE(department, '작업')
WHERE company_name IS NULL OR work_category IS NULL;

-- NOT NULL 제약조건 추가
ALTER TABLE workers 
ALTER COLUMN company_name SET NOT NULL,
ALTER COLUMN work_category SET NOT NULL,
ALTER COLUMN address SET NOT NULL,
ALTER COLUMN department SET NOT NULL;