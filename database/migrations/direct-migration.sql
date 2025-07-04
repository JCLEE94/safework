-- SafeWork Pro 새 기능 마이그레이션 (직접 실행용)
-- 2025-07-04

-- Drop existing types if they exist
DROP TYPE IF EXISTS checklisttype CASCADE;
DROP TYPE IF EXISTS checkliststatus CASCADE;
DROP TYPE IF EXISTS checklistpriority CASCADE;
DROP TYPE IF EXISTS specialmaterialtype CASCADE;
DROP TYPE IF EXISTS exposurelevel CASCADE;
DROP TYPE IF EXISTS controlmeasuretype CASCADE;
DROP TYPE IF EXISTS monitoringstatus CASCADE;
DROP TYPE IF EXISTS legalformstatus CASCADE;
DROP TYPE IF EXISTS legalformpriority CASCADE;
DROP TYPE IF EXISTS legalformcategory CASCADE;
DROP TYPE IF EXISTS backupfrequency CASCADE;
DROP TYPE IF EXISTS reportlanguage CASCADE;
DROP TYPE IF EXISTS dashboardlayout CASCADE;
DROP TYPE IF EXISTS theme CASCADE;
DROP TYPE IF EXISTS language CASCADE;

-- Create enums
CREATE TYPE checklisttype AS ENUM ('safety_management', 'risk_assessment', 'accident_response', 'health_management', 'education_training', 'facility_inspection', 'environment_monitoring', 'chemical_management', 'emergency_response', 'compliance_check');
CREATE TYPE checkliststatus AS ENUM ('pending', 'in_progress', 'completed', 'overdue', 'cancelled');
CREATE TYPE checklistpriority AS ENUM ('high', 'medium', 'low');
CREATE TYPE specialmaterialtype AS ENUM ('carcinogen', 'mutagen', 'reproductive_toxin', 'respiratory_sensitizer', 'skin_sensitizer', 'toxic_gas', 'asbestos', 'silica', 'heavy_metal', 'organic_solvent');
CREATE TYPE exposurelevel AS ENUM ('none', 'low', 'medium', 'high', 'critical');
CREATE TYPE controlmeasuretype AS ENUM ('engineering', 'administrative', 'ppe', 'substitution', 'elimination');
CREATE TYPE monitoringstatus AS ENUM ('pending', 'in_progress', 'completed', 'overdue', 'cancelled');
CREATE TYPE legalformstatus AS ENUM ('draft', 'pending_review', 'approved', 'rejected', 'in_progress', 'completed', 'archived');
CREATE TYPE legalformpriority AS ENUM ('urgent', 'high', 'medium', 'low');
CREATE TYPE legalformcategory AS ENUM ('health_management_plan', 'measurement_result', 'health_checkup', 'emergency_response', 'education_record', 'accident_report', 'chemical_inventory', 'protective_equipment', 'compliance_report', 'other');
CREATE TYPE backupfrequency AS ENUM ('daily', 'weekly', 'monthly');
CREATE TYPE reportlanguage AS ENUM ('ko', 'en', 'both');
CREATE TYPE dashboardlayout AS ENUM ('default', 'compact', 'detailed');
CREATE TYPE theme AS ENUM ('light', 'dark', 'auto');
CREATE TYPE language AS ENUM ('ko', 'en');

-- Drop tables if they exist
DROP TABLE IF EXISTS checklist_instance_items CASCADE;
DROP TABLE IF EXISTS checklist_attachments CASCADE;
DROP TABLE IF EXISTS checklist_instances CASCADE;
DROP TABLE IF EXISTS checklist_schedules CASCADE;
DROP TABLE IF EXISTS checklist_template_items CASCADE;
DROP TABLE IF EXISTS checklist_templates CASCADE;

DROP TABLE IF EXISTS control_measures CASCADE;
DROP TABLE IF EXISTS special_material_monitoring CASCADE;
DROP TABLE IF EXISTS exposure_assessments CASCADE;
DROP TABLE IF EXISTS special_material_usage CASCADE;
DROP TABLE IF EXISTS special_materials CASCADE;

DROP TABLE IF EXISTS legal_form_approvals CASCADE;
DROP TABLE IF EXISTS legal_form_attachments CASCADE;
DROP TABLE IF EXISTS legal_form_fields CASCADE;
DROP TABLE IF EXISTS legal_forms CASCADE;

DROP TABLE IF EXISTS unified_documents CASCADE;
DROP TABLE IF EXISTS settings_history CASCADE;
DROP TABLE IF EXISTS user_settings CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;

DROP TABLE IF EXISTS health_consultation_attachments CASCADE;
DROP TABLE IF EXISTS health_consultation_follow_ups CASCADE;

-- Create checklist tables
CREATE TABLE checklist_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    name_korean VARCHAR(255) NOT NULL,
    type checklisttype NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_mandatory BOOLEAN NOT NULL DEFAULT false,
    frequency_days INTEGER,
    legal_basis VARCHAR(500),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL
);

CREATE TABLE checklist_template_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES checklist_templates(id) ON DELETE CASCADE,
    item_code VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    description TEXT,
    check_method TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100),
    is_required BOOLEAN NOT NULL DEFAULT true,
    weight INTEGER NOT NULL DEFAULT 1,
    max_score INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE checklist_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES checklist_templates(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    assignee VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    scheduled_date TIMESTAMP NOT NULL,
    due_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status checkliststatus NOT NULL DEFAULT 'pending',
    priority checklistpriority NOT NULL DEFAULT 'medium',
    total_score INTEGER,
    max_total_score INTEGER,
    completion_rate INTEGER,
    notes TEXT,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL
);

CREATE TABLE checklist_instance_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES checklist_instances(id) ON DELETE CASCADE,
    template_item_id UUID NOT NULL REFERENCES checklist_template_items(id) ON DELETE CASCADE,
    is_checked BOOLEAN NOT NULL DEFAULT false,
    is_compliant BOOLEAN,
    score INTEGER,
    checked_at TIMESTAMP,
    checked_by VARCHAR(100),
    findings TEXT,
    corrective_action TEXT,
    corrective_due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE checklist_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES checklist_instances(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT now(),
    description TEXT
);

CREATE TABLE checklist_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES checklist_templates(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    frequency_type VARCHAR(20) NOT NULL,
    frequency_value INTEGER NOT NULL DEFAULT 1,
    default_assignee VARCHAR(100),
    default_department VARCHAR(100),
    auto_create_days_before INTEGER NOT NULL DEFAULT 7,
    reminder_days_before INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    last_created_at TIMESTAMP,
    next_scheduled_at TIMESTAMP
);

-- Create special materials tables
CREATE TABLE special_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_code VARCHAR(50) UNIQUE NOT NULL,
    material_name VARCHAR(255) NOT NULL,
    material_name_korean VARCHAR(255) NOT NULL,
    cas_number VARCHAR(50),
    material_type specialmaterialtype NOT NULL,
    hazard_classification VARCHAR(500),
    ghs_classification JSONB,
    occupational_exposure_limit NUMERIC(10, 6),
    short_term_exposure_limit NUMERIC(10, 6),
    ceiling_limit NUMERIC(10, 6),
    biological_exposure_index NUMERIC(10, 6),
    is_prohibited BOOLEAN NOT NULL DEFAULT false,
    requires_permit BOOLEAN NOT NULL DEFAULT true,
    monitoring_frequency_days INTEGER NOT NULL DEFAULT 180,
    health_exam_frequency_months INTEGER NOT NULL DEFAULT 12,
    physical_state VARCHAR(50),
    molecular_weight NUMERIC(10, 3),
    boiling_point NUMERIC(10, 2),
    melting_point NUMERIC(10, 2),
    vapor_pressure NUMERIC(15, 6),
    target_organs JSONB,
    health_effects TEXT,
    exposure_routes JSONB,
    first_aid_measures TEXT,
    safety_precautions TEXT,
    storage_requirements TEXT,
    disposal_methods TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL
);

CREATE TABLE special_material_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES special_materials(id) ON DELETE CASCADE,
    usage_date TIMESTAMP NOT NULL,
    usage_location VARCHAR(255) NOT NULL,
    usage_purpose VARCHAR(500) NOT NULL,
    work_process VARCHAR(500),
    quantity_used NUMERIC(15, 3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    concentration NUMERIC(10, 6),
    worker_id UUID,
    worker_count INTEGER NOT NULL DEFAULT 1,
    exposure_duration_hours NUMERIC(5, 2),
    control_measures JSONB,
    ppe_used JSONB,
    ventilation_type VARCHAR(100),
    approved_by VARCHAR(100),
    approval_date TIMESTAMP,
    permit_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    recorded_by VARCHAR(100) NOT NULL
);

CREATE TABLE exposure_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES special_materials(id) ON DELETE CASCADE,
    assessment_date TIMESTAMP NOT NULL,
    assessment_type VARCHAR(100) NOT NULL,
    assessment_location VARCHAR(255) NOT NULL,
    work_activity VARCHAR(500) NOT NULL,
    measured_concentration NUMERIC(15, 6),
    measurement_unit VARCHAR(20),
    sampling_duration_minutes INTEGER,
    sampling_method VARCHAR(200),
    analysis_method VARCHAR(200),
    exposure_level exposurelevel NOT NULL,
    exposure_route VARCHAR(100),
    risk_score NUMERIC(5, 2),
    recommended_controls JSONB,
    priority_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    follow_up_required BOOLEAN NOT NULL DEFAULT false,
    follow_up_date TIMESTAMP,
    assessor_name VARCHAR(100) NOT NULL,
    assessor_qualification VARCHAR(200),
    assessment_organization VARCHAR(200),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE special_material_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES special_materials(id) ON DELETE CASCADE,
    monitoring_date TIMESTAMP NOT NULL,
    monitoring_type VARCHAR(100) NOT NULL,
    location VARCHAR(255) NOT NULL,
    status monitoringstatus NOT NULL DEFAULT 'pending',
    scheduled_date TIMESTAMP NOT NULL,
    frequency_type VARCHAR(50) NOT NULL,
    next_monitoring_date TIMESTAMP,
    measurement_results JSONB,
    compliance_status BOOLEAN,
    exceedance_factor NUMERIC(10, 2),
    corrective_actions JSONB,
    action_due_date TIMESTAMP,
    action_responsible VARCHAR(100),
    action_status VARCHAR(50),
    monitor_name VARCHAR(100) NOT NULL,
    monitor_organization VARCHAR(200),
    report_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL
);

CREATE TABLE control_measures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES special_materials(id) ON DELETE CASCADE,
    measure_type controlmeasuretype NOT NULL,
    measure_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    implementation_date TIMESTAMP NOT NULL,
    effectiveness_rating INTEGER,
    cost_estimate NUMERIC(15, 2),
    maintenance_frequency VARCHAR(100),
    responsible_person VARCHAR(100) NOT NULL,
    responsible_department VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_inspection_date TIMESTAMP,
    next_inspection_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL
);

-- Create legal forms tables
CREATE TABLE legal_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_code VARCHAR(50) UNIQUE NOT NULL,
    form_name_korean VARCHAR(255) NOT NULL,
    form_name_english VARCHAR(255),
    category legalformcategory NOT NULL,
    legal_basis TEXT,
    status legalformstatus NOT NULL DEFAULT 'draft',
    priority legalformpriority NOT NULL DEFAULT 'medium',
    form_fields JSONB,
    required_documents JSONB,
    processing_notes TEXT,
    submission_deadline TIMESTAMP,
    submitted_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100)
);

CREATE TABLE legal_form_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES legal_forms(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_label VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT false,
    field_order INTEGER NOT NULL DEFAULT 0,
    validation_rules JSONB,
    default_value TEXT,
    options JSONB,
    help_text TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE legal_form_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES legal_forms(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT now(),
    description TEXT
);

CREATE TABLE legal_form_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id UUID NOT NULL REFERENCES legal_forms(id) ON DELETE CASCADE,
    approver VARCHAR(100) NOT NULL,
    approval_level INTEGER NOT NULL,
    approval_status VARCHAR(20) NOT NULL,
    approved_at TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE unified_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_code VARCHAR(50) UNIQUE NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    content JSONB,
    document_metadata JSONB,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    generated_at TIMESTAMP,
    exported_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    created_by VARCHAR(100) NOT NULL
);

-- Create settings tables
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    company_registration_number VARCHAR(50),
    company_address VARCHAR(500),
    company_phone VARCHAR(50),
    company_email VARCHAR(255),
    representative_name VARCHAR(100),
    health_manager_name VARCHAR(100),
    health_manager_license VARCHAR(100),
    workplace_name VARCHAR(255),
    workplace_address VARCHAR(500),
    total_employees INTEGER,
    construction_employees INTEGER,
    industry_type VARCHAR(100),
    business_type VARCHAR(100),
    smtp_host VARCHAR(255),
    smtp_port INTEGER,
    smtp_username VARCHAR(255),
    smtp_password VARCHAR(255),
    smtp_use_tls BOOLEAN DEFAULT true,
    notification_email VARCHAR(255),
    backup_enabled BOOLEAN DEFAULT true,
    backup_frequency backupfrequency,
    backup_retention_days INTEGER DEFAULT 30,
    backup_path VARCHAR(500),
    report_logo_path VARCHAR(500),
    report_header_text TEXT,
    report_footer_text TEXT,
    report_default_language reportlanguage DEFAULT 'ko',
    timezone VARCHAR(50) DEFAULT 'Asia/Seoul',
    date_format VARCHAR(50) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(50) DEFAULT 'HH:mm:ss',
    currency VARCHAR(10) DEFAULT 'KRW',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    updated_by VARCHAR(100)
);

CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) UNIQUE NOT NULL,
    dashboard_layout dashboardlayout DEFAULT 'default',
    theme theme DEFAULT 'auto',
    language language DEFAULT 'ko',
    items_per_page INTEGER DEFAULT 20,
    email_notifications BOOLEAN DEFAULT true,
    sms_notifications BOOLEAN DEFAULT false,
    push_notifications BOOLEAN DEFAULT true,
    notification_frequency VARCHAR(50) DEFAULT 'immediate',
    sidebar_collapsed BOOLEAN DEFAULT false,
    table_density VARCHAR(20) DEFAULT 'normal',
    show_tooltips BOOLEAN DEFAULT true,
    custom_shortcuts JSONB,
    pinned_menus JSONB,
    recent_searches JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE settings_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_type VARCHAR(50) NOT NULL,
    setting_id UUID NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT now(),
    change_reason TEXT
);

-- Health Consultation Updates
ALTER TABLE health_consultations ADD COLUMN IF NOT EXISTS consultation_type VARCHAR(50) NOT NULL DEFAULT 'general';
ALTER TABLE health_consultations ADD COLUMN IF NOT EXISTS follow_up_required BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE health_consultations ADD COLUMN IF NOT EXISTS follow_up_notes TEXT;

CREATE TABLE health_consultation_follow_ups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL,
    follow_up_date TIMESTAMP NOT NULL,
    follow_up_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    completed_at TIMESTAMP,
    completed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE health_consultation_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT now(),
    description TEXT
);

-- Create indexes
CREATE INDEX idx_checklist_templates_type ON checklist_templates(type);
CREATE INDEX idx_checklist_instances_status ON checklist_instances(status);
CREATE INDEX idx_checklist_instances_assignee ON checklist_instances(assignee);
CREATE INDEX idx_special_materials_type ON special_materials(material_type);
CREATE INDEX idx_special_material_usage_date ON special_material_usage(usage_date);
CREATE INDEX idx_exposure_assessments_level ON exposure_assessments(exposure_level);
CREATE INDEX idx_special_material_monitoring_status ON special_material_monitoring(status);
CREATE INDEX idx_legal_forms_category ON legal_forms(category);
CREATE INDEX idx_legal_forms_status ON legal_forms(status);

-- Insert default system settings
INSERT INTO system_settings (
    id,
    company_name,
    company_registration_number,
    workplace_name,
    total_employees,
    construction_employees
) VALUES (
    gen_random_uuid(),
    'SafeWork Pro',
    '000-00-00000',
    '건설현장',
    100,
    50
) ON CONFLICT DO NOTHING;