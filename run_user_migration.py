#!/usr/bin/env python3
"""
사용자 테이블 마이그레이션 실행 스크립트
Run user table migration
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.database import get_async_session
from src.models.migration_users import create_users_table, drop_users_table


async def main():
    """메인 마이그레이션 함수"""
    print("🚀 SafeWork Pro 사용자 테이블 마이그레이션 시작...")
    
    try:
        # 데이터베이스 연결
        async with get_async_session() as session:
            print("📊 데이터베이스 연결 성공")
            
            # 사용자 테이블 생성
            await create_users_table(session)
            
            print("✅ 사용자 테이블 마이그레이션 완료!")
            print("\n📋 기본 관리자 계정:")
            print("  이메일: admin@safework.local")
            print("  비밀번호: admin123!")
            print("  역할: admin")
            
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())