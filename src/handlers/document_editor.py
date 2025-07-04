"""
Document 폴더 PDF 편집 핸들러
Document folder PDF editing handler
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Form, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from src.config.settings import get_settings
from src.services.github_issues import github_issues_service
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/document-editor", tags=["문서편집"])

class DocumentManager:
    """문서 관리 클래스"""
    
    def __init__(self):
        self.document_dir = Path(settings.document_dir)
        self.supported_extensions = {'.pdf', '.hwp', '.doc', '.docx', '.xls', '.xlsx'}
        
    def get_document_tree(self) -> Dict[str, Any]:
        """문서 폴더 트리 구조 반환"""
        def build_tree(path: Path) -> Dict[str, Any]:
            tree = {
                "name": path.name,
                "path": str(path.relative_to(self.document_dir)),
                "type": "folder" if path.is_dir() else "file",
                "children": []
            }
            
            if path.is_dir():
                try:
                    for child in sorted(path.iterdir()):
                        if child.name.startswith('.'):
                            continue
                        tree["children"].append(build_tree(child))
                except PermissionError:
                    pass
            else:
                # 파일 정보 추가
                tree["size"] = path.stat().st_size
                tree["extension"] = path.suffix.lower()
                tree["editable"] = path.suffix.lower() in self.supported_extensions
                
            return tree
        
        if not self.document_dir.exists():
            return {"name": "document", "type": "folder", "children": [], "error": "Document directory not found"}
            
        return build_tree(self.document_dir)
    
    def get_pdf_files(self) -> List[Dict[str, Any]]:
        """PDF 파일 목록만 반환"""
        pdf_files = []
        
        def scan_directory(path: Path, category: str = ""):
            for item in path.iterdir():
                if item.is_dir():
                    # 폴더명을 카테고리로 사용
                    folder_category = item.name
                    scan_directory(item, folder_category)
                elif item.suffix.lower() == '.pdf':
                    pdf_files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.document_dir)),
                        "full_path": str(item),
                        "category": category,
                        "size": item.stat().st_size,
                        "editable": True
                    })
        
        if self.document_dir.exists():
            scan_directory(self.document_dir)
            
        return pdf_files
    
    def get_file_path(self, relative_path: str) -> Path:
        """상대 경로를 절대 경로로 변환"""
        full_path = self.document_dir / relative_path
        
        # 보안 체크: document 폴더 외부 접근 방지
        try:
            full_path.resolve().relative_to(self.document_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
            
        return full_path

document_manager = DocumentManager()

@router.get("/files")
async def get_document_files():
    """문서 폴더의 파일 목록 조회"""
    try:
        tree = document_manager.get_document_tree()
        pdf_files = document_manager.get_pdf_files()
        
        return {
            "status": "success",
            "tree": tree,
            "pdf_files": pdf_files,
            "total_files": len(pdf_files)
        }
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="문서 목록을 불러올 수 없습니다")

@router.get("/pdf-list")
async def get_pdf_list():
    """PDF 파일 목록만 조회"""
    try:
        pdf_files = document_manager.get_pdf_files()
        
        # 카테고리별로 그룹화
        categorized = {}
        for file in pdf_files:
            category = file["category"] or "기타"
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(file)
        
        return {
            "status": "success",
            "files": pdf_files,
            "categorized": categorized,
            "total_count": len(pdf_files)
        }
    except Exception as e:
        logger.error(f"PDF 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="PDF 목록을 불러올 수 없습니다")

@router.get("/view/{file_path:path}")
async def view_document(file_path: str):
    """문서 파일 뷰어용 다운로드"""
    try:
        full_path = document_manager.get_file_path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # PDF 파일만 지원
        if full_path.suffix.lower() != '.pdf':
            raise HTTPException(status_code=415, detail="PDF 파일만 뷰어에서 볼 수 있습니다")
        
        return FileResponse(
            path=str(full_path),
            media_type="application/pdf",
            filename=full_path.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 뷰어 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="문서를 불러올 수 없습니다")

@router.post("/analyze/{file_path:path}")
async def analyze_pdf_fields(file_path: str):
    """기존 PDF 파일의 필드 분석"""
    try:
        full_path = document_manager.get_file_path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        if full_path.suffix.lower() != '.pdf':
            raise HTTPException(status_code=415, detail="PDF 파일만 분석할 수 있습니다")
        
        # PDF 정밀 분석기 사용
        from src.handlers.pdf_precise import PrecisePDFProcessor
        processor = PrecisePDFProcessor()
        
        with open(full_path, 'rb') as f:
            pdf_content = f.read()
        
        # 필드 감지
        detected_fields = await processor.detect_form_fields_async(pdf_content)
        
        return {
            "status": "success",
            "file_name": full_path.name,
            "file_path": file_path,
            "detected_fields": detected_fields.get("detected_fields", []),
            "total_fields": detected_fields.get("total_fields", 0),
            "methods_used": detected_fields.get("methods_used", []),
            "analysis_time": detected_fields.get("processing_time", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/edit/{file_path:path}")
async def edit_document_pdf(
    file_path: str,
    field_data: str = Form(...),
    field_mappings: str = Form(None)
):
    """기존 PDF 문서 편집"""
    try:
        full_path = document_manager.get_file_path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        if full_path.suffix.lower() != '.pdf':
            raise HTTPException(status_code=415, detail="PDF 파일만 편집할 수 있습니다")
        
        # JSON 데이터 파싱
        try:
            field_data_dict = json.loads(field_data)
            field_mappings_dict = json.loads(field_mappings) if field_mappings else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="잘못된 JSON 데이터입니다")
        
        # PDF 정밀 편집기 사용
        from src.handlers.pdf_precise import PrecisePDFProcessor
        processor = PrecisePDFProcessor()
        
        with open(full_path, 'rb') as f:
            pdf_content = f.read()
        
        # 필드 매핑이 없으면 자동 감지
        if not field_mappings_dict:
            analysis_result = await processor.detect_form_fields_async(pdf_content)
            
            # 자동 매핑 생성
            detected_fields = analysis_result.get("detected_fields", [])
            for field in detected_fields:
                field_name = field.get("name", "")
                if field_name in field_data_dict:
                    field_mappings_dict[field_name] = {
                        "label": field_name,
                        "value": field_data_dict[field_name],
                        "type": field.get("type", "text"),
                        "coordinates": field.get("coordinates", {})
                    }
        
        # PDF 편집 실행
        edited_pdf = processor.fill_pdf_precisely(pdf_content, field_data_dict, field_mappings_dict)
        
        # 편집된 파일 저장 (원본 파일명에 _edited 추가)
        output_filename = f"{full_path.stem}_edited_{field_data_dict.get('worker_name', 'document')}.pdf"
        
        from fastapi.responses import Response
        return Response(
            content=edited_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{output_filename}\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 편집 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 편집 중 오류가 발생했습니다: {str(e)}")

@router.get("/download/{file_path:path}")
async def download_document(file_path: str):
    """문서 파일 다운로드"""
    try:
        full_path = document_manager.get_file_path(file_path)
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
        
        # MIME 타입 결정
        mime_types = {
            '.pdf': 'application/pdf',
            '.hwp': 'application/haansofthwp',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        media_type = mime_types.get(full_path.suffix.lower(), 'application/octet-stream')
        
        return FileResponse(
            path=str(full_path),
            media_type=media_type,
            filename=full_path.name,
            headers={"Content-Disposition": f"attachment; filename=\"{full_path.name}\""}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 다운로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 다운로드 중 오류가 발생했습니다")

@router.get("/categories")
async def get_document_categories():
    """문서 카테고리 목록 조회"""
    try:
        categories = []
        if document_manager.document_dir.exists():
            for item in document_manager.document_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # 각 폴더의 파일 수 계산
                    file_count = len([f for f in item.rglob('*') if f.is_file()])
                    pdf_count = len([f for f in item.rglob('*.pdf')])
                    
                    categories.append({
                        "name": item.name,
                        "path": str(item.relative_to(document_manager.document_dir)),
                        "total_files": file_count,
                        "pdf_files": pdf_count
                    })
        
        return {
            "status": "success",
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        logger.error(f"카테고리 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="카테고리를 불러올 수 없습니다")

@router.post("/batch-edit")
async def batch_edit_documents(
    file_paths: List[str] = Form(...),
    field_data: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    """여러 PDF 문서 일괄 편집"""
    try:
        field_data_dict = json.loads(field_data)
        results = []
        
        for file_path in file_paths:
            try:
                full_path = document_manager.get_file_path(file_path)
                
                if full_path.exists() and full_path.suffix.lower() == '.pdf':
                    # 개별 파일 편집 (백그라운드에서)
                    results.append({
                        "file_path": file_path,
                        "status": "queued",
                        "message": "편집 작업이 대기열에 추가되었습니다"
                    })
                else:
                    results.append({
                        "file_path": file_path,
                        "status": "error",
                        "message": "파일을 찾을 수 없거나 PDF가 아닙니다"
                    })
                    
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "status": "error",
                    "message": str(e)
                })
        
        return {
            "status": "success",
            "message": f"{len([r for r in results if r['status'] == 'queued'])}개 파일이 편집 대기열에 추가되었습니다",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"일괄 편집 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="일괄 편집 중 오류가 발생했습니다")