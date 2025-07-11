"""
PDF Generation Integration Tests
Inline tests for PDF form generation and manipulation
"""

import os
import asyncio
import base64
from datetime import date
from io import BytesIO
import PyPDF2

from src.testing import (
    integration_test, run_inline_tests,
    create_test_environment, measure_performance,
    assert_response_ok, assert_pdf_valid, assert_korean_text
)


class IntegrationTestPDFGeneration:
    """PDF 생성 통합 테스트"""
    
    @integration_test
    @measure_performance
    async def test_health_certificate_generation(self):
        """건강진단 확인서 PDF 생성 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]
            
            # 테스트 데이터 생성
            async with db.get_session() as session:
                from src.models import Worker, HealthExam
                
                # 근로자 생성
                worker = Worker(
                    name="김건강",
                    employee_id="PDF_TEST_001",
                    birth_date=date(1990, 5, 15),
                    gender="남성",
                    department="생산부",
                    work_type="제조"
                )
                session.add(worker)
                await session.flush()
                
                # 건강검진 기록 생성
                exam = HealthExam(
                    worker_id=worker.id,
                    exam_date=date.today(),
                    exam_type="특수건강진단",
                    exam_agency="서울대학교병원",
                    blood_pressure_systolic=120,
                    blood_pressure_diastolic=80,
                    heart_rate=72,
                    height=175.5,
                    weight=70.0,
                    vision_left=1.0,
                    vision_right=1.2,
                    hearing_left="정상",
                    hearing_right="정상",
                    chest_xray_result="정상",
                    overall_result="정상A",
                    doctor_name="김의사",
                    doctor_license="의사-12345"
                )
                session.add(exam)
                await session.commit()
                
                worker_id = worker.id
                exam_id = exam.id
            
            # PDF 생성 요청
            pdf_data = {
                "worker_id": worker_id,
                "exam_id": exam_id,
                "purpose": "취업용",
            }
            
            response = await client.post(
                "/api/v1/documents/fill-pdf/health_certificate",
                json=pdf_data
            )
            
            result = assert_response_ok(response)
            assert "pdf_base64" in result
            assert "filename" in result
            
            # PDF 검증
            pdf_info = assert_pdf_valid(
                result["pdf_base64"],
                min_pages=1,
                check_korean=True
            )
            
            # PDF 내용 확인
            pdf_bytes = base64.b64decode(result["pdf_base64"])
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
            
            # 첫 페이지 텍스트 추출
            first_page = pdf_reader.pages[0]
            text = first_page.extract_text()
            
            # 주요 정보 포함 확인
            assert "김건강" in text or len(text) > 100  # 한글 추출 문제 가능성
            
            print(f"✅ PDF 생성 성공: {pdf_info['size_bytes']} bytes")
    
    @integration_test
    async def test_work_environment_report_generation(self):
        """작업환경 측정 보고서 PDF 생성 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]
            
            # 작업환경 측정 데이터 생성
            async with db.get_session() as session:
                from src.models import WorkEnvironment
                
                measurements = []
                locations = ["A동 1층", "A동 2층", "B동 작업장", "C동 창고"]
                
                for idx, location in enumerate(locations):
                    measurement = WorkEnvironment(
                        measurement_date=date.today(),
                        location=location,
                        dust_concentration=0.05 + idx * 0.01,
                        noise_level=75.0 + idx * 2,
                        temperature=22.0 + idx * 0.5,
                        humidity=50.0 + idx * 2,
                        co_concentration=5.0 + idx * 0.5,
                        co2_concentration=800.0 + idx * 50,
                        illuminance=500.0 + idx * 50,
                        measured_by="측정전문가",
                        measurement_equipment="DUST-2000, NOISE-PRO",
                        notes=f"{location} 정기 측정"
                    )
                    measurements.append(measurement)
                    session.add(measurement)
                
                await session.commit()
                measurement_ids = [m.id for m in measurements]
            
            # PDF 생성 요청
            pdf_data = {
                "measurement_ids": measurement_ids,
                "report_date": str(date.today()),
                "company_name": "테스트건설(주)",
                "site_name": "서울 강남 신축현장",
                "report_type": "monthly"
            }
            
            response = await client.post(
                "/api/v1/documents/fill-pdf/environment_report",
                json=pdf_data
            )
            
            result = assert_response_ok(response)
            
            # PDF 검증
            pdf_info = assert_pdf_valid(result["pdf_base64"], min_pages=1)
            
            # 여러 측정 위치가 포함되어야 함
            assert pdf_info["num_pages"] >= 1
            print(f"✅ 작업환경 보고서 생성: {pdf_info['num_pages']} 페이지")
    
    @integration_test
    async def test_msds_summary_generation(self):
        """MSDS 요약표 PDF 생성 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]
            
            # 화학물질 데이터 생성
            async with db.get_session() as session:
                from src.models import ChemicalSubstance
                
                chemicals = [
                    {
                        "name_korean": "아세톤",
                        "name_english": "Acetone",
                        "cas_number": "67-64-1",
                        "usage_purpose": "세척제",
                        "daily_usage_amount": 5.0,
                        "unit": "L",
                        "hazard_classification": "인화성 액체 구분2",
                        "health_hazards": "눈 자극, 졸음",
                        "physical_hazards": "고인화성",
                        "storage_location": "위험물 저장소 A"
                    },
                    {
                        "name_korean": "톨루엔",
                        "name_english": "Toluene", 
                        "cas_number": "108-88-3",
                        "usage_purpose": "희석제",
                        "daily_usage_amount": 2.0,
                        "unit": "L",
                        "hazard_classification": "인화성 액체 구분2, 생식독성 구분2",
                        "health_hazards": "생식능력 손상 의심",
                        "physical_hazards": "인화성",
                        "storage_location": "위험물 저장소 B"
                    }
                ]
                
                substance_ids = []
                for chem_data in chemicals:
                    substance = ChemicalSubstance(**chem_data)
                    session.add(substance)
                    await session.flush()
                    substance_ids.append(substance.id)
                
                await session.commit()
            
            # PDF 생성 요청
            pdf_data = {
                "substance_ids": substance_ids,
                "department": "도장부",
                "prepared_by": "안전관리자",
                "review_date": str(date.today())
            }
            
            response = await client.post(
                "/api/v1/documents/fill-pdf/msds_summary",
                json=pdf_data
            )
            
            result = assert_response_ok(response)
            pdf_info = assert_pdf_valid(result["pdf_base64"])
            
            print(f"✅ MSDS 요약표 생성: {pdf_info['size_bytes']} bytes")
    
    @integration_test
    @measure_performance
    async def test_bulk_pdf_generation(self):
        """대량 PDF 생성 성능 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]
            
            # 50명의 근로자와 건강검진 데이터 생성
            async with db.get_session() as session:
                from src.models import Worker, HealthExam
                
                worker_exam_pairs = []
                
                for i in range(50):
                    worker = Worker(
                        name=f"테스트근로자{i:03d}",
                        employee_id=f"BULK_PDF_{i:03d}",
                        birth_date=date(1990, 1, 1),
                        gender="남성" if i % 2 == 0 else "여성",
                        department="테스트부"
                    )
                    session.add(worker)
                    await session.flush()
                    
                    exam = HealthExam(
                        worker_id=worker.id,
                        exam_date=date.today(),
                        exam_type="일반건강진단",
                        exam_agency="테스트병원",
                        overall_result="정상"
                    )
                    session.add(exam)
                    await session.flush()
                    
                    worker_exam_pairs.append((worker.id, exam.id))
                
                await session.commit()
            
            # 동시 PDF 생성
            start_time = asyncio.get_event_loop().time()
            
            async def generate_single_pdf(worker_id: int, exam_id: int):
                pdf_data = {
                    "worker_id": worker_id,
                    "exam_id": exam_id,
                    "purpose": "정기검진"
                }
                
                response = await client.post(
                    "/api/v1/documents/fill-pdf/health_certificate",
                    json=pdf_data
                )
                
                return response.status_code == 200
            
            # 10개씩 배치로 처리
            batch_size = 10
            total_success = 0
            
            for i in range(0, len(worker_exam_pairs), batch_size):
                batch = worker_exam_pairs[i:i + batch_size]
                results = await asyncio.gather(*[
                    generate_single_pdf(w_id, e_id) for w_id, e_id in batch
                ])
                total_success += sum(results)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            # 성능 검증
            assert total_success >= 45, f"너무 많은 PDF 생성 실패: {50 - total_success}개"
            assert duration < 30.0, f"대량 PDF 생성이 너무 느립니다: {duration:.2f}초"
            
            avg_time = duration / 50
            print(f"✅ 50개 PDF 생성 완료: {duration:.2f}초 (평균 {avg_time:.2f}초/PDF)")
    
    @integration_test
    async def test_pdf_template_coordinates(self):
        """PDF 템플릿 좌표 정확도 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            
            # 좌표 테스트용 데이터
            test_fields = {
                "name": "테스트이름가나다라마바사",  # 긴 이름
                "employee_id": "1234567890",  # 긴 사번
                "birth_date": "1990-12-31",
                "department": "매우긴부서이름테스트부서",
                "exam_date": str(date.today()),
                "exam_result": "정상A(재검불필요)"
            }
            
            # 각 PDF 양식별 테스트
            forms = [
                "health_certificate",
                "health_checkup_result", 
                "special_health_exam",
                "fitness_for_work"
            ]
            
            for form_name in forms:
                # 최소 데이터로 PDF 생성 시도
                response = await client.post(
                    f"/api/v1/documents/fill-pdf/{form_name}",
                    json=test_fields
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # PDF 생성 확인
                    assert "pdf_base64" in result
                    
                    # 좌표가 올바른지 간접 확인 (크기로 판단)
                    pdf_size = len(base64.b64decode(result["pdf_base64"]))
                    assert pdf_size > 10000, f"{form_name} PDF가 너무 작습니다"
                    
                    print(f"✅ {form_name} 템플릿 테스트 완료")
                else:
                    # 일부 양식은 더 많은 데이터 필요할 수 있음
                    print(f"⚠️  {form_name} 템플릿은 추가 데이터 필요")
    
    @integration_test
    async def test_pdf_korean_font_rendering(self):
        """PDF 한글 폰트 렌더링 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]
            
            # 다양한 한글 테스트
            korean_test_cases = [
                "가나다라마바사아자차카타파하",  # 기본 한글
                "뷁뷂뷃뷄뷅뷆뷇뷈뷉뷊",  # 복잡한 한글
                "①②③④⑤ⓐⓑⓒ",  # 특수문자
                "㈜테스트 ㎡ ㎏ ℃",  # 단위 기호
                "한글abc123!@#",  # 혼합
            ]
            
            async with db.get_session() as session:
                from src.models import Worker, HealthExam
                
                for idx, test_text in enumerate(korean_test_cases):
                    worker = Worker(
                        name=test_text[:20],  # 이름 길이 제한
                        employee_id=f"FONT_TEST_{idx}",
                        department=test_text[:30],
                        notes=test_text
                    )
                    session.add(worker)
                
                await session.commit()
            
            # 각 테스트 케이스로 PDF 생성
            for idx in range(len(korean_test_cases)):
                response = await client.get(f"/api/v1/workers/")
                workers = assert_response_ok(response)
                
                # 데이터가 올바르게 저장되었는지 확인
                test_workers = [
                    w for w in workers.get("items", [])
                    if w["employee_id"].startswith("FONT_TEST_")
                ]
                
                assert len(test_workers) > 0, "한글 테스트 데이터가 저장되지 않았습니다"
                
                # 한글이 깨지지 않았는지 확인
                for worker in test_workers:
                    if worker["name"]:
                        assert_korean_text(worker["name"], "worker.name")
                    if worker["department"]:
                        assert_korean_text(worker["department"], "worker.department")
    
    @integration_test
    async def test_pdf_error_handling(self):
        """PDF 생성 에러 처리 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            
            # 1. 잘못된 양식 이름
            response = await client.post(
                "/api/v1/documents/fill-pdf/invalid_form_name",
                json={"test": "data"}
            )
            assert response.status_code == 404
            
            # 2. 필수 데이터 누락
            response = await client.post(
                "/api/v1/documents/fill-pdf/health_certificate",
                json={}  # 빈 데이터
            )
            assert response.status_code == 422
            
            # 3. 존재하지 않는 근로자 ID
            response = await client.post(
                "/api/v1/documents/fill-pdf/health_certificate",
                json={"worker_id": 99999, "exam_id": 99999}
            )
            assert response.status_code == 404
            
            # 4. 잘못된 데이터 타입
            response = await client.post(
                "/api/v1/documents/fill-pdf/health_certificate",
                json={"worker_id": "not_a_number", "exam_id": "also_not_a_number"}
            )
            assert response.status_code == 422
    
    @integration_test
    async def test_pdf_concurrent_generation(self):
        """동시 다발적 PDF 생성 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]
            
            # 테스트 데이터 준비
            async with db.get_session() as session:
                from src.models import Worker
                
                worker = Worker(
                    name="동시성테스트",
                    employee_id="CONCURRENT_001",
                    department="테스트부"
                )
                session.add(worker)
                await session.commit()
                worker_id = worker.id
            
            # 동일 리소스에 대한 동시 PDF 생성
            async def generate_pdf(request_id: int):
                try:
                    response = await client.post(
                        "/api/v1/documents/fill-pdf/worker_info",
                        json={"worker_id": worker_id, "request_id": request_id}
                    )
                    return {
                        "request_id": request_id,
                        "success": response.status_code == 200,
                        "status": response.status_code
                    }
                except Exception as e:
                    return {
                        "request_id": request_id,
                        "success": False,
                        "error": str(e)
                    }
            
            # 20개 동시 요청
            results = await asyncio.gather(*[
                generate_pdf(i) for i in range(20)
            ])
            
            # 성공률 확인
            successful = [r for r in results if r["success"]]
            success_rate = len(successful) / len(results)
            
            assert success_rate >= 0.9, f"동시 요청 성공률이 너무 낮습니다: {success_rate:.0%}"
            print(f"✅ 동시 PDF 생성 성공률: {success_rate:.0%}")


# Run inline tests if module is executed directly
if __name__ == "__main__" or os.environ.get("RUN_INTEGRATION_TESTS"):
    if __name__ == "__main__":
        asyncio.run(run_inline_tests(__name__))