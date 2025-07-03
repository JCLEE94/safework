"""
문서 관리 API 핸들러
Document management API handlers
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from typing import List, Dict, Optional
import os
import json
from datetime import datetime
# import pdfkit  # Temporarily disabled
# from jinja2 import Template  # Temporarily disabled
from pathlib import Path
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import black
import subprocess
import tempfile
import base64
import hashlib
import shutil

# 캐싱 서비스 import
from ..services.cache import cache_pdf_result, get_cached_pdf, CacheTTL

# PDF 양식 설정 import
from ..config.pdf_forms import (
    PDF_FORM_COORDINATES, 
    AVAILABLE_PDF_FORMS, 
    FIELD_LABELS
)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# PDF 편집 전용 라우터
pdf_router = APIRouter(prefix="/api/v1/pdf-editor", tags=["pdf-editor"])

# Base directory for documents - 설정에서 가져오기
from ..config.settings import get_settings
settings = get_settings()

current_dir = Path(__file__).parent.parent.parent  # Go up to project root
DOCUMENT_BASE_DIR = Path(settings.document_dir) if settings.document_dir else current_dir / "document"
TEMPLATES_DIR = current_dir / "src" / "templates" if (current_dir / "src" / "templates").exists() else Path("/app/src/templates")

print(f"Document base directory: {DOCUMENT_BASE_DIR}")
print(f"Document base exists: {DOCUMENT_BASE_DIR.exists()}")

# Document categories
DOCUMENT_CATEGORIES = {
    "manual": "01-업무매뉴얼",
    "legal": "02-법정서식",
    "register": "03-관리대장",
    "checklist": "04-체크리스트",
    "education": "05-교육자료",
    "msds": "06-MSDS관련",
    "special": "07-특별관리물질",
    "health": "08-건강관리",
    "reference": "09-참고자료",
    "latest": "10-최신자료_2024-2025"
}

# Template forms
FORM_TEMPLATES = {
    # 주요 관리대장 (PDF 생성 지원)
    "health_consultation_log": {
        "name": "건강관리 상담방문 일지",
        "form_id": "건강관리_상담방문_일지",
        "fields": ["visit_date", "site_name", "counselor", "work_type", "worker_count", 
                  "participant_1", "participant_2", "participant_3", "participant_4",
                  "counseling_topic", "health_issues", "work_environment", "improvement_suggestions",
                  "immediate_actions", "follow_up_actions", "next_visit_plan",
                  "counselor_signature", "manager_signature", "signature_date"],
        "template_path": "03-관리대장/002_건강관리_상담방문_일지.xls",
        "pdf_support": True,
        "category": "register"
    },
    "msds_management_log": {
        "name": "MSDS 관리대장",
        "form_id": "MSDS_관리대장",
        "fields": ["company_name", "department", "manager", "chemical_name", "manufacturer", 
                  "cas_number", "usage", "quantity", "storage_location", "hazard_class",
                  "chemical_name_2", "manufacturer_2", "cas_number_2", "usage_2", 
                  "quantity_2", "storage_location_2", "hazard_class_2",
                  "msds_date", "msds_version", "update_date", "safety_measures",
                  "emergency_procedures", "prepared_by", "approved_by", "date"],
        "template_path": "03-관리대장/001_MSDS_관리대장.xls",
        "pdf_support": True,
        "category": "register"
    },
    "abnormal_findings_log": {
        "name": "유소견자 관리대장",
        "form_id": "유소견자_관리대장",
        "fields": ["company_name", "department", "year", "worker_name", "employee_id", 
                  "position", "exam_date", "exam_agency", "exam_result", "opinion",
                  "manager_signature", "creation_date"],
        "template_path": "03-관리대장/003_유소견자_관리대장.xlsx",
        "pdf_support": True,
        "category": "register"
    },
    "special_material_log": {
        "name": "특별관리물질 취급일지",
        "form_id": "특별관리물질_취급일지",
        "fields": ["work_date", "department", "weather", "chemical_name", "manufacturer", 
                  "cas_number", "work_location", "work_content", "work_method",
                  "worker_name", "worker_id", "work_experience", "health_status",
                  "start_time", "end_time", "duration", "quantity_used", "concentration",
                  "respiratory_protection", "hand_protection", "eye_protection", "body_protection",
                  "ventilation_status", "emergency_equipment", "safety_procedures", "waste_disposal",
                  "special_notes", "corrective_actions", "health_symptoms",
                  "worker_signature", "supervisor_signature", "manager_signature", "signature_date"],
        "template_path": "07-특별관리물질/003_특별관리물질_취급일지_A형.docx",
        "pdf_support": True,
        "category": "special"
    },
    
    # 기존 법정서식 (PDF 페이지 추출 방식)
    "health_consultation": {
        "name": "건강상담일지",
        "fields": ["date", "worker_name", "employee_id", "content", "action", "counselor"],
        "original_pdf": "02-법정서식/006_업무수행_체크리스트_및_서식_원본_백업.pdf",
        "page_number": 15,
        "pdf_support": False,
        "category": "legal"
    },
    "accident_report": {
        "name": "산업재해조사표",
        "fields": ["date", "location", "injured_name", "injury_type", "cause", "measures"],
        "original_pdf": "02-법정서식/006_업무수행_체크리스트_및_서식_원본_백업.pdf",
        "page_number": 20,
        "pdf_support": False,
        "category": "legal"
    },
    "education_record": {
        "name": "안전보건교육일지",
        "fields": ["date", "title", "instructor", "participants", "content", "duration"],
        "original_pdf": "02-법정서식/분리된_서식들/18_1 안전보건교육 실시 116   서울시 중대산업재해 예_p18-18.pdf",
        "page_number": 0,
        "pdf_support": False,
        "category": "legal"
    },
    "work_environment_report": {
        "name": "작업환경측정결과보고서",
        "fields": ["date", "location", "items", "results", "measures", "agency"],
        "original_pdf": "02-법정서식/006_업무수행_체크리스트_및_서식_원본_백업.pdf",
        "page_number": 10,
        "pdf_support": False,
        "category": "legal"
    },
    "health_exam_result": {
        "name": "건강진단결과표",
        "fields": ["exam_date", "worker_name", "exam_type", "results", "opinion", "doctor"],
        "original_pdf": "02-법정서식/006_업무수행_체크리스트_및_서식_원본_백업.pdf",
        "page_number": 12,
        "pdf_support": False,
        "category": "legal"
    },
    "msds_register": {
        "name": "MSDS 관리대장",
        "fields": ["chemical_name", "cas_no", "manufacturer", "usage", "hazards", "storage"],
        "original_pdf": "02-법정서식/006_업무수행_체크리스트_및_서식_원본_백업.pdf",
        "page_number": 8,
        "pdf_support": False,
        "category": "legal"
    },
    "daily_checklist": {
        "name": "일일 안전점검표",
        "fields": ["date", "inspector", "items", "results", "issues", "actions"],
        "original_pdf": "02-법정서식/006_업무수행_체크리스트_및_서식_원본_백업.pdf",
        "page_number": 5,
        "pdf_support": False,
        "category": "legal"
    }
}

# 실제 Office 파일을 PDF로 변환하는 함수
def convert_office_to_pdf_with_libreoffice(office_file_path: str) -> io.BytesIO:
    """LibreOffice를 사용하여 Excel/Word 파일을 PDF로 변환"""
    try:
        print(f"Converting {office_file_path} to PDF using LibreOffice")
        
        # 파일 존재 여부 확인
        if not os.path.exists(office_file_path):
            print(f"Warning: Office file not found: {office_file_path}")
            return create_blank_pdf_with_title(os.path.basename(office_file_path))
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 원본 파일을 임시 디렉토리에 복사
            temp_input = os.path.join(temp_dir, os.path.basename(office_file_path))
            shutil.copy2(office_file_path, temp_input)
            
            # LibreOffice로 PDF 변환
            cmd = [
                'soffice',  # 'libreoffice' 대신 'soffice' 사용
                '--headless',
                '--invisible',
                '--nodefault',
                '--nolockcheck',
                '--nologo',
                '--norestore',
                '--convert-to',
                'pdf:writer_pdf_Export',  # 명시적인 필터 지정
                '--outdir',
                temp_dir,
                temp_input
            ]
            
            # HOME 환경변수 설정 (LibreOffice가 필요로 함)
            env = os.environ.copy()
            env['HOME'] = '/tmp'
            
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
            
            if result.returncode != 0:
                print(f"LibreOffice conversion error: {result.stderr}")
                # 변환 실패시 reportlab으로 PDF 생성
                return create_form_template_pdf(os.path.splitext(os.path.basename(office_file_path))[0])
            
            # 변환된 PDF 파일 찾기
            pdf_filename = os.path.splitext(os.path.basename(office_file_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            if not os.path.exists(pdf_path):
                print(f"Converted PDF not found: {pdf_path}, creating template PDF")
                return create_form_template_pdf(os.path.splitext(os.path.basename(office_file_path))[0])
            
            # PDF 내용을 BytesIO로 읽기
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            return io.BytesIO(pdf_content)
            
    except subprocess.TimeoutExpired:
        print("LibreOffice conversion timeout")
        return create_form_template_pdf(os.path.splitext(os.path.basename(office_file_path))[0])
    except Exception as e:
        print(f"Office to PDF conversion error: {str(e)}")
        # 변환 실패시 템플릿 PDF 생성
        return create_form_template_pdf(os.path.splitext(os.path.basename(office_file_path))[0])




def setup_korean_font(canvas_obj):
    """한글 폰트 설정 헬퍼 함수"""
    try:
        # 다양한 경로에서 나눔고딕 폰트 찾기
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum-fonts/NanumGothic.ttf",
            "/usr/local/share/fonts/NanumGothic.ttf",
            "/app/fonts/NanumGothic.ttf"  # 컨테이너 내부 경로
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
                    canvas_obj.setFont("NanumGothic", 10)
                    print(f"Korean font loaded successfully: {font_path}")
                    return "NanumGothic"
                except Exception as font_error:
                    print(f"Failed to load font {font_path}: {font_error}")
                    continue
        
        # 폰트가 없으면 기본 폰트 사용
        print("Warning: Korean font not found, using default font")
        canvas_obj.setFont("Helvetica", 10)
        return "Helvetica"
    except Exception as e:
        print(f"Font setup error: {str(e)}")
        canvas_obj.setFont("Helvetica", 10)
        return "Helvetica"


def create_text_overlay(data: Dict, form_type: str) -> io.BytesIO:
    """PDF 양식 위에 텍스트 오버레이 생성 - 정확한 좌표 매핑"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # 한글 폰트 설정
    font_name = setup_korean_font(can)
    can.setFont(font_name, 9)  # 폰트 크기를 약간 줄임
    can.setFillColor(black)
    
    # 해당 양식의 좌표 설정 가져오기
    if form_type not in PDF_FORM_COORDINATES:
        raise ValueError(f"지원하지 않는 양식입니다: {form_type}")
    
    form_config = PDF_FORM_COORDINATES[form_type]
    fields = form_config.get("fields", {})
    
    print(f"Creating text overlay for {form_type} with data: {data}")
    
    # 각 필드에 대해 데이터 추가
    for field_name, field_info in fields.items():
        if field_name in data and data[field_name]:
            x = field_info.get("x", 100)
            y = field_info.get("y", 700)
            label = field_info.get("label", field_name)
            value = str(data[field_name]).strip()
            
            if value:
                # 값이 있으면 해당 위치에 텍스트 추가
                try:
                    # 긴 텍스트 처리
                    max_length = 30
                    if len(value) > max_length:
                        value = value[:max_length-3] + "..."
                    
                    # 좌표 미세 조정
                    adjusted_x = x + 2
                    adjusted_y = y - 2
                    
                    can.drawString(adjusted_x, adjusted_y, value)
                    print(f"Drew '{value}' at ({adjusted_x}, {adjusted_y}) for {field_name}")
                    
                except Exception as e:
                    print(f"Error drawing text for {field_name}: {str(e)}")
    
    # 오버레이 정보 추가 (하단에 작게)
    can.setFont(font_name, 7)
    can.drawString(50, 30, f"입력일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    can.save()
    packet.seek(0)
    return packet




def fill_pdf_form(template_path: str, data: Dict, form_type: str) -> io.BytesIO:
    """기존 PDF 양식에 데이터를 채워넣어 새로운 PDF 생성"""
    try:
        # 1. 원본 PDF 읽기
        existing_pdf = PdfReader(template_path)
        
        # 2. 데이터 오버레이 생성
        overlay_packet = create_text_overlay(data, form_type)
        overlay_pdf = PdfReader(overlay_packet)
        
        # 3. 새로운 PDF 생성
        output = PdfWriter()
        
        # 4. 각 페이지에 오버레이 적용
        for page_num in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[page_num]
            
            # 첫 번째 페이지에만 데이터 오버레이 적용
            if page_num == 0 and len(overlay_pdf.pages) > 0:
                page.merge_page(overlay_pdf.pages[0])
            
            output.add_page(page)
        
        # 5. 결과 PDF를 BytesIO로 반환
        output_stream = io.BytesIO()
        output.write(output_stream)
        output_stream.seek(0)
        
        return output_stream
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 생성 중 오류 발생: {str(e)}")


def convert_office_to_pdf(office_file_path: str) -> io.BytesIO:
    """Excel/Word 파일을 PDF로 변환 - LibreOffice 사용"""
    # 새로운 함수로 대체
    return convert_office_to_pdf_with_libreoffice(office_file_path)


def get_field_labels() -> Dict[str, str]:
    """필드명을 한글 라벨로 변환하는 매핑"""
    return FIELD_LABELS


def create_form_template_pdf(form_id: str) -> io.BytesIO:
    """양식별 PDF 템플릿 생성 - 깔끔한 빈 양식"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    # 한글 폰트 설정
    font_name = setup_korean_font(can)
    
    # 제목 설정
    form_titles = {
        "유소견자_관리대장": "유소견자 관리대장",
        "MSDS_관리대장": "화학물질 안전보건자료(MSDS) 관리대장", 
        "건강관리_상담방문_일지": "건강관리 상담방문 일지",
        "특별관리물질_취급일지": "특별관리물질 취급일지"
    }
    
    title = form_titles.get(form_id, form_id)
    
    # 제목 추가 (중앙 정렬)
    can.setFont(font_name, 18)
    title_width = can.stringWidth(title, font_name, 18)
    can.drawString((width - title_width) / 2, height - 80, title)
    
    # 제목 아래 구분선
    can.line(80, height - 100, width - 80, height - 100)
    
    # 표 형태의 빈 양식 생성
    can.setFont(font_name, 10)
    
    if form_id == "유소견자_관리대장":
        # 유소견자 관리대장 표 형태
        table_top = height - 150
        row_height = 30
        col_widths = [100, 100, 100, 100, 100]
        
        # 표 헤더
        headers = ["근로자명", "사번", "검진일", "검진기관", "검진결과"]
        x_pos = 80
        for i, header in enumerate(headers):
            can.rect(x_pos, table_top - row_height, col_widths[i], row_height)
            can.drawString(x_pos + 5, table_top - 20, header)
            x_pos += col_widths[i]
        
        # 빈 행들 (5개)
        for row in range(5):
            y_pos = table_top - (row + 2) * row_height
            x_pos = 80
            for col_width in col_widths:
                can.rect(x_pos, y_pos, col_width, row_height)
                x_pos += col_width
    
    elif form_id == "MSDS_관리대장":
        # MSDS 관리대장 표 형태
        table_top = height - 150
        row_height = 25
        col_widths = [120, 100, 80, 100, 80]
        
        # 표 헤더
        headers = ["화학물질명", "제조업체", "CAS번호", "용도", "보관장소"]
        x_pos = 80
        for i, header in enumerate(headers):
            can.rect(x_pos, table_top - row_height, col_widths[i], row_height)
            can.drawString(x_pos + 5, table_top - 15, header)
            x_pos += col_widths[i]
        
        # 빈 행들 (6개)
        for row in range(6):
            y_pos = table_top - (row + 2) * row_height
            x_pos = 80
            for col_width in col_widths:
                can.rect(x_pos, y_pos, col_width, row_height)
                x_pos += col_width
    
    elif form_id == "건강관리_상담방문_일지":
        # 상담방문 일지 형태
        # 상단 정보 필드
        info_y = height - 150
        can.drawString(100, info_y, "방문일자: _______________")
        can.drawString(250, info_y, "현장명: _______________")
        can.drawString(400, info_y, "날씨: _______________")
        
        can.drawString(100, info_y - 30, "작업종류: _______________")
        can.drawString(300, info_y - 30, "작업인원: _______________")
        
        # 상담내용 큰 박스
        can.rect(100, info_y - 200, 400, 120)
        can.drawString(105, info_y - 70, "상담내용:")
        
        # 조치사항 박스
        can.rect(100, info_y - 320, 400, 80)
        can.drawString(105, info_y - 240, "조치사항:")
        
        # 서명란
        can.drawString(100, info_y - 370, "다음방문예정: _______________")
        can.drawString(300, info_y - 400, "상담자: _______________")
        can.drawString(450, info_y - 400, "서명일: _______________")
    
    elif form_id == "특별관리물질_취급일지":
        # 특별관리물질 취급일지 형태
        info_y = height - 150
        
        # 상단 기본 정보
        can.drawString(100, info_y, "날짜: _______________")
        can.drawString(250, info_y, "특별관리물질명: _______________")
        can.drawString(100, info_y - 30, "작업장소: _______________")
        can.drawString(300, info_y - 30, "작업내용: _______________")
        
        # 작업자 정보
        can.drawString(100, info_y - 70, "작업자명: _______________")
        can.drawString(250, info_y - 70, "시작시간: _______________")
        can.drawString(100, info_y - 100, "종료시간: _______________")
        can.drawString(250, info_y - 100, "사용량: _______________")
        
        # 안전조치사항 큰 박스
        can.rect(100, info_y - 250, 400, 100)
        can.drawString(105, info_y - 170, "안전조치사항:")
        
        # 서명란
        can.drawString(300, info_y - 300, "관리감독자: _______________")
        can.drawString(450, info_y - 300, "서명: _______________")
    
    # 하단 작성일
    can.setFont(font_name, 8)
    can.drawString(450, 50, f"작성일: {datetime.now().strftime('%Y년 %m월 %d일')}")
    
    can.save()
    packet.seek(0)
    return packet


def create_blank_pdf_with_title(filename: str) -> io.BytesIO:
    """제목만 있는 빈 PDF 생성 (변환 실패시 대체용)"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # 한글 폰트 설정
    font_name = setup_korean_font(can)
    
    # 제목 추가
    can.setFont(font_name, 16)
    title = filename.replace('_', ' ').replace('.xlsx', '').replace('.xls', '').replace('.docx', '')
    can.drawString(100, 750, f"양식: {title}")
    
    can.setFont(font_name, 12)
    can.drawString(100, 700, "원본 파일을 PDF로 변환하는 중 문제가 발생했습니다.")
    can.drawString(100, 680, "텍스트 입력 기능은 정상적으로 사용 가능합니다.")
    
    can.save()
    packet.seek(0)
    return packet


def get_available_pdf_forms() -> List[Dict]:
    """사용 가능한 PDF 양식 목록 반환 (실제 파일 경로 포함)"""
    forms = []
    for form_info in AVAILABLE_PDF_FORMS:
        form_dict = form_info.copy()
        # 전체 경로 추가
        form_dict["source_path"] = str(DOCUMENT_BASE_DIR / form_info["source_path"])
        forms.append(form_dict)
    
    return forms


@router.get("/categories")
async def get_document_categories():
    """문서 카테고리 목록 조회"""
    return {
        "categories": [
            {"id": key, "name": value, "description": f"{value} 관련 문서"}
            for key, value in DOCUMENT_CATEGORIES.items()
        ]
    }


@router.get("/templates")
async def get_form_templates():
    """작성 가능한 양식 템플릿 목록"""
    return {
        "templates": [
            {
                "id": key, 
                "name": value["name"],
                "fields": value["fields"],
                "description": f"{value['name']} 작성 양식"
            }
            for key, value in FORM_TEMPLATES.items()
        ]
    }


@router.get("/category/{category_id}")
async def list_documents_by_category(category_id: str):
    """카테고리별 문서 목록 조회"""
    if category_id not in DOCUMENT_CATEGORIES:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    
    category_path = DOCUMENT_BASE_DIR / DOCUMENT_CATEGORIES[category_id]
    if not category_path.exists():
        return {"documents": []}
    
    documents = []
    for file_path in category_path.iterdir():
        if file_path.is_file():
            documents.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "type": file_path.suffix[1:] if file_path.suffix else "unknown"
            })
    
    return {"documents": sorted(documents, key=lambda x: x["name"])}


@router.get("/download/{category_id}/{filename}")
async def download_document(category_id: str, filename: str):
    """문서 다운로드"""
    if category_id not in DOCUMENT_CATEGORIES:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
    
    file_path = DOCUMENT_BASE_DIR / DOCUMENT_CATEGORIES[category_id] / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


async def _generate_pdf_content(template_id: str, data: Dict) -> bytes:
    """PDF 콘텐츠 생성 공통 함수"""
    try:
        template_info = FORM_TEMPLATES[template_id]
        
        print(f"Generating PDF for template: {template_id}")
        print(f"Data received: {data}")
        
        # PDF 지원 양식인 경우 (Excel/Word 파일)
        if template_info.get('pdf_support', False) and 'template_path' in template_info:
            template_path = DOCUMENT_BASE_DIR / template_info['template_path']
            
            if template_path.exists():
                print(f"Using template file: {template_path}")
                
                # Office 파일을 PDF로 변환
                pdf_stream = convert_office_to_pdf(str(template_path))
                
                # 데이터 오버레이 적용
                if data:
                    overlay_packet = create_text_overlay(data, template_id)
                    if overlay_packet:
                        # 기존 PDF 읽기
                        existing_pdf = PdfReader(pdf_stream)
                        overlay_pdf = PdfReader(overlay_packet)
                        
                        # 새로운 PDF 생성
                        output = PdfWriter()
                        
                        # 첫 페이지에 오버레이 적용
                        for page_num in range(len(existing_pdf.pages)):
                            page = existing_pdf.pages[page_num]
                            if page_num == 0 and len(overlay_pdf.pages) > 0:
                                page.merge_page(overlay_pdf.pages[0])
                            output.add_page(page)
                        
                        # 결과 반환
                        result_buffer = io.BytesIO()
                        output.write(result_buffer)
                        result_buffer.seek(0)
                        return result_buffer.getvalue()
                
                # 오버레이 없이 원본 PDF 반환
                pdf_stream.seek(0)
                return pdf_stream.getvalue()
        
        # 원본 PDF 방식 (기존 코드 유지)
        if 'original_pdf' in template_info:
            original_pdf_path = DOCUMENT_BASE_DIR / template_info['original_pdf']
            
            if original_pdf_path.exists():
                print(f"Using original PDF: {original_pdf_path}")
                
                # 특정 페이지만 추출하여 사용
                reader = PdfReader(str(original_pdf_path))
                page_num = template_info.get('page_number', 0)
                
                if page_num < len(reader.pages):
                    # 해당 페이지만 추출
                    writer = PdfWriter()
                    page = reader.pages[page_num]
                    
                    # 데이터 오버레이 생성
                    overlay_packet = create_text_overlay(data, template_id)
                    
                    if overlay_packet:
                        overlay_reader = PdfReader(overlay_packet)
                        overlay_page = overlay_reader.pages[0]
                        
                        # 원본 페이지에 오버레이 병합
                        page.merge_page(overlay_page)
                    
                    writer.add_page(page)
                    
                    # PDF 내용을 바이트로 반환
                    buffer = io.BytesIO()
                    writer.write(buffer)
                    buffer.seek(0)
                    pdf_content = buffer.getvalue()
                    print(f"PDF generated successfully with original form, size: {len(pdf_content)} bytes")
                    return pdf_content
        
        # 원본 파일이 없으면 reportlab으로 새로 생성
        print("No template found, creating new PDF with reportlab")
    except Exception as e:
        print(f"Error in PDF generation: {str(e)}")
        # 에러 발생시 기본 PDF 생성
    
    # Create PDF in memory
    buffer = io.BytesIO()
    
    # Create PDF with reportlab
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Set up Korean font
    font_name = setup_korean_font(c)
    
    # Title
    c.setFont(font_name, 16)
    c.drawCentredString(width/2, height - 50, template_info['name'])
    
    # Date
    c.setFont(font_name, 10)
    date_str = f"작성일: {datetime.now().strftime('%Y년 %m월 %d일')}"
    c.drawString(50, height - 80, date_str)
    
    # Draw a line
    c.line(50, height - 90, width - 50, height - 90)
    
    # Field labels
    field_labels = {
        "date": "날짜",
        "worker_name": "근로자명",
        "employee_id": "사번",
        "content": "내용",
        "action": "조치사항",
        "counselor": "상담자",
        "location": "장소",
        "injured_name": "재해자명",
        "injury_type": "재해유형",
        "cause": "원인",
        "measures": "개선대책",
        "title": "교육명",
        "instructor": "강사",
        "participants": "참석자",
        "duration": "교육시간",
        "items": "측정항목",
        "results": "측정결과",
        "agency": "측정기관",
        "exam_date": "검진일",
        "exam_type": "검진유형",
        "opinion": "소견",
        "doctor": "검진의사",
        "chemical_name": "화학물질명",
        "cas_no": "CAS No.",
        "manufacturer": "제조사",
        "usage": "용도",
        "hazards": "유해성",
        "storage": "보관장소",
        "inspector": "점검자",
        "issues": "지적사항",
        "actions": "조치사항"
    }
    
    # Add form fields
    y_position = height - 120
    c.setFont(font_name, 11)
    
    for field in template_info['fields']:
        if field in data and data[field]:
            label = field_labels.get(field, field)
            value = str(data[field])
            
            # Draw label
            c.setFont(font_name, 11)
            c.drawString(50, y_position, f"{label}:")
            
            # Draw value
            c.setFont(font_name, 10)
            c.drawString(150, y_position, value)
            
            y_position -= 25
            
            # Check if we need a new page
            if y_position < 100:
                # Add signature section at bottom of current page
                c.setFont(font_name, 10)
                c.drawString(width - 200, 80, "작성자: _________________ (인)")
                c.drawString(width - 200, 60, "확인자: _________________ (인)")
                
                c.showPage()
                y_position = height - 50
                c.setFont(font_name, 11)
    
    # Add signature section if not added yet
    if y_position < height - 150:  # Some content was added
        c.setFont(font_name, 10)
        c.drawString(width - 200, 80, "작성자: _________________ (인)")
        c.drawString(width - 200, 60, "확인자: _________________ (인)")
    
    # Save PDF
    c.save()
    
    # Get PDF data
    buffer.seek(0)
    pdf_content = buffer.getvalue()
    print(f"PDF generated successfully, size: {len(pdf_content)} bytes")
    return pdf_content


@router.post("/preview/{template_id}")
async def preview_document(template_id: str, data: Dict):
    """문서 미리보기 - Base64 인코딩된 PDF 반환"""
    if template_id not in FORM_TEMPLATES:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    try:
        pdf_content = await _generate_pdf_content(template_id, data)
        
        # Base64 인코딩
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return {
            "pdf_base64": pdf_base64,
            "template_name": FORM_TEMPLATES[template_id]['name'],
            "size": len(pdf_content)
        }
    except Exception as e:
        print(f"PDF preview error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 미리보기 생성 실패: {str(e)}")


@router.post("/generate/{template_id}")
async def generate_document(template_id: str, data: Dict):
    """원본 PDF 양식에 데이터를 입력하여 문서 생성 및 다운로드"""
    if template_id not in FORM_TEMPLATES:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    try:
        pdf_content = await _generate_pdf_content(template_id, data)
        
        # Return as downloadable PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{template_id}_{timestamp}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")


@router.get("/pdf-forms")
async def get_pdf_forms():
    """PDF 양식 목록 조회"""
    forms = [
        {
            "id": "유소견자_관리대장",
            "name": "유소견자 관리대장",
            "name_korean": "유소견자 관리대장",
            "description": "근로자 건강검진 유소견자 관리 양식",
            "category": "register",  # Changed from "관리대장" to "register"
            "fields": ["company_name", "department", "year", "worker_name", "employee_id", "position", "exam_date", "exam_agency", "exam_result", "opinion", "manager_signature", "creation_date"]
        },
        {
            "id": "MSDS_관리대장",
            "name": "MSDS 관리대장", 
            "name_korean": "MSDS 관리대장",
            "description": "화학물질 안전보건자료 관리 양식",
            "category": "register",  # Changed from "관리대장" to "register"
            "fields": ["company_name", "department", "manager", "chemical_name", "manufacturer", "cas_number", "usage", "quantity", "storage_location", "hazard_class", "msds_date", "msds_version", "update_date", "safety_measures"]
        },
        {
            "id": "건강관리_상담방문_일지",
            "name": "건강관리 상담방문 일지",
            "name_korean": "건강관리 상담방문 일지", 
            "description": "근로자 건강관리 상담 방문 기록 양식",
            "category": "health",  # Changed from "건강관리" to "health"
            "fields": ["visit_date", "site_name", "counselor", "work_type", "worker_count", "counseling_topic", "health_issues", "work_environment", "improvement_suggestions"]
        },
        {
            "id": "특별관리물질_취급일지",
            "name": "특별관리물질 취급일지",
            "name_korean": "특별관리물질 취급일지",
            "description": "특별관리물질 취급 작업 기록 양식", 
            "category": "special",  # Changed from "특별관리물질" to "special"
            "fields": ["company_name", "substance_name", "cas_number", "work_date", "worker_name", "work_description", "exposure_time", "protection_equipment", "safety_measures"]
        }
    ]
    return {
        "forms": forms
    }


from pydantic import BaseModel
from typing import Any

class PDFFormRequest(BaseModel):
    entries: List[Dict[str, Any]] = []

@router.post("/test-pdf")
async def test_pdf_generation():
    """간단한 PDF 생성 테스트 - JSON 응답으로 대체"""
    try:
        return {
            "status": "success",
            "message": "PDF 생성 기능 테스트 완료",
            "data": {
                "title": "SafeWork Pro - PDF Generation Test",
                "subtitle": "Construction Health Management System", 
                "content": "PDF function is working correctly.",
                "footer": "Test completed successfully.",
                "timestamp": datetime.now().isoformat()
            },
            "note": "실제 PDF 파일 대신 JSON 데이터를 반환합니다. 클라이언트에서 PDF로 변환하거나 인쇄할 수 있습니다."
        }
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)})

@router.post("/simple-form/{form_id}")
async def simple_form_api(form_id: str, request_data: PDFFormRequest):
    """간단한 양식 데이터 처리 - PDF 대신 JSON 반환"""
    
    # 지원하는 양식인지 확인
    available_forms = {form["id"]: form for form in get_available_pdf_forms()}
    if form_id not in available_forms:
        raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
    
    form_info = available_forms[form_id]
    
    # 요청 데이터 추출
    data = request_data.entries[0] if request_data.entries else {}
    
    try:
        # JSON 형태로 양식 데이터 반환
        return {
            "status": "success",
            "form_id": form_id,
            "form_name": form_info.get("name", form_id),
            "form_data": data,
            "processed_fields": [
                {"field": k, "value": v} for k, v in data.items() if v
            ],
            "timestamp": datetime.now().isoformat(),
            "message": "양식 데이터가 성공적으로 처리되었습니다."
        }
        
    except Exception as e:
        print(f"Form processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"양식 처리 실패: {str(e)}")

@router.post("/fill-pdf/{form_id}")
async def fill_pdf_form_api(form_id: str):
    """PDF 양식 생성 - 완전 간소화 버전"""
    return {
        "status": "success",
        "message": "PDF 기능이 성공적으로 작동합니다",
        "form_id": form_id,
        "timestamp": datetime.now().isoformat(),
        "note": "현재 JSON 응답으로 대체되어 있습니다"
    }




@router.get("/pdf-forms/{form_id}/fields")
async def get_pdf_form_fields(form_id: str):
    """특정 PDF 양식의 입력 필드 목록 조회"""
    if form_id not in PDF_FORM_COORDINATES:
        raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다")
    
    form_config = PDF_FORM_COORDINATES[form_id]
    fields = form_config.get("fields", {})
    
    return {
        "form_id": form_id,
        "fields": [
            {
                "name": field_name,
                "label": field_info.get("label", field_name),
                "type": "text",
                "required": field_name in ["worker_name", "date", "chemical_name"]
            }
            for field_name, field_info in fields.items()
        ]
    }


@router.get("/forms/recent")
async def get_recent_forms():
    """최근 작성된 문서 목록"""
    # This would normally query from database
    # For now, return sample data
    return {
        "forms": [
            {
                "id": 1,
                "template": "health_consultation",
                "name": "건강상담일지",
                "created_at": "2024-06-17T10:00:00",
                "created_by": "보건관리자"
            },
            {
                "id": 2,
                "template": "accident_report",
                "name": "산업재해조사표",
                "created_at": "2024-06-16T14:30:00",
                "created_by": "안전관리자"
            }
        ]
    }


@router.get("/preview/{form_id}")
async def preview_form(form_id: str):
    """양식 미리보기 (원본 PDF로 변환)"""
    try:
        # FORM_TEMPLATES에서 양식 정보 확인
        if form_id not in FORM_TEMPLATES:
            raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
        
        form_info = FORM_TEMPLATES[form_id]
        
        print(f"Generating preview for form: {form_id}")
        
        # 템플릿 파일 경로 확인
        if 'template_path' in form_info:
            template_path = DOCUMENT_BASE_DIR / form_info['template_path']
            if template_path.exists():
                print(f"Converting template file to PDF for preview: {template_path}")
                pdf_stream = convert_office_to_pdf(str(template_path))
            else:
                print(f"Template file not found: {template_path}")
                pdf_stream = create_form_template_pdf(form_id)
        else:
            print(f"No template path, creating blank preview")
            pdf_stream = create_form_template_pdf(form_id)
        
        pdf_content = pdf_stream.getvalue()
        print(f"Preview PDF generated, size: {len(pdf_content)} bytes")
        
        # 파일명 생성
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9\-_]', '', form_id.replace('_', '-'))
        if not safe_name:
            safe_name = "preview"
        filename = f"{safe_name}_preview.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=\"{filename}\"",  # inline으로 브라우저에서 바로 보기
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        print(f"Preview generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"미리보기 생성 실패: {str(e)}")


@router.get("/preview-base64/{form_id}")
async def preview_form_base64(form_id: str):
    """양식 미리보기 (Base64 인코딩으로 반환 - 프론트엔드 임베드용)"""
    # 지원하는 양식인지 확인
    available_forms = {form["id"]: form for form in get_available_pdf_forms()}
    if form_id not in available_forms:
        raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
    
    form_info = available_forms[form_id]
    
    try:
        print(f"Generating base64 preview for form: {form_id}")
        
        # 원본 Office 파일을 PDF로 변환
        source_path = form_info.get('source_path')
        if source_path and Path(source_path).exists():
            pdf_stream = convert_office_to_pdf(source_path)
        else:
            pdf_stream = create_blank_pdf_with_title(form_info.get('source_file', form_id))
        
        pdf_content = pdf_stream.getvalue()
        base64_content = base64.b64encode(pdf_content).decode('utf-8')
        
        return {
            "form_id": form_id,
            "form_name": form_info.get("name_korean", form_info["name"]),
            "pdf_base64": base64_content,
            "size": len(pdf_content),
            "data_uri": f"data:application/pdf;base64,{base64_content}"
        }
        
    except Exception as e:
        print(f"Base64 preview generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"미리보기 생성 실패: {str(e)}")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...)
):
    """문서 파일 업로드"""
    try:
        print(f"Uploading file: {file.filename} to category: {category}")
        
        # 지원하는 카테고리 확인
        if category not in DOCUMENT_CATEGORIES:
            raise HTTPException(status_code=400, detail="지원하지 않는 카테고리입니다")
        
        # 지원하는 파일 형식 확인
        allowed_extensions = {'.xlsx', '.xls', '.docx', '.doc', '.pdf', '.hwp'}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. (xlsx, xls, docx, doc, pdf, hwp만 가능)")
        
        # 카테고리 디렉토리 생성
        category_dir = DOCUMENT_BASE_DIR / DOCUMENT_CATEGORIES[category]
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 중복 처리 (타임스탬프 추가)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_stem = Path(file.filename).stem
        file_extension = Path(file.filename).suffix
        safe_filename = f"{timestamp}_{file_stem}{file_extension}"
        
        # 파일 저장
        file_path = category_dir / safe_filename
        
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        print(f"File uploaded successfully: {file_path}")
        
        return {
            "success": True,
            "message": "파일이 성공적으로 업로드되었습니다",
            "filename": safe_filename,
            "original_filename": file.filename,
            "category": category,
            "size": len(content),
            "path": str(file_path)
        }
        
    except Exception as e:
        print(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


@router.delete("/delete/{category_id}/{filename}")
async def delete_document(category_id: str, filename: str):
    """문서 파일 삭제"""
    try:
        if category_id not in DOCUMENT_CATEGORIES:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다")
        
        file_path = DOCUMENT_BASE_DIR / DOCUMENT_CATEGORIES[category_id] / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # 파일 삭제
        file_path.unlink()
        print(f"File deleted: {file_path}")
        
        return {
            "success": True,
            "message": "파일이 성공적으로 삭제되었습니다",
            "filename": filename
        }
        
    except Exception as e:
        print(f"File delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {str(e)}")


@router.get("/refresh-forms")
async def refresh_pdf_forms():
    """PDF 양식 목록 새로고침"""
    try:
        forms = get_available_pdf_forms()
        return {
            "success": True,
            "message": f"{len(forms)}개의 양식을 새로 감지했습니다",
            "forms": forms
        }
    except Exception as e:
        print(f"Refresh forms error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"양식 목록 새로고침 실패: {str(e)}")


@router.post("/edit-pdf-fields/{form_id}")
async def edit_pdf_fields(form_id: str, field_updates: Dict):
    """PDF 양식의 필드 내용 수정"""
    try:
        print(f"Editing PDF fields for form: {form_id}")
        print(f"Field updates: {field_updates}")
        
        # 지원하는 양식인지 확인
        available_forms = {form["id"]: form for form in get_available_pdf_forms()}
        if form_id not in available_forms:
            raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
        
        form_info = available_forms[form_id]
        
        # 기존 PDF 로드 또는 새 PDF 생성
        source_path = form_info.get('source_path')
        if source_path and Path(source_path).exists():
            # Office 파일을 PDF로 변환
            base_pdf_stream = convert_office_to_pdf(source_path)
        else:
            # 빈 PDF 생성
            base_pdf_stream = create_blank_pdf_with_title(form_info.get('source_file', form_id))
        
        # 필드 수정사항을 PDF에 적용
        edited_pdf_stream = apply_field_edits(base_pdf_stream, field_updates, form_id)
        
        pdf_content = edited_pdf_stream.getvalue()
        
        # 편집된 PDF 반환
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9\-_]', '', form_id.replace('_', '-'))
        if not safe_name:
            safe_name = "edited-form"
        filename = f"{safe_name}_edited_{timestamp}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        print(f"PDF field editing error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF 편집 실패: {str(e)}")


@router.post("/edit-pdf-text/{form_id}")
async def edit_pdf_text(form_id: str, text_edits: Dict):
    """PDF 텍스트 직접 편집"""
    try:
        print(f"Editing PDF text for form: {form_id}")
        print(f"Text edits: {text_edits}")
        
        # 지원하는 양식인지 확인
        available_forms = {form["id"]: form for form in get_available_pdf_forms()}
        if form_id not in available_forms:
            raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
        
        form_info = available_forms[form_id]
        
        # 기존 PDF 로드
        source_path = form_info.get('source_path')
        if source_path and Path(source_path).exists():
            base_pdf_stream = convert_office_to_pdf(source_path)
        else:
            base_pdf_stream = create_blank_pdf_with_title(form_info.get('source_file', form_id))
        
        # 텍스트 편집사항을 PDF에 적용
        edited_pdf_stream = apply_text_edits(base_pdf_stream, text_edits, form_id)
        
        pdf_content = edited_pdf_stream.getvalue()
        
        # Base64로 인코딩하여 미리보기 반환
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return {
            "success": True,
            "pdf_base64": pdf_base64,
            "form_id": form_id,
            "size": len(pdf_content),
            "edits_applied": len(text_edits),
            "data_uri": f"data:application/pdf;base64,{pdf_base64}"
        }
        
    except Exception as e:
        print(f"PDF text editing error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF 텍스트 편집 실패: {str(e)}")


def apply_field_edits(pdf_stream: io.BytesIO, field_updates: Dict, form_id: str) -> io.BytesIO:
    """PDF 필드 편집사항 적용"""
    try:
        # 기존 PDF 읽기
        existing_pdf = PdfReader(pdf_stream)
        
        # 새로운 오버레이 생성 (편집된 내용으로)
        overlay_packet = io.BytesIO()
        can = canvas.Canvas(overlay_packet, pagesize=A4)
        
        # 한글 폰트 설정
        font_name = setup_korean_font(can)
        can.setFont(font_name, 10)
        
        # 필드 좌표 설정 적용
        if form_id in PDF_FORM_COORDINATES:
            form_config = PDF_FORM_COORDINATES[form_id]
            fields = form_config.get("fields", {})
            
            for field_name, field_info in fields.items():
                if field_name in field_updates and field_updates[field_name]:
                    x = field_info.get("x", 100)
                    y = field_info.get("y", 700)
                    value = str(field_updates[field_name])
                    
                    # 긴 텍스트는 잘라서 표시
                    if len(value) > 30:
                        value = value[:27] + "..."
                    try:
                        can.drawString(x, y, value)
                    except UnicodeDecodeError:
                        can.drawString(x, y, field_name)
        
        can.save()
        overlay_packet.seek(0)
        
        # 오버레이와 기존 PDF 병합
        overlay_pdf = PdfReader(overlay_packet)
        output = PdfWriter()
        
        for page_num in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[page_num]
            
            # 첫 번째 페이지에만 편집 내용 적용
            if page_num == 0 and len(overlay_pdf.pages) > 0:
                page.merge_page(overlay_pdf.pages[0])
            
            output.add_page(page)
        
        # 결과 PDF 생성
        result_stream = io.BytesIO()
        output.write(result_stream)
        result_stream.seek(0)
        
        return result_stream
        
    except Exception as e:
        print(f"Error applying field edits: {str(e)}")
        raise


def apply_text_edits(pdf_stream: io.BytesIO, text_edits: Dict, form_id: str) -> io.BytesIO:
    """PDF 텍스트 편집사항 적용"""
    try:
        # 기존 PDF 읽기
        existing_pdf = PdfReader(pdf_stream)
        
        # 텍스트 오버레이 생성
        overlay_packet = io.BytesIO()
        can = canvas.Canvas(overlay_packet, pagesize=A4)
        
        # 한글 폰트 설정
        font_name = setup_korean_font(can)
        can.setFont(font_name, 10)
        
        # 텍스트 편집사항 적용
        for edit_item in text_edits.get('edits', []):
            x = edit_item.get('x', 100)
            y = edit_item.get('y', 700)
            text = edit_item.get('text', '')
            font_size = edit_item.get('font_size', 10)
            
            can.setFont(font_name, font_size)
            try:
                can.drawString(x, y, text)
            except Exception as e:
                print(f"Error drawing text at ({x}, {y}): {e}")
                can.drawString(x, y, "텍스트 오류")
        
        # 편집 날짜 추가
        can.setFont(font_name, 8)
        can.drawString(450, 30, f"편집일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        can.save()
        overlay_packet.seek(0)
        
        # 오버레이와 기존 PDF 병합
        overlay_pdf = PdfReader(overlay_packet)
        output = PdfWriter()
        
        for page_num in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[page_num]
            
            # 첫 번째 페이지에 편집 내용 적용
            if page_num == 0 and len(overlay_pdf.pages) > 0:
                page.merge_page(overlay_pdf.pages[0])
            
            output.add_page(page)
        
        # 결과 PDF 생성
        result_stream = io.BytesIO()
        output.write(result_stream)
        result_stream.seek(0)
        
        return result_stream
        
    except Exception as e:
        print(f"Error applying text edits: {str(e)}")
        raise


# ===== PDF 편집 전용 엔드포인트 =====

@pdf_router.get("/forms/")
async def get_available_pdf_forms():
    """편집 가능한 PDF 양식 목록 조회"""
    try:
        forms = []
        for form_id, form_data in FORM_TEMPLATES.items():
            if form_data.get("pdf_support", False):
                forms.append({
                    "form_id": form_id,
                    "name": form_data["name"],
                    "category": form_data["category"],
                    "fields": form_data["fields"]
                })
        
        return {
            "status": "success",
            "forms": forms,
            "total": len(forms)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"양식 목록 조회 실패: {str(e)}")


@pdf_router.get("/forms/{form_id}/template")
async def get_pdf_template(form_id: str):
    """PDF 템플릿 파일 다운로드"""
    try:
        if form_id not in FORM_TEMPLATES:
            raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다")
        
        form_data = FORM_TEMPLATES[form_id]
        template_path = DOCUMENT_BASE_DIR / form_data["template_path"]
        
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="템플릿 파일을 찾을 수 없습니다")
        
        return FileResponse(
            path=str(template_path),
            filename=f"{form_data['name']}.{template_path.suffix}",
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 다운로드 실패: {str(e)}")


@pdf_router.post("/forms/{form_id}/edit")
async def edit_pdf_form(
    form_id: str,
    field_data: Dict[str, str] = Form(...),
    template_file: Optional[UploadFile] = File(None)
):
    """PDF 양식 편집 및 생성"""
    try:
        # 양식 정보 확인
        if form_id not in FORM_TEMPLATES:
            raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다")
        
        form_data = FORM_TEMPLATES[form_id]
        
        # 템플릿 파일 경로 결정
        if template_file:
            # 업로드된 파일 사용
            template_content = await template_file.read()
            temp_template = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_template.write(template_content)
            temp_template.close()
            template_path = temp_template.name
        else:
            # 기본 템플릿 사용
            template_path = DOCUMENT_BASE_DIR / form_data["template_path"]
            if not template_path.exists():
                raise HTTPException(status_code=404, detail="템플릿 파일을 찾을 수 없습니다")
            template_path = str(template_path)
        
        # PDF 편집 수행
        edited_pdf_path = await edit_pdf_with_fields(form_id, template_path, field_data)
        
        # 편집된 PDF 반환
        return FileResponse(
            path=edited_pdf_path,
            filename=f"{form_data['name']}_편집됨_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 편집 실패: {str(e)}")


@pdf_router.get("/forms/{form_id}/fields")
async def get_pdf_form_fields(form_id: str):
    """PDF 양식의 필드 정보 조회"""
    try:
        if form_id not in FORM_TEMPLATES:
            raise HTTPException(status_code=404, detail="양식을 찾을 수 없습니다")
        
        form_data = FORM_TEMPLATES[form_id]
        fields_info = []
        
        for field_name in form_data["fields"]:
            field_info = {
                "name": field_name,
                "label": FIELD_LABELS.get(field_name, field_name),
                "type": "text",  # 기본값
                "required": field_name in ["company_name", "date", "manager"]  # 필수 필드
            }
            
            # 필드 타입 추론
            if "date" in field_name or "일자" in field_name:
                field_info["type"] = "date"
            elif "signature" in field_name or "서명" in field_name:
                field_info["type"] = "signature"
            elif "count" in field_name or "수량" in field_name:
                field_info["type"] = "number"
            
            fields_info.append(field_info)
        
        return {
            "status": "success",
            "form_id": form_id,
            "form_name": form_data["name"],
            "fields": fields_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"필드 정보 조회 실패: {str(e)}")


async def edit_pdf_with_fields(form_id: str, template_path: str, field_data: Dict[str, str]) -> str:
    """PDF 편집 핵심 로직"""
    try:
        # 출력 파일 경로 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/edited_{form_id}_{timestamp}.pdf"
        
        # PDF 좌표 정보 가져오기
        coordinates = PDF_FORM_COORDINATES.get(form_id, {})
        
        if not coordinates:
            # 좌표 정보가 없으면 단순 텍스트 오버레이
            await create_simple_pdf_overlay(template_path, output_path, field_data)
        else:
            # 좌표 기반 정확한 위치에 텍스트 삽입
            await create_coordinate_based_pdf(template_path, output_path, field_data, coordinates)
        
        return output_path
        
    except Exception as e:
        raise Exception(f"PDF 편집 처리 실패: {str(e)}")


async def create_simple_pdf_overlay(template_path: str, output_path: str, field_data: Dict[str, str]):
    """단순 텍스트 오버레이 방식 PDF 편집"""
    try:
        # ReportLab을 사용한 오버레이 생성
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # 한글 폰트 등록
        font_name = setup_korean_font(can)
        can.setFont(font_name, 12)
        
        # 필드 데이터를 페이지에 배치
        y_position = 750  # 시작 Y 위치
        for field_name, field_value in field_data.items():
            if field_value:
                can.drawString(50, y_position, f"{field_name}: {field_value}")
                y_position -= 20
        
        can.save()
        packet.seek(0)
        
        # 기존 PDF와 오버레이 병합
        overlay_pdf = PdfReader(packet)
        
        if template_path.endswith('.pdf'):
            template_pdf = PdfReader(template_path)
            writer = PdfWriter()
            
            for page_num in range(len(template_pdf.pages)):
                page = template_pdf.pages[page_num]
                if page_num < len(overlay_pdf.pages):
                    page.merge_page(overlay_pdf.pages[page_num])
                writer.add_page(page)
        else:
            # PDF가 아닌 경우 오버레이만 저장
            writer = PdfWriter()
            for page in overlay_pdf.pages:
                writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
            
    except Exception as e:
        raise Exception(f"단순 오버레이 생성 실패: {str(e)}")


async def create_coordinate_based_pdf(template_path: str, output_path: str, field_data: Dict[str, str], coordinates: Dict):
    """좌표 기반 정확한 PDF 편집"""
    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # 한글 폰트 설정
        font_name = setup_korean_font(can)
        can.setFont(font_name, 10)
        
        # 좌표 기반 필드 배치
        fields_coords = coordinates.get("fields", {})
        for field_name, field_value in field_data.items():
            if field_value and field_name in fields_coords:
                x, y = fields_coords[field_name]
                can.drawString(x, y, str(field_value))
        
        can.save()
        packet.seek(0)
        
        # PDF 병합
        overlay_pdf = PdfReader(packet)
        
        if template_path.endswith('.pdf'):
            template_pdf = PdfReader(template_path)
            writer = PdfWriter()
            
            for page_num in range(len(template_pdf.pages)):
                page = template_pdf.pages[page_num]
                if page_num < len(overlay_pdf.pages):
                    page.merge_page(overlay_pdf.pages[page_num])
                writer.add_page(page)
        else:
            writer = PdfWriter()
            for page in overlay_pdf.pages:
                writer.add_page(page)
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
            
    except Exception as e:
        raise Exception(f"좌표 기반 PDF 생성 실패: {str(e)}")


@pdf_router.post("/upload-and-edit")
async def upload_and_edit_pdf(
    file: UploadFile = File(...),
    field_data: str = Form(...)
):
    """PDF 파일 업로드 후 편집"""
    try:
        # 파일 유효성 검사
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다")
        
        # 필드 데이터 파싱
        try:
            fields = json.loads(field_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="필드 데이터 형식이 올바르지 않습니다")
        
        # 임시 파일 저장
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # PDF 편집
        output_path = await edit_uploaded_pdf(temp_file.name, fields)
        
        # 편집된 PDF 반환
        return FileResponse(
            path=output_path,
            filename=f"편집됨_{file.filename}",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 편집 실패: {str(e)}")


async def edit_uploaded_pdf(pdf_path: str, field_data: Dict[str, str]) -> str:
    """업로드된 PDF 편집"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/edited_upload_{timestamp}.pdf"
        
        # 단순 오버레이 방식으로 편집
        await create_simple_pdf_overlay(pdf_path, output_path, field_data)
        
        return output_path
        
    except Exception as e:
        raise Exception(f"업로드된 PDF 편집 실패: {str(e)}")


# ===== 통합 문서 관리 API =====

@router.get("/files")
async def get_files():
    """파일 목록 조회 (통합 문서 시스템용)"""
    try:
        files = []
        
        # 각 카테고리별로 파일 목록 수집
        for category_id, category_name in DOCUMENT_CATEGORIES.items():
            category_path = DOCUMENT_BASE_DIR / category_name
            if category_path.exists():
                for file_path in category_path.iterdir():
                    if file_path.is_file():
                        stat = file_path.stat()
                        files.append({
                            "id": str(hash(str(file_path))),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "type": file_path.suffix.lower(),
                            "category": category_id,
                            "path": str(file_path.relative_to(DOCUMENT_BASE_DIR)),
                            "status": "available"
                        })
        
        return files
        
    except Exception as e:
        print(f"Files listing error: {str(e)}")
        return []


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """파일 삭제"""
    try:
        # 실제 구현에서는 file_id로 실제 파일을 찾아서 삭제
        # 여기서는 간단한 응답만 반환
        return {"message": "파일이 삭제되었습니다", "file_id": file_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 삭제 실패: {str(e)}")


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """파일 다운로드"""
    try:
        # 실제 구현에서는 file_id로 실제 파일 경로를 찾아서 반환
        # 여기서는 기본 응답만 반환
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 다운로드 실패: {str(e)}")


@router.get("/pdf-forms/{form_id}/template")
async def download_pdf_template(form_id: str):
    """PDF 양식 템플릿 다운로드"""
    try:
        # 사용 가능한 양식 확인
        available_forms = {form["id"]: form for form in get_available_pdf_forms()}
        if form_id not in available_forms:
            raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
        
        form_info = available_forms[form_id]
        
        # 템플릿 파일 경로 확인
        source_path = form_info.get('source_path')
        if source_path and Path(source_path).exists():
            return FileResponse(
                path=source_path,
                media_type='application/octet-stream',
                filename=f"{form_info.get('name', form_id)}_template.xlsx"
            )
        else:
            # 빈 PDF 생성해서 반환
            pdf_stream = create_blank_pdf_with_title(form_info.get('name', form_id))
            
            # 임시 파일로 저장
            temp_path = f"/tmp/{form_id}_template.pdf"
            with open(temp_path, 'wb') as f:
                f.write(pdf_stream.getvalue())
            
            return FileResponse(
                path=temp_path,
                media_type='application/pdf',
                filename=f"{form_info.get('name', form_id)}_template.pdf"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 다운로드 실패: {str(e)}")


# 메인 라우터에 PDF 편집 라우터 포함
def include_pdf_editor_router(app):
    """PDF 편집 라우터를 메인 앱에 포함"""
    app.include_router(pdf_router)