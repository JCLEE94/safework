#!/usr/bin/env python3
"""
SafeWork Pro 전체 시스템 테스트 스크립트
Complete system testing script for SafeWork Pro
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

# 환경 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
HEALTH_URL = os.getenv("HEALTH_URL", "http://localhost:8000/health")


class Colors:
    """터미널 색상"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_status(message, status="info"):
    """상태 메시지 출력"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "success":
        print(f"[{timestamp}] {Colors.GREEN}✅ {message}{Colors.ENDC}")
    elif status == "error":
        print(f"[{timestamp}] {Colors.RED}❌ {message}{Colors.ENDC}")
    elif status == "warning":
        print(f"[{timestamp}] {Colors.YELLOW}⚠️  {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {Colors.BLUE}ℹ️  {message}{Colors.ENDC}")


def test_api_endpoint(url, method="GET", data=None, expected_status=200):
    """API 엔드포인트 테스트"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)

        if response.status_code == expected_status:
            return True, response.json() if response.content else None
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)


def test_health_check():
    """헬스 체크 테스트"""
    print_status("헬스 체크 테스트 시작...")

    success, result = test_api_endpoint(HEALTH_URL)
    if success:
        print_status("헬스 체크 성공", "success")
        if isinstance(result, dict):
            print(f"  - 서비스: {result.get('service')}")
            print(f"  - 버전: {result.get('version')}")
            print(f"  - 상태: {result.get('status')}")
            print(f"  - 컴포넌트: {result.get('components', {})}")
        return True
    else:
        print_status(f"헬스 체크 실패: {result}", "error")
        return False


def test_api_endpoints():
    """주요 API 엔드포인트 테스트"""
    print_status("API 엔드포인트 테스트 시작...")

    endpoints = [
        # 기본 엔드포인트
        ("/workers/", "GET", "근로자 목록"),
        ("/health-exams/", "GET", "건강진단 목록"),
        ("/chemical-substances/", "GET", "화학물질 목록"),
        ("/work-environments/", "GET", "작업환경 목록"),
        ("/accident-reports/", "GET", "사고신고 목록"),
        ("/health-educations/", "GET", "보건교육 목록"),
        # 대시보드
        ("/dashboard", "GET", "대시보드 데이터"),
        # 문서 관리
        ("/documents/", "GET", "문서 목록"),
        ("/documents/stats", "GET", "문서 통계"),
        ("/documents/pdf-forms", "GET", "PDF 양식 목록"),
        ("/documents/categories", "GET", "문서 카테고리"),
        ("/documents/files", "GET", "파일 목록"),
        # 모니터링
        ("/monitoring/metrics", "GET", "시스템 메트릭"),
        ("/monitoring/health", "GET", "시스템 상태"),
    ]

    passed = 0
    failed = 0

    for endpoint, method, description in endpoints:
        url = f"{API_BASE_URL}{endpoint}"
        success, result = test_api_endpoint(url, method)

        if success:
            print_status(f"{description} ✓", "success")
            passed += 1
        else:
            print_status(f"{description} ✗ ({result})", "error")
            failed += 1

    print_status(f"API 테스트 완료: {passed}개 성공, {failed}개 실패")
    return failed == 0


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print_status("데이터베이스 연결 테스트...")

    # 간단한 쿼리로 DB 연결 확인
    success, result = test_api_endpoint(f"{API_BASE_URL}/dashboard")

    if success:
        print_status("데이터베이스 연결 성공", "success")
        return True
    else:
        print_status(f"데이터베이스 연결 실패: {result}", "error")
        return False


def test_file_operations():
    """파일 작업 테스트"""
    print_status("파일 작업 테스트...")

    # 문서 파일 목록 확인
    success, result = test_api_endpoint(f"{API_BASE_URL}/documents/files")

    if success:
        file_count = len(result) if isinstance(result, list) else 0
        print_status(f"파일 목록 조회 성공 ({file_count}개 파일)", "success")
        return True
    else:
        print_status(f"파일 작업 실패: {result}", "error")
        return False


def test_pdf_functionality():
    """PDF 기능 테스트"""
    print_status("PDF 기능 테스트...")

    # PDF 양식 목록 확인
    success, result = test_api_endpoint(f"{API_BASE_URL}/documents/pdf-forms")

    if success:
        form_count = len(result.get("forms", [])) if isinstance(result, dict) else 0
        print_status(f"PDF 양식 조회 성공 ({form_count}개 양식)", "success")
        return True
    else:
        print_status(f"PDF 기능 실패: {result}", "error")
        return False


def test_authentication():
    """인증 시스템 테스트"""
    print_status("인증 시스템 테스트...")

    # 현재는 개발 모드라서 인증이 스킵됨
    # 인증이 필요한 엔드포인트에 접근해보기
    success, result = test_api_endpoint(f"{API_BASE_URL}/workers/", "GET")

    if success:
        print_status("인증 시스템 작동 (개발 모드)", "success")
        return True
    else:
        print_status(f"인증 시스템 오류: {result}", "error")
        return False


def test_error_handling():
    """에러 처리 테스트"""
    print_status("에러 처리 테스트...")

    # 존재하지 않는 엔드포인트 테스트
    success, result = test_api_endpoint(
        f"{API_BASE_URL}/non-existent-endpoint", expected_status=404
    )

    if success:
        print_status("404 에러 처리 정상", "success")
        return True
    else:
        print_status(f"에러 처리 실패: {result}", "error")
        return False


def run_performance_test():
    """간단한 성능 테스트"""
    print_status("성능 테스트 시작...")

    import time

    # 대시보드 API 10회 연속 호출
    start_time = time.time()
    success_count = 0

    for i in range(10):
        success, _ = test_api_endpoint(f"{API_BASE_URL}/dashboard")
        if success:
            success_count += 1

    end_time = time.time()
    duration = end_time - start_time
    avg_time = duration / 10

    if success_count >= 8:  # 80% 이상 성공
        print_status(f"성능 테스트 통과 - 평균 응답시간: {avg_time:.2f}초", "success")
        return True
    else:
        print_status(f"성능 테스트 실패 - {success_count}/10 성공", "error")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print(f"{Colors.BOLD}SafeWork Pro 시스템 테스트 시작{Colors.ENDC}")
    print("=" * 60)

    tests = [
        ("헬스 체크", test_health_check),
        ("데이터베이스 연결", test_database_connection),
        ("API 엔드포인트", test_api_endpoints),
        ("파일 작업", test_file_operations),
        ("PDF 기능", test_pdf_functionality),
        ("인증 시스템", test_authentication),
        ("에러 처리", test_error_handling),
        ("성능 테스트", run_performance_test),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{Colors.BLUE}[{test_name}]{Colors.ENDC}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_status(f"{test_name} 테스트 중 예외 발생: {e}", "error")
            failed += 1

    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}테스트 결과 요약{Colors.ENDC}")
    print(f"✅ 성공: {passed}")
    print(f"❌ 실패: {failed}")
    print(f"📊 성공률: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 모든 테스트 통과!{Colors.ENDC}")
        return True
    else:
        print(
            f"\n{Colors.YELLOW}⚠️  일부 테스트 실패. 시스템 점검이 필요합니다.{Colors.ENDC}"
        )
        return False


def main():
    """메인 함수"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # 빠른 테스트 (헬스체크만)
        success = test_health_check()
        sys.exit(0 if success else 1)
    else:
        # 전체 테스트
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
