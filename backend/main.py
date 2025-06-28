#!/usr/bin/env python3
"""
SafeWork Pro Entry Point
건설업 보건관리 시스템 진입점

건설업 보건관리자를 위한 통합 관리 시스템
"""

import os
import uvicorn
from src.app import create_app

def main():
    """애플리케이션 진입점"""
    app = create_app()
    
    # 환경변수에서 포트 읽기, 기본값 3001 (nginx 제거)
    port = int(os.environ.get("PORT", 3001))
    
    # 프로덕션 환경에서는 bind to all interfaces
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()