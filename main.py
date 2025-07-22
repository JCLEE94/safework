#!/usr/bin/env python3
"""
SafeWork Pro - Main Application Entry Point
건설업 보건관리 시스템 메인 실행 파일
"""

import uvicorn
from src.app import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )