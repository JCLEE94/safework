"""
정밀 PDF 필드 감지 및 정확한 좌표 기반 채우기 핸들러
Precise PDF field detection and coordinate-based filling handler
"""

import io
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
# import fitz  # PyMuPDF - disabled due to missing dependency
import numpy as np
from PIL import Image
import cv2
import pytesseract
from pdfplumber import PDF
import pdfplumber
from fillpdf import fillpdfs
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pdf-precise", tags=["pdf-precise"])


class PrecisePDFProcessor:
    """정밀 PDF 처리 클래스"""
    
    def __init__(self):
        self.dpi = 300  # 고해상도 OCR용
        self.confidence_threshold = 0.7
        
        # 한국어 필드명 패턴 매칭
        self.field_patterns = {
            'name': ['이름', '성명', '명', 'name', '근로자명', '작업자명', '신청인', '성함'],
            'date': ['날짜', '일자', '일', 'date', '작성일', '등록일', '신청일', '검진일'],
            'company': ['회사', '사업장', '업체', 'company', '회사명', '사업장명', '업체명', '소속'],
            'department': ['부서', '팀', '소속', 'dept', 'department', '부서명', '팀명'],
            'id': ['번호', 'id', '사번', '직원번호', '등록번호', '관리번호'],
            'phone': ['전화', '연락처', 'phone', 'tel', '휴대폰', '전화번호'],
            'address': ['주소', 'address', '거주지', '소재지', '위치'],
            'signature': ['서명', '사인', 'signature', '확인', '서명란', '날인'],
            'position': ['직책', '직위', 'position', 'title', '담당', '역할'],
            'age': ['나이', 'age', '연령', '년생', '생년월일'],
            'gender': ['성별', 'gender', '남/여', '성', 'sex']
        }

    def extract_form_fields_advanced(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """고급 PDF 폼 필드 추출 (PyMuPDF + pdfplumber + OCR 결합)"""
        detected_fields = []
        
        try:
            # 1. PyMuPDF로 기본 폼 필드 추출
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 위젯 기반 필드 감지
                for widget in page.widgets():
                    if widget.field_name:
                        rect = widget.rect
                        field_info = {
                            'name': widget.field_name,
                            'type': self._determine_field_type(widget.field_type_string, widget.field_name),
                            'coordinates': {
                                'x': float(rect.x0),
                                'y': float(rect.y0),
                                'width': float(rect.x1 - rect.x0),
                                'height': float(rect.y1 - rect.y0),
                                'page': page_num + 1
                            },
                            'confidence': 0.95,
                            'method': 'pymupdf_widget'
                        }
                        detected_fields.append(field_info)
            
            doc.close()
            
            # 2. pdfplumber로 텍스트 패턴 기반 필드 감지
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 텍스트 객체 분석
                    chars = page.chars
                    words = page.extract_words()
                    
                    # 빈 텍스트 박스나 밑줄 패턴 감지
                    detected_patterns = self._detect_text_patterns(words, chars, page_num + 1)
                    detected_fields.extend(detected_patterns)
            
            # 3. OCR 기반 필드 감지 (텍스트가 적은 경우)
            if len(detected_fields) < 5:  # 감지된 필드가 적으면 OCR 보강
                ocr_fields = self._detect_fields_with_ocr(pdf_content)
                detected_fields.extend(ocr_fields)
            
            # 4. 중복 제거 및 정확도 기반 필터링
            filtered_fields = self._filter_and_deduplicate_fields(detected_fields)
            
            return filtered_fields
            
        except Exception as e:
            logger.error(f"고급 필드 추출 오류: {str(e)}")
            return []

    def _determine_field_type(self, widget_type: str, field_name: str) -> str:
        """위젯 타입과 필드명으로 필드 타입 결정"""
        field_name_lower = field_name.lower()
        
        # 위젯 타입 우선
        if 'text' in widget_type.lower():
            # 텍스트 필드 세부 분류
            if any(pattern in field_name_lower for pattern in ['date', '날짜', '일자']):
                return 'date'
            elif any(pattern in field_name_lower for pattern in ['sign', '서명', '사인']):
                return 'signature'
            else:
                return 'text'
        elif 'check' in widget_type.lower() or 'button' in widget_type.lower():
            return 'checkbox'
        elif 'radio' in widget_type.lower():
            return 'radio'
        else:
            return 'text'

    def _detect_text_patterns(self, words: List[Dict], chars: List[Dict], page_num: int) -> List[Dict[str, Any]]:
        """텍스트 패턴 기반 필드 감지"""
        detected_fields = []
        
        for i, word in enumerate(words):
            word_text = word['text'].strip()
            
            # 콜론이나 괄호로 끝나는 라벨 패턴 감지
            if word_text.endswith(':') or word_text.endswith('：') or '(        )' in word_text:
                label = word_text.rstrip(':：')
                
                # 필드 타입 결정
                field_type = self._classify_field_by_label(label)
                
                # 입력 영역 추정 (라벨 옆의 빈 공간)
                input_area = self._estimate_input_area(word, words[i+1:i+3] if i+1 < len(words) else [])
                
                if input_area:
                    field_info = {
                        'name': label,
                        'type': field_type,
                        'coordinates': {
                            'x': input_area['x0'],
                            'y': input_area['top'],
                            'width': input_area['x1'] - input_area['x0'],
                            'height': input_area['bottom'] - input_area['top'],
                            'page': page_num
                        },
                        'confidence': 0.8,
                        'method': 'text_pattern'
                    }
                    detected_fields.append(field_info)
        
        return detected_fields

    def _classify_field_by_label(self, label: str) -> str:
        """라벨 텍스트로 필드 타입 분류"""
        label_lower = label.lower()
        
        for field_type, patterns in self.field_patterns.items():
            if any(pattern in label_lower for pattern in patterns):
                if field_type in ['name', 'company', 'department', 'id', 'phone', 'address', 'position']:
                    return 'text'
                elif field_type == 'date':
                    return 'date'
                elif field_type == 'signature':
                    return 'signature'
                elif field_type in ['age', 'gender']:
                    return 'text'
        
        return 'text'

    def _estimate_input_area(self, label_word: Dict, next_words: List[Dict]) -> Optional[Dict]:
        """라벨 다음의 입력 영역 추정"""
        label_bbox = label_word
        
        # 라벨 바로 옆에 충분한 공간이 있는지 확인
        estimated_width = max(100, len(label_word['text']) * 8)  # 최소 100px
        
        input_area = {
            'x0': label_bbox['x1'] + 5,  # 라벨 끝에서 5px 간격
            'x1': label_bbox['x1'] + estimated_width,
            'top': label_bbox['top'],
            'bottom': label_bbox['bottom']
        }
        
        # 다음 단어들과 겹치지 않는지 확인
        for next_word in next_words:
            if (next_word['x0'] < input_area['x1'] and 
                next_word['top'] < input_area['bottom'] and 
                next_word['bottom'] > input_area['top']):
                # 겹치면 너비 조정
                input_area['x1'] = min(input_area['x1'], next_word['x0'] - 5)
        
        # 최소 너비 확인
        if input_area['x1'] - input_area['x0'] < 50:
            return None
            
        return input_area

    def _detect_fields_with_ocr(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """OCR을 사용한 필드 감지"""
        detected_fields = []
        
        try:
            # PDF를 이미지로 변환
            images = convert_from_bytes(pdf_content, dpi=self.dpi)
            
            for page_num, image in enumerate(images):
                # OCR로 텍스트와 위치 정보 추출
                ocr_data = pytesseract.image_to_data(
                    image, 
                    lang='kor+eng',  # 한글+영어
                    output_type=pytesseract.Output.DICT,
                    config='--psm 6'  # 텍스트 블록 모드
                )
                
                # 신뢰도 높은 텍스트만 필터링
                for i in range(len(ocr_data['text'])):
                    if int(ocr_data['conf'][i]) > 30:  # 신뢰도 30% 이상
                        text = ocr_data['text'][i].strip()
                        
                        # 필드 라벨 패턴 감지
                        if self._is_field_label(text):
                            # 입력 영역 추정
                            input_coords = self._estimate_ocr_input_area(
                                ocr_data, i, image.size
                            )
                            
                            if input_coords:
                                field_info = {
                                    'name': text.rstrip(':：'),
                                    'type': self._classify_field_by_label(text),
                                    'coordinates': {
                                        'x': input_coords['x'],
                                        'y': input_coords['y'],
                                        'width': input_coords['width'],
                                        'height': input_coords['height'],
                                        'page': page_num + 1
                                    },
                                    'confidence': int(ocr_data['conf'][i]) / 100,
                                    'method': 'ocr'
                                }
                                detected_fields.append(field_info)
                                
        except Exception as e:
            logger.error(f"OCR 필드 감지 오류: {str(e)}")
        
        return detected_fields

    def _is_field_label(self, text: str) -> bool:
        """텍스트가 필드 라벨인지 판단"""
        if len(text) < 2 or len(text) > 20:
            return False
            
        # 라벨 패턴 확인
        if text.endswith(':') or text.endswith('：'):
            return True
            
        # 알려진 필드 패턴과 매칭
        text_lower = text.lower()
        for patterns in self.field_patterns.values():
            if any(pattern in text_lower for pattern in patterns):
                return True
                
        return False

    def _estimate_ocr_input_area(self, ocr_data: Dict, label_index: int, image_size: Tuple[int, int]) -> Optional[Dict]:
        """OCR 데이터에서 입력 영역 추정"""
        label_left = ocr_data['left'][label_index]
        label_top = ocr_data['top'][label_index]
        label_width = ocr_data['width'][label_index]
        label_height = ocr_data['height'][label_index]
        
        # PDF 좌표계로 변환 (DPI 고려)
        scale_x = 595 / image_size[0]  # A4 width
        scale_y = 842 / image_size[1]  # A4 height
        
        input_area = {
            'x': (label_left + label_width + 10) * scale_x,
            'y': 842 - (label_top + label_height) * scale_y,  # Y축 뒤집기
            'width': max(100, label_width) * scale_x,
            'height': label_height * scale_y
        }
        
        return input_area

    def _filter_and_deduplicate_fields(self, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 필드 제거 및 정확도 기반 필터링"""
        if not fields:
            return []
        
        # 신뢰도 기준으로 정렬
        fields.sort(key=lambda x: x['confidence'], reverse=True)
        
        filtered_fields = []
        used_names = set()
        
        for field in fields:
            # 신뢰도 임계값 확인
            if field['confidence'] < self.confidence_threshold:
                continue
                
            # 중복 이름 확인
            if field['name'] in used_names:
                continue
                
            # 좌표 유효성 확인
            coords = field['coordinates']
            if coords['width'] <= 0 or coords['height'] <= 0:
                continue
                
            filtered_fields.append(field)
            used_names.add(field['name'])
        
        return filtered_fields

    def fill_pdf_precisely(
        self, 
        pdf_content: bytes, 
        field_data: Dict[str, str],
        field_mappings: Dict[str, Any]
    ) -> bytes:
        """정확한 좌표 기반 PDF 채우기"""
        try:
            # PyMuPDF로 PDF 열기
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            for field_name, value in field_data.items():
                if not value:
                    continue
                    
                # 필드 매핑 정보 가져오기
                field_info = field_mappings.get(field_name)
                if not field_info:
                    continue
                
                coords = field_info['coordinates']
                page_num = coords['page'] - 1
                
                if page_num >= len(doc):
                    continue
                    
                page = doc[page_num]
                
                # 필드 타입에 따른 처리
                field_type = field_info.get('type', 'text')
                
                if field_type == 'checkbox':
                    self._draw_checkbox(page, coords, value == 'true')
                elif field_type == 'signature':
                    self._draw_signature(page, coords, value)
                else:
                    self._draw_text(page, coords, value, field_type)
            
            # 결과 반환
            result = doc.tobytes()
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"정밀 PDF 채우기 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _draw_text(self, page, coords: Dict, text: str, field_type: str):
        """텍스트 필드 그리기"""
        rect = fitz.Rect(
            coords['x'], 
            coords['y'], 
            coords['x'] + coords['width'], 
            coords['y'] + coords['height']
        )
        
        # 폰트 크기 자동 조정
        font_size = min(12, coords['height'] * 0.7)
        
        # 날짜 필드 특별 처리
        if field_type == 'date' and len(text) == 10 and '-' in text:
            text = text.replace('-', '.')  # 2024-01-01 -> 2024.01.01
        
        # 텍스트 삽입
        page.insert_text(
            (rect.x0 + 2, rect.y0 + font_size + 2),  # 약간의 패딩
            text,
            fontsize=font_size,
            color=(0, 0, 0),  # 검은색
            fontname="helv"  # Helvetica
        )
        
        # 디버그용 경계선 (개발 시에만)
        # page.draw_rect(rect, color=(0, 1, 0), width=0.5)

    def _draw_checkbox(self, page, coords: Dict, checked: bool):
        """체크박스 그리기"""
        rect = fitz.Rect(
            coords['x'], 
            coords['y'], 
            coords['x'] + coords['width'], 
            coords['y'] + coords['height']
        )
        
        # 체크박스 경계선
        page.draw_rect(rect, color=(0, 0, 0), width=1)
        
        # 체크 표시
        if checked:
            # X 표시 또는 체크 마크
            page.draw_line(
                (rect.x0 + 2, rect.y0 + 2), 
                (rect.x1 - 2, rect.y1 - 2), 
                color=(0, 0, 0), width=2
            )
            page.draw_line(
                (rect.x1 - 2, rect.y0 + 2), 
                (rect.x0 + 2, rect.y1 - 2), 
                color=(0, 0, 0), width=2
            )

    def _draw_signature(self, page, coords: Dict, name: str):
        """서명 필드 그리기"""
        rect = fitz.Rect(
            coords['x'], 
            coords['y'], 
            coords['x'] + coords['width'], 
            coords['y'] + coords['height']
        )
        
        # 서명선 그리기
        line_y = rect.y1 - 5
        page.draw_line(
            (rect.x0, line_y), 
            (rect.x1, line_y), 
            color=(0, 0, 0), width=1
        )
        
        # 이름 추가 (서명선 위에)
        if name:
            font_size = min(10, coords['height'] * 0.5)
            page.insert_text(
                (rect.x0 + 2, line_y - 2),
                name,
                fontsize=font_size,
                color=(0, 0, 0),
                fontname="helv"
            )


# API 엔드포인트
processor = PrecisePDFProcessor()


@router.post("/detect-fields")
async def detect_precise_fields(file: UploadFile = File(...)):
    """정밀 PDF 필드 감지"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원됩니다")
    
    content = await file.read()
    
    try:
        detected_fields = processor.extract_form_fields_advanced(content)
        
        return {
            "status": "success",
            "detected_fields": detected_fields,
            "total_fields": len(detected_fields),
            "methods_used": list(set(field.get('method', 'unknown') for field in detected_fields))
        }
        
    except Exception as e:
        logger.error(f"정밀 필드 감지 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-fill")
async def precise_auto_fill(
    file: UploadFile = File(...),
    field_data: str = Form(...),
    field_mappings: str = Form(...)
):
    """정밀 좌표 기반 PDF 자동 채우기"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원됩니다")
    
    try:
        content = await file.read()
        data = json.loads(field_data)
        mappings = json.loads(field_mappings)
        
        filled_pdf = processor.fill_pdf_precisely(content, data, mappings)
        
        return Response(
            content=filled_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=precise_filled_{file.filename}"
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="잘못된 JSON 데이터")
    except Exception as e:
        logger.error(f"정밀 PDF 채우기 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-structure")
async def analyze_pdf_structure(file: UploadFile = File(...)):
    """PDF 구조 분석 (디버깅용)"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 지원됩니다")
    
    content = await file.read()
    
    try:
        # PyMuPDF로 구조 분석
        doc = fitz.open(stream=content, filetype="pdf")
        structure_info = {
            "pages": len(doc),
            "page_info": [],
            "form_fields": [],
            "text_blocks": []
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 페이지 정보
            page_info = {
                "page": page_num + 1,
                "size": {
                    "width": page.rect.width,
                    "height": page.rect.height
                },
                "widgets": len(page.widgets()),
                "text_blocks": len(page.get_text("dict")["blocks"])
            }
            structure_info["page_info"].append(page_info)
            
            # 폼 필드 정보
            for widget in page.widgets():
                if widget.field_name:
                    field_info = {
                        "name": widget.field_name,
                        "type": widget.field_type_string,
                        "page": page_num + 1,
                        "rect": {
                            "x0": widget.rect.x0,
                            "y0": widget.rect.y0,
                            "x1": widget.rect.x1,
                            "y1": widget.rect.y1
                        }
                    }
                    structure_info["form_fields"].append(field_info)
        
        doc.close()
        return structure_info
        
    except Exception as e:
        logger.error(f"PDF 구조 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))