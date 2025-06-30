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
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 원본 파일을 임시 디렉토리에 복사
            temp_input = os.path.join(temp_dir, os.path.basename(office_file_path))
            shutil.copy2(office_file_path, temp_input)
            
            # LibreOffice로 PDF 변환
            cmd = [
                'libreoffice',
                '--headless',
                '--invisible',
                '--nodefault',
                '--nolockcheck',
                '--nologo',
                '--norestore',
                '--convert-to',
                'pdf',
                '--outdir',
                temp_dir,
                temp_input
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"LibreOffice conversion error: {result.stderr}")
                raise Exception(f"LibreOffice conversion failed: {result.stderr}")
            
            # 변환된 PDF 파일 찾기
            pdf_filename = os.path.splitext(os.path.basename(office_file_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            if not os.path.exists(pdf_path):
                raise Exception(f"Converted PDF not found: {pdf_path}")
            
            # PDF 내용을 BytesIO로 읽기
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            return io.BytesIO(pdf_content)
            
    except Exception as e:
        print(f"Office to PDF conversion error: {str(e)}")
        # 변환 실패시 빈 PDF 생성
        return create_blank_pdf_with_title(os.path.basename(office_file_path))




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
    template_info = FORM_TEMPLATES[template_id]
    
    print(f"Generating PDF for template: {template_id}")
    print(f"Data received: {data}")
    
    # 원본 PDF 경로 확인
    if 'original_pdf' in template_info:
        original_pdf_path = DOCUMENT_BASE_DIR / template_info['original_pdf']
        
        if original_pdf_path.exists():
            # 실제 원본 PDF 양식 사용
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
    
    # 원본 PDF가 없으면 reportlab으로 새로 생성
    print("Original PDF not found, creating new PDF with reportlab")
    
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
            "category": "관리대장"
        },
        {
            "id": "MSDS_관리대장",
            "name": "MSDS 관리대장", 
            "name_korean": "MSDS 관리대장",
            "description": "화학물질 안전보건자료 관리 양식",
            "category": "관리대장"
        },
        {
            "id": "건강관리_상담방문_일지",
            "name": "건강관리 상담방문 일지",
            "name_korean": "건강관리 상담방문 일지", 
            "description": "근로자 건강관리 상담 방문 기록 양식",
            "category": "건강관리"
        },
        {
            "id": "특별관리물질_취급일지",
            "name": "특별관리물질 취급일지",
            "name_korean": "특별관리물질 취급일지",
            "description": "특별관리물질 취급 작업 기록 양식", 
            "category": "특별관리물질"
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
    """간단한 PDF 생성 테스트"""
    try:
        # 간단한 PDF 생성
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # 기본 폰트 사용 (한글 폰트 문제 방지)
        can.setFont("Helvetica", 12)
        
        # 영어 테스트 텍스트 추가
        can.drawString(100, 750, "SafeWork Pro - PDF Generation Test")
        can.drawString(100, 700, "Construction Health Management System")
        can.drawString(100, 650, "PDF function is working correctly.")
        can.drawString(100, 600, "Test completed successfully.")
        
        can.save()
        
        # PDF 생성
        packet.seek(0)
        
        return Response(
            content=packet.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline; filename=test.pdf"
            }
        )
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")

@router.post("/fill-pdf/{form_id}")
async def fill_pdf_form_api(form_id: str, request_data: PDFFormRequest):
    """실제 Excel/Word 양식을 PDF로 변환하고 데이터를 입력하여 완성된 PDF 생성"""
    
    # 지원하는 양식인지 확인
    available_forms = {form["id"]: form for form in get_available_pdf_forms()}
    if form_id not in available_forms:
        raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
    
    form_info = available_forms[form_id]
    
    # 캐시 키 생성을 위한 데이터 해시
    data_str = json.dumps(request_data.model_dump(), sort_keys=True, ensure_ascii=False)
    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:12]
    
    # 캐시에서 PDF 조회
    cached_pdf = await get_cached_pdf(form_id, data_hash)
    if cached_pdf:
        print(f"PDF cache hit for form: {form_id}, hash: {data_hash}")
        return Response(
            content=cached_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={form_id}.pdf",
                "X-Cache": "HIT"
            }
        )
    
    try:
        print(f"Filling PDF form: {form_id}")
        print(f"Form data received: {request_data}")
        
        # 요청 데이터 추출
        data = request_data.entries[0] if request_data.entries else {}
        print(f"Extracted data: {data}")
        
        # 단순화된 PDF 생성 - 기본 템플릿 사용
        print(f"Creating simple PDF template for form: {form_id}")
        base_pdf_stream = create_form_template_pdf(form_id)
        
        # 2단계: 텍스트 오버레이 생성
        overlay_packet = io.BytesIO()
        can = canvas.Canvas(overlay_packet, pagesize=A4)
        
        # 한글 폰트 설정
        font_name = setup_korean_font(can)
        can.setFont(font_name, 10)
        
        # 3단계: 데이터 필드들을 좌표에 맞춰 추가
        if form_id in PDF_FORM_COORDINATES:
            coordinates = PDF_FORM_COORDINATES[form_id]
            field_labels = get_field_labels()
            
            for field_name, field_coords in coordinates.items():
                if isinstance(field_coords, dict):
                    # 중첩된 좌표 구조 (예: row_1, row_2 등) - 행별 데이터 처리
                    row_data = data.get(field_name, {})
                    if isinstance(row_data, dict):
                        for sub_field, (x, y) in field_coords.items():
                            if sub_field in row_data and row_data[sub_field]:
                                value = str(row_data[sub_field])
                                try:
                                    can.drawString(x, y, value)
                                except Exception as e:
                                    print(f"Error drawing field {field_name}.{sub_field}: {str(e)}")
                elif isinstance(field_coords, tuple) and len(field_coords) == 2:
                    # 단일 좌표 (x, y)
                    x, y = field_coords
                    if field_name in data and data[field_name]:
                        label = field_labels.get(field_name, field_name)
                        value = str(data[field_name])
                        try:
                            # 라벨과 값을 적절한 위치에 표시
                            can.drawString(x, y + 15, f"{label}:")
                            can.drawString(x, y, value)
                        except Exception as e:
                            print(f"Error drawing field {field_name}: {str(e)}")
                            can.drawString(x, y, f"{field_name}: {value}")
                else:
                    print(f"Invalid coordinate format for field {field_name}: {field_coords}")
        else:
            # 좌표 정보가 없으면 기본 위치에 순차 배치
            y_position = 700
            field_labels = get_field_labels()
            
            for field_name, value in data.items():
                if value:
                    label = field_labels.get(field_name, field_name)
                    try:
                        can.drawString(50, y_position, f"{label}: {str(value)}")
                        y_position -= 20
                        if y_position < 100:
                            break
                    except Exception as e:
                        print(f"Error drawing field {field_name}: {str(e)}")
        
        # 작성일 추가
        try:
            can.drawString(400, 50, f"작성일: {datetime.now().strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"Error drawing date: {str(e)}")
        
        can.save()
        overlay_packet.seek(0)
        
        # 4단계: 기본 PDF와 오버레이 결합
        try:
            base_pdf = PdfReader(base_pdf_stream)
            overlay_pdf = PdfReader(overlay_packet)
            output = PdfWriter()
            
            # 모든 페이지에 오버레이 적용 (첫 페이지에만 데이터)
            for page_num in range(len(base_pdf.pages)):
                page = base_pdf.pages[page_num]
                
                # 첫 번째 페이지에만 데이터 오버레이
                if page_num == 0 and len(overlay_pdf.pages) > 0:
                    page.merge_page(overlay_pdf.pages[0])
                
                output.add_page(page)
            
            # 최종 PDF 생성
            final_pdf_stream = io.BytesIO()
            output.write(final_pdf_stream)
            final_pdf_stream.seek(0)
            pdf_content = final_pdf_stream.getvalue()
            
        except Exception as e:
            print(f"PDF merge error: {str(e)}, using overlay only")
            # 병합 실패시 오버레이만 사용
            pdf_content = overlay_packet.getvalue()
        
        print(f"PDF form filled successfully, size: {len(pdf_content)} bytes")
        
        # PDF 결과 캐싱
        try:
            await cache_pdf_result(form_id, data_hash, pdf_content, CacheTTL.PDF_RESULT)
            print(f"PDF cached successfully for form: {form_id}, hash: {data_hash}")
        except Exception as cache_e:
            print(f"PDF caching failed (non-critical): {cache_e}")
        
        # 파일명 생성 (한글 파일명 처리)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9\-_]', '', form_id.replace('_', '-'))
        if not safe_name:
            safe_name = "form"
        filename = f"{safe_name}_{timestamp}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(pdf_content)),
                "X-Cache": "MISS",
                "X-Cache-TTL": str(CacheTTL.PDF_RESULT)
            }
        )
            
    except Exception as e:
        print(f"PDF form fill error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF 생성 실패: {str(e)}")




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
    # 지원하는 양식인지 확인
    available_forms = {form["id"]: form for form in get_available_pdf_forms()}
    if form_id not in available_forms:
        raise HTTPException(status_code=404, detail="지원하지 않는 양식입니다")
    
    form_info = available_forms[form_id]
    
    try:
        print(f"Generating preview for form: {form_id}")
        
        # 원본 Office 파일을 PDF로 변환
        source_path = form_info.get('source_path')
        if source_path and Path(source_path).exists():
            print(f"Converting office file to PDF for preview: {source_path}")
            pdf_stream = convert_office_to_pdf(source_path)
        else:
            print(f"Source file not found, creating blank preview")
            pdf_stream = create_blank_pdf_with_title(form_info.get('source_file', form_id))
        
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