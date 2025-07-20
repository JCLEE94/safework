"""QR 등록 페이지 라우트"""
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
from src.config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/qr-register")
async def serve_qr_register():
    """QR 등록 페이지를 위한 특별 라우트"""
    static_dir = (
        settings.static_files_dir
        if os.path.exists(settings.static_files_dir)
        else os.path.join(os.path.dirname(__file__), "../../static")
    )
    return FileResponse(os.path.join(static_dir, "index.html"))