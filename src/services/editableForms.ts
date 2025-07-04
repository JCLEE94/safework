/**
 * 편집 가능한 양식 문서 목록
 * Editable form documents list
 */

export interface EditableForm {
  id: string;
  name: string;
  korean_name: string;
  description: string;
  category: string;
  file_path: string;
  fields: string[];
  template_type: 'fillable' | 'form' | 'checklist';
  required_fields: string[];
}

// 편집 가능한 양식 문서만 선별
export const EDITABLE_FORMS: EditableForm[] = [
  // 03-관리대장 (실제 편집이 필요한 대장류)
  {
    id: "msds_register",
    name: "MSDS Management Register",
    korean_name: "MSDS 관리대장",
    description: "화학물질 안전보건자료 관리대장",
    category: "03-관리대장",
    file_path: "03-관리대장/001_MSDS_관리대장.xls",
    fields: ["chemical_name", "supplier", "date_received", "manager", "location"],
    template_type: "form",
    required_fields: ["chemical_name", "date_received"]
  },
  {
    id: "health_consultation_log",
    name: "Health Consultation Visit Log", 
    korean_name: "건강관리 상담방문 일지",
    description: "보건관리자 현장방문 및 상담 기록",
    category: "03-관리대장",
    file_path: "03-관리대장/002_건강관리_상담방문_일지.xls",
    fields: ["visit_date", "visitor_name", "consultation_type", "findings", "recommendations"],
    template_type: "form",
    required_fields: ["visit_date", "visitor_name"]
  },
  {
    id: "health_findings_register",
    name: "Health Findings Management Register",
    korean_name: "유소견자 관리대장", 
    description: "건강진단 유소견자 관리 및 추적",
    category: "03-관리대장",
    file_path: "03-관리대장/003_유소견자_관리대장.xlsx",
    fields: ["worker_name", "exam_date", "findings", "follow_up_date", "status"],
    template_type: "form",
    required_fields: ["worker_name", "exam_date", "findings"]
  },

  // 07-특별관리물질 (법정 양식)
  {
    id: "special_substance_log",
    name: "Special Substance Handling Log",
    korean_name: "특별관리물질 취급일지",
    description: "특별관리물질 취급 기록 일지 (별표7 양식)",
    category: "07-특별관리물질", 
    file_path: "07-특별관리물질/001_특별관리물질_취급일지_별표7_양식.pdf",
    fields: ["date", "worker_name", "substance_name", "handling_type", "duration", "ppe_used"],
    template_type: "fillable",
    required_fields: ["date", "worker_name", "substance_name"]
  },
  {
    id: "special_substance_log_a",
    name: "Special Substance Log Type A",
    korean_name: "특별관리물질 취급일지 A형",
    description: "특별관리물질 취급일지 A형 양식",
    category: "07-특별관리물질",
    file_path: "07-특별관리물질/003_특별관리물질_취급일지_A형.docx", 
    fields: ["date", "worker_name", "substance_name", "work_content", "duration"],
    template_type: "form",
    required_fields: ["date", "worker_name", "substance_name"]
  },
  {
    id: "special_substance_log_b", 
    name: "Special Substance Log Type B",
    korean_name: "특별관리물질 취급일지 B형",
    description: "특별관리물질 취급일지 B형 양식",
    category: "07-특별관리물질",
    file_path: "07-특별관리물질/004_특별관리물질_취급일지_B형.docx",
    fields: ["date", "worker_name", "substance_name", "work_content", "duration"],
    template_type: "form", 
    required_fields: ["date", "worker_name", "substance_name"]
  },

  // 02-법정서식/분리된_서식들 (편집 가능한 체크리스트)
  {
    id: "safety_checklist_01",
    name: "Safety Management Responsibility Checklist",
    korean_name: "안전보건관리책임자 체크리스트",
    description: "안전보건관리책임자 업무 체크리스트",
    category: "02-법정서식",
    file_path: "02-법정서식/분리된_서식들/01_3 안전보건관리책임자  36   서울시 중대산업재해 예_p1-1.pdf",
    fields: ["check_date", "inspector", "items_checked", "remarks"],
    template_type: "checklist",
    required_fields: ["check_date", "inspector"]
  },
  {
    id: "safety_checklist_02", 
    name: "Management System Checklist",
    korean_name: "안전보건관리체계 체크리스트",
    description: "안전보건관리체계 구축 체크리스트", 
    category: "02-법정서식",
    file_path: "02-법정서식/분리된_서식들/02_Ⅱ 안전보건관리체계 구축 3 7관리감독자 업무 수행 평_p2-2.pdf",
    fields: ["check_date", "inspector", "system_status", "improvements"],
    template_type: "checklist",
    required_fields: ["check_date", "inspector"]
  },

  // 02-법정서식/체크리스트_모음 (통합 체크리스트)
  {
    id: "integrated_safety_checklist",
    name: "Integrated Safety Management Checklist", 
    korean_name: "안전보건관리체계 통합체크리스트",
    description: "안전보건관리체계 통합 점검 체크리스트",
    category: "02-법정서식",
    file_path: "02-법정서식/체크리스트_모음/01_안전보건관리체계_통합체크리스트.pdf",
    fields: ["inspection_date", "inspector", "department", "checklist_items", "score", "recommendations"],
    template_type: "checklist",
    required_fields: ["inspection_date", "inspector"]
  },
  {
    id: "risk_assessment_checklist",
    name: "Risk Assessment Integrated Checklist",
    korean_name: "위험요인 조사 통합체크리스트", 
    description: "위험요인 조사 및 평가 통합 체크리스트",
    category: "02-법정서식",
    file_path: "02-법정서식/체크리스트_모음/02_위험요인_조사_통합체크리스트.pdf",
    fields: ["assessment_date", "assessor", "work_area", "hazards_identified", "risk_level", "controls"],
    template_type: "checklist",
    required_fields: ["assessment_date", "assessor", "work_area"]
  },
  {
    id: "accident_response_checklist",
    name: "Accident Response Integrated Checklist",
    korean_name: "산업재해 대응 통합체크리스트",
    description: "산업재해 발생시 대응 절차 체크리스트",
    category: "02-법정서식", 
    file_path: "02-법정서식/체크리스트_모음/04_산업재해_대응_통합체크리스트.pdf",
    fields: ["incident_date", "responder", "incident_type", "response_actions", "followup_required"],
    template_type: "checklist",
    required_fields: ["incident_date", "responder", "incident_type"]
  },

  // 04-체크리스트 (실제 현장 사용 체크리스트)
  {
    id: "health_checklist",
    name: "Health Related Checklist",
    korean_name: "보건관련 체크리스트", 
    description: "현장 보건관리 점검 체크리스트",
    category: "04-체크리스트",
    file_path: "04-체크리스트/001_보건관련_체크리스트.pdf",
    fields: ["check_date", "checker", "health_items", "compliance_status", "corrective_actions"],
    template_type: "checklist",
    required_fields: ["check_date", "checker"]
  }
];

// 카테고리별 편집 가능한 문서 수
export const getEditableFormsByCategory = (category: string): EditableForm[] => {
  return EDITABLE_FORMS.filter(form => form.category === category);
};

// 템플릿 타입별 필터링
export const getEditableFormsByType = (type: 'fillable' | 'form' | 'checklist'): EditableForm[] => {
  return EDITABLE_FORMS.filter(form => form.template_type === type);
};

// 편집 가능한 전체 문서 수
export const getTotalEditableForms = (): number => {
  return EDITABLE_FORMS.length;
};

// 카테고리별 요약
export const getCategorySummary = () => {
  const summary: Record<string, number> = {};
  EDITABLE_FORMS.forEach(form => {
    summary[form.category] = (summary[form.category] || 0) + 1;
  });
  return summary;
};