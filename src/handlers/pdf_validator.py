"""
PDF 문서 검증 및 좌표 최적화 도구
PDF Document Validation and Coordinate Optimization Tool
"""

import io
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import red, blue, green, black
import json


class PDFCoordinateValidator:
    """PDF 좌표 검증 및 최적화 도구"""
    
    def __init__(self, document_base_dir: str):
        self.document_base_dir = Path(document_base_dir)
        self.debug_mode = True
        self.font_name = self._setup_korean_font()
    
    def _setup_korean_font(self) -> str:
        """한글 폰트 설정"""
        try:
            # 시스템에서 사용 가능한 한글 폰트 경로들
            font_paths = [
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/System/Library/Fonts/AppleGothic.ttf",
                "/Windows/Fonts/malgun.ttf",
                "./fonts/NanumGothic.ttf"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                    return 'NanumGothic'
            
            # 폰트가 없으면 기본 폰트 사용
            print("Warning: Korean font not found, using default font")
            return 'Helvetica'
            
        except Exception as e:
            print(f"Font setup error: {e}")
            return 'Helvetica'
    
    def validate_coordinates(self, form_type: str, coordinates: Dict, test_data: Dict) -> Dict:
        """좌표 유효성 검증 및 최적화 제안"""
        validation_result = {
            "form_type": form_type,
            "valid_coordinates": [],
            "invalid_coordinates": [],
            "optimization_suggestions": [],
            "coverage_analysis": {}
        }
        
        # A4 용지 크기 체크
        a4_width, a4_height = A4
        
        for field_name, coord in coordinates.items():
            if isinstance(coord, dict):
                # 중첩된 좌표 구조 처리
                for sub_field, (x, y) in coord.items():
                    is_valid, suggestion = self._validate_single_coordinate(
                        f"{field_name}.{sub_field}", x, y, a4_width, a4_height
                    )
                    if is_valid:
                        validation_result["valid_coordinates"].append(f"{field_name}.{sub_field}")
                    else:
                        validation_result["invalid_coordinates"].append({
                            "field": f"{field_name}.{sub_field}",
                            "coordinate": (x, y),
                            "issue": suggestion
                        })
            elif isinstance(coord, tuple) and len(coord) == 2:
                x, y = coord
                is_valid, suggestion = self._validate_single_coordinate(
                    field_name, x, y, a4_width, a4_height
                )
                if is_valid:
                    validation_result["valid_coordinates"].append(field_name)
                else:
                    validation_result["invalid_coordinates"].append({
                        "field": field_name,
                        "coordinate": (x, y),
                        "issue": suggestion
                    })
        
        # 좌표 분포 분석
        validation_result["coverage_analysis"] = self._analyze_coordinate_distribution(coordinates)
        
        return validation_result
    
    def _validate_single_coordinate(self, field_name: str, x: float, y: float, 
                                  max_width: float, max_height: float) -> Tuple[bool, str]:
        """단일 좌표 검증"""
        issues = []
        
        # 경계 체크
        if x < 0 or x > max_width:
            issues.append(f"X 좌표 범위 초과: {x} (0-{max_width})")
        if y < 0 or y > max_height:
            issues.append(f"Y 좌표 범위 초과: {y} (0-{max_height})")
        
        # 마진 체크 (최소 20포인트 마진 권장)
        margin = 20
        if x < margin:
            issues.append(f"왼쪽 마진 부족: {x} < {margin}")
        if x > max_width - margin:
            issues.append(f"오른쪽 마진 부족: {x} > {max_width - margin}")
        if y < margin:
            issues.append(f"하단 마진 부족: {y} < {margin}")
        if y > max_height - margin:
            issues.append(f"상단 마진 부족: {y} > {max_height - margin}")
        
        # 읽기 가능 영역 체크 (중앙 영역 권장)
        readable_x_start = max_width * 0.1
        readable_x_end = max_width * 0.9
        readable_y_start = max_height * 0.1
        readable_y_end = max_height * 0.9
        
        if not (readable_x_start <= x <= readable_x_end and readable_y_start <= y <= readable_y_end):
            issues.append("권장 읽기 영역 밖에 위치")
        
        return len(issues) == 0, "; ".join(issues) if issues else "정상"
    
    def _analyze_coordinate_distribution(self, coordinates: Dict) -> Dict:
        """좌표 분포 분석"""
        all_coords = []
        
        def extract_coordinates(coord_dict):
            for key, value in coord_dict.items():
                if isinstance(value, dict):
                    extract_coordinates(value)
                elif isinstance(value, tuple) and len(value) == 2:
                    all_coords.append(value)
        
        extract_coordinates(coordinates)
        
        if not all_coords:
            return {"error": "좌표를 찾을 수 없음"}
        
        x_coords = [coord[0] for coord in all_coords]
        y_coords = [coord[1] for coord in all_coords]
        
        return {
            "total_fields": len(all_coords),
            "x_range": {"min": min(x_coords), "max": max(x_coords)},
            "y_range": {"min": min(y_coords), "max": max(y_coords)},
            "center_x": sum(x_coords) / len(x_coords),
            "center_y": sum(y_coords) / len(y_coords),
            "spread_x": max(x_coords) - min(x_coords),
            "spread_y": max(y_coords) - min(y_coords)
        }
    
    def create_coordinate_debug_pdf(self, form_type: str, coordinates: Dict, 
                                  output_path: str, test_data: Optional[Dict] = None) -> str:
        """좌표 디버깅용 PDF 생성"""
        debug_pdf = io.BytesIO()
        can = canvas.Canvas(debug_pdf, pagesize=A4)
        width, height = A4
        
        # 제목
        can.setFont(self.font_name, 16)
        title = f"좌표 디버그: {form_type}"
        title_width = can.stringWidth(title, self.font_name, 16)
        can.drawString((width - title_width) / 2, height - 50, title)
        
        # 그리드 그리기 (50포인트 간격)
        can.setStrokeColor(blue)
        can.setLineWidth(0.5)
        
        # 세로선
        for x in range(0, int(width), 50):
            can.line(x, 0, x, height)
            if x % 100 == 0:  # 100포인트마다 숫자 표시
                can.setFont(self.font_name, 8)
                can.drawString(x + 2, 10, str(x))
        
        # 가로선
        for y in range(0, int(height), 50):
            can.line(0, y, width, y)
            if y % 100 == 0:  # 100포인트마다 숫자 표시
                can.setFont(self.font_name, 8)
                can.drawString(10, y + 2, str(y))
        
        # 좌표 점과 필드명 표시
        can.setFont(self.font_name, 9)
        
        def draw_coordinate_markers(coord_dict, prefix=""):
            for field_name, coord in coord_dict.items():
                if isinstance(coord, dict):
                    draw_coordinate_markers(coord, f"{prefix}{field_name}.")
                elif isinstance(coord, tuple) and len(coord) == 2:
                    x, y = coord
                    full_name = f"{prefix}{field_name}"
                    
                    # 좌표 유효성에 따라 색상 설정
                    a4_width, a4_height = A4
                    is_valid, _ = self._validate_single_coordinate(full_name, x, y, a4_width, a4_height)
                    
                    if is_valid:
                        can.setFillColor(green)
                        can.setStrokeColor(green)
                    else:
                        can.setFillColor(red)
                        can.setStrokeColor(red)
                    
                    # 좌표 점 그리기
                    can.circle(x, y, 3, fill=1)
                    
                    # 필드명 표시
                    can.setFillColor(black)
                    text_x = x + 5
                    text_y = y + 5
                    
                    # 텍스트가 페이지를 벗어나지 않도록 조정
                    if text_x > width - 100:
                        text_x = x - 100
                    if text_y > height - 20:
                        text_y = y - 15
                    
                    can.drawString(text_x, text_y, full_name)
                    
                    # 테스트 데이터가 있으면 실제 값도 표시
                    if test_data and field_name in test_data:
                        can.setFillColor(blue)
                        can.drawString(text_x, text_y - 10, f"= {test_data[field_name]}")
                        can.setFillColor(black)
        
        draw_coordinate_markers(coordinates)
        
        # 범례
        can.setFont(self.font_name, 10)
        legend_y = height - 100
        can.setFillColor(green)
        can.circle(50, legend_y, 3, fill=1)
        can.setFillColor(black)
        can.drawString(60, legend_y - 3, "유효한 좌표")
        
        can.setFillColor(red)
        can.circle(50, legend_y - 20, 3, fill=1)
        can.setFillColor(black)
        can.drawString(60, legend_y - 23, "문제가 있는 좌표")
        
        can.setStrokeColor(blue)
        can.line(50, legend_y - 40, 70, legend_y - 40)
        can.drawString(75, legend_y - 43, "50포인트 그리드")
        
        can.save()
        
        # 파일 저장
        debug_pdf.seek(0)
        with open(output_path, 'wb') as f:
            f.write(debug_pdf.getvalue())
        
        return output_path
    
    def suggest_coordinate_improvements(self, form_type: str, coordinates: Dict) -> Dict:
        """좌표 개선 제안"""
        improvements = {
            "form_type": form_type,
            "suggestions": [],
            "optimized_coordinates": {}
        }
        
        # 좌표 밀도 분석
        density_analysis = self._analyze_coordinate_density(coordinates)
        
        # 겹치는 좌표 검사
        overlapping_coords = self._find_overlapping_coordinates(coordinates)
        if overlapping_coords:
            improvements["suggestions"].append({
                "type": "overlapping",
                "description": "겹치는 좌표가 발견됨",
                "affected_fields": overlapping_coords
            })
        
        # 정렬 개선 제안
        alignment_suggestions = self._suggest_alignment_improvements(coordinates)
        if alignment_suggestions:
            improvements["suggestions"].extend(alignment_suggestions)
        
        # 최적화된 좌표 생성
        optimized_coords = self._optimize_coordinates(coordinates)
        improvements["optimized_coordinates"] = optimized_coords
        
        return improvements
    
    def _analyze_coordinate_density(self, coordinates: Dict) -> Dict:
        """좌표 밀도 분석"""
        # 구현 생략 (복잡한 공간 분석 알고리즘)
        return {"density_score": 0.8, "hot_spots": []}
    
    def _find_overlapping_coordinates(self, coordinates: Dict, threshold: int = 10) -> List:
        """겹치는 좌표 찾기"""
        all_coords = []
        
        def extract_all_coordinates(coord_dict, prefix=""):
            for key, value in coord_dict.items():
                if isinstance(value, dict):
                    extract_all_coordinates(value, f"{prefix}{key}.")
                elif isinstance(value, tuple) and len(value) == 2:
                    all_coords.append((f"{prefix}{key}", value))
        
        extract_all_coordinates(coordinates)
        
        overlapping = []
        for i, (name1, coord1) in enumerate(all_coords):
            for j, (name2, coord2) in enumerate(all_coords[i+1:], i+1):
                distance = ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)**0.5
                if distance < threshold:
                    overlapping.append((name1, name2, distance))
        
        return overlapping
    
    def _suggest_alignment_improvements(self, coordinates: Dict) -> List:
        """정렬 개선 제안"""
        suggestions = []
        
        # X축 정렬 검사
        x_groups = {}
        
        def group_by_x_coordinate(coord_dict, prefix=""):
            for key, value in coord_dict.items():
                if isinstance(value, dict):
                    group_by_x_coordinate(value, f"{prefix}{key}.")
                elif isinstance(value, tuple) and len(value) == 2:
                    x = value[0]
                    x_rounded = round(x / 10) * 10  # 10포인트 단위로 그룹화
                    if x_rounded not in x_groups:
                        x_groups[x_rounded] = []
                    x_groups[x_rounded].append(f"{prefix}{key}")
        
        group_by_x_coordinate(coordinates)
        
        # 비슷한 X 좌표를 가진 필드들을 정렬 제안
        for x_coord, fields in x_groups.items():
            if len(fields) >= 3:  # 3개 이상의 필드가 비슷한 X 좌표를 가질 때
                suggestions.append({
                    "type": "vertical_alignment",
                    "description": f"X={x_coord} 근처의 필드들을 수직 정렬 가능",
                    "fields": fields,
                    "suggested_x": x_coord
                })
        
        return suggestions
    
    def _optimize_coordinates(self, coordinates: Dict) -> Dict:
        """좌표 최적화"""
        # 기본적인 최적화: 그리드에 맞춤
        optimized = {}
        
        def optimize_recursive(coord_dict):
            result = {}
            for key, value in coord_dict.items():
                if isinstance(value, dict):
                    result[key] = optimize_recursive(value)
                elif isinstance(value, tuple) and len(value) == 2:
                    x, y = value
                    # 5포인트 단위로 반올림
                    optimized_x = round(x / 5) * 5
                    optimized_y = round(y / 5) * 5
                    result[key] = (optimized_x, optimized_y)
                else:
                    result[key] = value
            return result
        
        return optimize_recursive(coordinates)


def run_coordinate_validation():
    """좌표 검증 실행 함수"""
    # 실제 좌표 데이터 가져오기
    from documents import PDF_FORM_COORDINATES
    
    validator = PDFCoordinateValidator("/home/jclee/dev/health/document")
    
    results = {}
    
    # 각 양식별 검증
    for form_type, coordinates in PDF_FORM_COORDINATES.items():
        print(f"\n=== {form_type} 검증 중 ===")
        
        # 테스트 데이터
        test_data = {
            "worker_name": "김철수",
            "employee_id": "2024001",
            "exam_date": "2024-06-20",
            "exam_agency": "한국산업보건협회",
            "exam_result": "정상",
            "opinion": "이상없음"
        }
        
        # 검증 실행
        validation_result = validator.validate_coordinates(form_type, coordinates, test_data)
        results[form_type] = validation_result
        
        # 결과 출력
        print(f"유효한 좌표: {len(validation_result['valid_coordinates'])}개")
        print(f"문제있는 좌표: {len(validation_result['invalid_coordinates'])}개")
        
        if validation_result['invalid_coordinates']:
            print("문제가 있는 좌표들:")
            for invalid in validation_result['invalid_coordinates']:
                print(f"  - {invalid['field']}: {invalid['coordinate']} ({invalid['issue']})")
        
        # 디버그 PDF 생성
        debug_pdf_path = f"/tmp/debug_{form_type}.pdf"
        validator.create_coordinate_debug_pdf(form_type, coordinates, debug_pdf_path, test_data)
        print(f"디버그 PDF 생성: {debug_pdf_path}")
        
        # 개선 제안
        improvements = validator.suggest_coordinate_improvements(form_type, coordinates)
        if improvements['suggestions']:
            print("개선 제안:")
            for suggestion in improvements['suggestions']:
                print(f"  - {suggestion['type']}: {suggestion['description']}")
    
    return results


if __name__ == "__main__":
    run_coordinate_validation()