"""
PDF 자동 필드 매핑 및 채우기 핸들러
Automatic PDF form field detection and filling handler
"""

import io
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
# import fitz  # PyMuPDF - disabled due to missing dependency
from fillpdf import fillpdfs
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
from pypdf import PdfReader, PdfWriter

from ..utils.pdf_field_detector import PDFFieldDetector
from ..config.pdf_forms import PDF_FORM_COORDINATES, FIELD_LABELS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pdf-auto", tags=["pdf-auto"])


class PDFAutoFiller:
    """PDF 자동 채우기 클래스"""
    
    def __init__(self):
        self.detector = PDFFieldDetector()
        self.field_mappings = {
            # 한글 -> 영문 필드명 매핑
            "사업장명": ["company_name", "company", "사업장", "회사명", "업체명"],
            "부서명": ["department", "dept", "부서", "팀", "소속"],
            "근로자명": ["worker_name", "name", "성명", "이름", "작업자명"],
            "사번": ["employee_id", "emp_id", "id", "번호", "직원번호"],
            "날짜": ["date", "작성일", "일자", "작성일자", "등록일"],
            "서명": ["signature", "sign", "사인", "확인", "서명란"],
            
            # 화학물질 관련
            "화학물질명": ["chemical_name", "물질명", "제품명", "chemical"],
            "CAS번호": ["cas_number", "cas", "CAS", "cas_no"],
            "제조업체": ["manufacturer", "제조사", "업체명", "maker"],
            "사용량": ["quantity", "amount", "용량", "수량"],
            "보관장소": ["storage_location", "storage", "보관", "장소"],
            
            # 건강검진 관련
            "검진일": ["exam_date", "검진일자", "진단일", "examination_date"],
            "검진기관": ["exam_agency", "기관", "병원", "의료기관"],
            "소견": ["opinion", "의견", "결과", "소견사항"],
            "검진결과": ["exam_result", "result", "결과", "판정"],
        }

    def detect_fields_with_fillpdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """fillpdf 라이브러리를 사용한 필드 감지"""
        try:
            # 임시 파일로 저장
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(pdf_content)
                tmp_path = tmp.name
            
            # fillpdf로 필드 추출
            fields = fillpdfs.get_form_fields(tmp_path)
            
            # 임시 파일 삭제
            import os
            os.unlink(tmp_path)
            
            return fields or {}
            
        except Exception as e:
            logger.error(f"fillpdf 필드 감지 오류: {str(e)}")
            return {}

    def detect_fields_with_pdfminer(self, pdf_content: bytes) -> Dict[str, Any]:
        """PDFMiner를 사용한 AcroForm 필드 감지"""
        try:
            fp = io.BytesIO(pdf_content)
            parser = PDFParser(fp)
            doc = PDFDocument(parser)
            
            fields = {}
            if 'AcroForm' in doc.catalog:
                acroform = resolve1(doc.catalog['AcroForm'])
                if 'Fields' in acroform:
                    for field_ref in acroform['Fields']:
                        field = resolve1(field_ref)
                        field_name = field.get('T', b'').decode('utf-8', errors='ignore')
                        field_value = field.get('V', b'')
                        if isinstance(field_value, bytes):
                            field_value = field_value.decode('utf-8', errors='ignore')
                        
                        fields[field_name] = {
                            'value': field_value,
                            'type': field.get('FT', b'').decode('utf-8', errors='ignore'),
                            'flags': field.get('Ff', 0)
                        }
            
            return fields
            
        except Exception as e:
            logger.error(f"PDFMiner 필드 감지 오류: {str(e)}")
            return {}

    def map_fields_intelligently(
        self, detected_fields: Dict[str, Any], user_data: Dict[str, str]
    ) -> Dict[str, str]:
        """지능적 필드 매핑"""
        mapped_data = {}
        
        # 1. 정확한 이름 매칭
        for field_name in detected_fields:
            if field_name in user_data:
                mapped_data[field_name] = user_data[field_name]
                continue
            
            # 2. 대소문자 무시 매칭
            field_lower = field_name.lower()
            for user_key, user_value in user_data.items():
                if user_key.lower() == field_lower:
                    mapped_data[field_name] = user_value
                    break
            
            # 3. 매핑 테이블 기반 매칭
            if field_name not in mapped_data:
                for korean_name, eng_names in self.field_mappings.items():
                    # 한글 필드명 확인
                    if korean_name in field_name:
                        for user_key, user_value in user_data.items():
                            if user_key in eng_names or user_key == korean_name:
                                mapped_data[field_name] = user_value
                                break
                    
                    # 영문 필드명 확인
                    for eng_name in eng_names:
                        if eng_name in field_lower:
                            for user_key, user_value in user_data.items():
                                if user_key.lower() in [n.lower() for n in eng_names]:
                                    mapped_data[field_name] = user_value
                                    break
        
        return mapped_data

    async def auto_fill_pdf(
        self, pdf_content: bytes, user_data: Dict[str, str]
    ) -> bytes:
        """PDF 자동 채우기"""
        try:
            # 1. 모든 방법으로 필드 감지
            fillpdf_fields = self.detect_fields_with_fillpdf(pdf_content)
            pdfminer_fields = self.detect_fields_with_pdfminer(pdf_content)
            pymupdf_fields = self.detector.detect_fields_pymupdf(pdf_content)
            
            # 필드 통합
            all_detected_fields = {
                **fillpdf_fields,
                **pdfminer_fields,
                **pymupdf_fields
            }
            
            if not all_detected_fields:
                logger.warning("PDF에서 폼 필드를 찾을 수 없습니다")
                # 필드가 없으면 오버레이 방식 시도
                return await self._create_overlay_pdf(pdf_content, user_data)
            
            # 2. 지능적 필드 매핑
            mapped_data = self.map_fields_intelligently(
                all_detected_fields, user_data
            )
            
            # 3. fillpdf로 채우기 시도
            if fillpdf_fields:
                return await self._fill_with_fillpdf(pdf_content, mapped_data)
            
            # 4. PyMuPDF로 채우기 시도
            # PyMuPDF disabled due to size constraints - use fillpdfs instead
            return await self._fill_with_fillpdfs(pdf_content, mapped_data)
            
        except Exception as e:
            logger.error(f"PDF 자동 채우기 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _fill_with_fillpdf(
        self, pdf_content: bytes, field_data: Dict[str, str]
    ) -> bytes:
        """fillpdf를 사용한 PDF 채우기"""
        import tempfile
        import os
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as input_tmp:
            input_tmp.write(pdf_content)
            input_path = input_tmp.name
        
        output_path = input_path.replace('.pdf', '_filled.pdf')
        
        try:
            # fillpdf로 채우기
            fillpdfs.write_fillable_pdf(input_path, output_path, field_data)
            
            # 결과 읽기
            with open(output_path, 'rb') as f:
                result = f.read()
            
            return result
            
        finally:
            # 임시 파일 정리
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    async def _fill_with_pymupdf(
        self, pdf_content: bytes, field_data: Dict[str, str]
    ) -> bytes:
        """PyMuPDF를 사용한 PDF 채우기"""
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        try:
            for page in doc:
                for widget in page.widgets():
                    if widget.field_name in field_data:
                        widget.field_value = field_data[widget.field_name]
                        widget.update()
            
            # 결과 반환
            return doc.tobytes()
            
        finally:
            doc.close()

    async def _create_overlay_pdf(
        self, pdf_content: bytes, user_data: Dict[str, str]
    ) -> bytes:
        """오버레이 방식으로 PDF 생성 (필드가 없는 경우)"""
        # 기존 오버레이 로직 사용
        from ..handlers.documents import create_text_overlay
        
        # 임시로 첫 번째 양식 사용
        form_id = list(PDF_FORM_COORDINATES.keys())[0]
        overlay_packet = create_text_overlay(user_data, form_id)
        
        if not overlay_packet:
            return pdf_content
        
        # PDF 병합
        reader = PdfReader(io.BytesIO(pdf_content))
        writer = PdfWriter()
        overlay_reader = PdfReader(overlay_packet)
        
        for page_num, page in enumerate(reader.pages):
            if page_num < len(overlay_reader.pages):
                page.merge_page(overlay_reader.pages[page_num])
            writer.add_page(page)
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.read()


# API 엔드포인트
auto_filler = PDFAutoFiller()


@router.post("/detect-fields")
async def detect_pdf_fields(file: UploadFile = File(...)):
    """PDF 파일의 필드 자동 감지"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원됩니다")
    
    content = await file.read()
    
    # 모든 감지 방법 사용
    result = {
        "fillpdf_fields": auto_filler.detect_fields_with_fillpdf(content),
        "pdfminer_fields": auto_filler.detect_fields_with_pdfminer(content),
        "auto_detection": auto_filler.detector.auto_detect_and_map(content)
    }
    
    return result


@router.post("/auto-fill")
async def auto_fill_pdf(
    file: UploadFile = File(...),
    data: str = Form(...)  # JSON 문자열로 받음
):
    """PDF 자동 채우기"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원됩니다")
    
    import json
    try:
        user_data = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="잘못된 JSON 데이터")
    
    content = await file.read()
    filled_pdf = await auto_filler.auto_fill_pdf(content, user_data)
    
    return Response(
        content=filled_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=auto_filled_{file.filename}"
        }
    )


@router.post("/suggest-mapping")
async def suggest_field_mapping(
    file: UploadFile = File(...),
    target_form: Optional[str] = None
):
    """PDF 필드와 타겟 양식 간의 매핑 제안"""
    content = await file.read()
    
    # 필드 감지
    detected = auto_filler.detector.auto_detect_and_map(content)
    
    # 타겟 양식과 매핑 제안
    suggestions = []
    if target_form and target_form in PDF_FORM_COORDINATES:
        target_fields = PDF_FORM_COORDINATES[target_form]["fields"]
        
        for target_field, field_info in target_fields.items():
            label = field_info.get("label", target_field)
            
            # 감지된 필드에서 매칭 찾기
            best_match = None
            for detected_field in detected["detected_fields"]:
                if auto_filler._is_field_match(detected_field, label):
                    best_match = detected_field
                    break
            
            suggestions.append({
                "target_field": target_field,
                "target_label": label,
                "detected_field": best_match,
                "confidence": "high" if best_match else "low"
            })
    
    return {
        "detected_fields": detected["detected_fields"],
        "mapping_suggestions": suggestions,
        "auto_mapped": detected["mapped_fields"]
    }


def _is_field_match(field_name: str, target_label: str) -> bool:
    """필드 이름 매칭 확인"""
    field_lower = field_name.lower()
    label_lower = target_label.lower()
    
    # 정확한 매칭
    if field_lower == label_lower:
        return True
    
    # 부분 매칭
    if label_lower in field_lower or field_lower in label_lower:
        return True
    
    # 유사어 매칭
    similar_words = {
        "name": ["이름", "성명", "명"],
        "date": ["날짜", "일자", "일"],
        "company": ["회사", "사업장", "업체"],
        "dept": ["부서", "팀", "소속"]
    }
    
    for eng, kor_list in similar_words.items():
        if eng in field_lower:
            for kor in kor_list:
                if kor in label_lower:
                    return True
    
    return False