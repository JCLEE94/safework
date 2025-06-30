#!/usr/bin/env python3
"""
웹 API를 통한 샘플 데이터 추가 스크립트
Add sample data via web API
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = os.getenv("PRODUCTION_URL", "http://192.168.50.215:3001") + "/api/v1"

import os

def add_sample_workers():
    """근로자 샘플 데이터 추가"""
    workers = [
        {
            "name": "김철수",
            "employee_id": "EMP001",
            "gender": "male", 
            "department": "건설팀",
            "position": "주임",
            "employment_type": "regular",
            "work_type": "construction",
            "hire_date": "2025-01-01",
            "birth_date": "1990-01-15",
            "phone": "010-1234-9999",
            "health_status": "normal"
        },
        {
            "name": "이영희",
            "employee_id": "EMP002", 
            "gender": "female",
            "department": "전기팀",
            "position": "기사",
            "employment_type": "regular",
            "work_type": "electrical",
            "hire_date": "2024-12-01",
            "birth_date": "1985-05-20",
            "phone": "010-2345-8888",
            "health_status": "normal"
        },
        {
            "name": "박민수",
            "employee_id": "EMP003",
            "gender": "male",
            "department": "배관팀", 
            "position": "반장",
            "employment_type": "contract",
            "work_type": "plumbing",
            "hire_date": "2024-11-15",
            "birth_date": "1988-08-10",
            "phone": "010-3456-7777",
            "health_status": "caution"
        }
    ]
    
    for worker in workers:
        try:
            response = requests.post(f"{API_BASE}/workers/", json=worker)
            if response.status_code == 201:
                print(f"✅ 근로자 추가 성공: {worker['name']}")
            else:
                print(f"❌ 근로자 추가 실패: {worker['name']} - {response.text}")
        except Exception as e:
            print(f"❌ 요청 오류: {e}")

def add_sample_chemical_substances():
    """화학물질 샘플 데이터 추가"""
    chemicals = [
        {
            "substance_name": "톨루엔",
            "cas_number": "108-88-3",
            "category": "organic_solvent",
            "hazard_classification": "인화성액체",
            "exposure_limit_twa": 50.0,
            "exposure_limit_stel": 150.0,
            "unit": "ppm",
            "health_effects": "중추신경계 억제, 피부염",
            "safety_measures": "환기설비 가동, 보호장비 착용",
            "storage_conditions": "서늘하고 건조한 곳",
            "usage_location": "도장작업장",
            "supplier": "한국화학",
            "status": "active"
        },
        {
            "substance_name": "아세톤", 
            "cas_number": "67-64-1",
            "category": "organic_solvent",
            "hazard_classification": "인화성액체",
            "exposure_limit_twa": 250.0,
            "exposure_limit_stel": 500.0,
            "unit": "ppm",
            "health_effects": "점막 자극, 중추신경계 억제",
            "safety_measures": "환기, 화기 금지",
            "storage_conditions": "밀폐된 서늘한 곳",
            "usage_location": "청소작업장",
            "supplier": "대한화학",
            "status": "active"
        }
    ]
    
    for chemical in chemicals:
        try:
            response = requests.post(f"{API_BASE}/chemical-substances/", json=chemical)
            if response.status_code == 201:
                print(f"✅ 화학물질 추가 성공: {chemical['substance_name']}")
            else:
                print(f"❌ 화학물질 추가 실패: {chemical['substance_name']} - {response.text}")
        except Exception as e:
            print(f"❌ 요청 오류: {e}")

def add_sample_work_environments():
    """작업환경 샘플 데이터 추가"""
    environments = [
        {
            "measurement_date": datetime.now().strftime("%Y-%m-%d"),
            "location": "1층 작업장",
            "measurement_type": "noise",
            "measured_value": 85.5,
            "unit": "dB",
            "standard_value": 90.0,
            "status": "normal",
            "measuring_institution": "한국산업안전보건공단",
            "next_measurement_date": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            "remarks": "정상 범위 내"
        },
        {
            "measurement_date": datetime.now().strftime("%Y-%m-%d"),
            "location": "2층 도장장",
            "measurement_type": "chemical",
            "measured_value": 12.5,
            "unit": "ppm",
            "standard_value": 50.0,
            "status": "normal",
            "measuring_institution": "환경보건연구원", 
            "next_measurement_date": (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            "remarks": "톨루엔 농도 측정"
        }
    ]
    
    for env in environments:
        try:
            response = requests.post(f"{API_BASE}/work-environments/", json=env)
            if response.status_code == 201:
                print(f"✅ 작업환경 추가 성공: {env['location']}")
            else:
                print(f"❌ 작업환경 추가 실패: {env['location']} - {response.text}")
        except Exception as e:
            print(f"❌ 요청 오류: {e}")

def add_sample_health_education():
    """보건교육 샘플 데이터 추가"""
    educations = [
        {
            "education_date": datetime.now().strftime("%Y-%m-%d"),
            "education_type": "safety",
            "topic": "건설현장 안전교육",
            "duration_hours": 2,
            "instructor": "김안전",
            "location": "2층 회의실",
            "attendees_count": 25,
            "materials": "안전수칙 매뉴얼",
            "completion_rate": 100.0,
            "effectiveness_score": 4.5,
            "next_education_date": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        },
        {
            "education_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "education_type": "health",
            "topic": "근골격계 질환 예방교육",
            "duration_hours": 1,
            "instructor": "이보건",
            "location": "1층 휴게실",
            "attendees_count": 20,
            "materials": "스트레칭 가이드",
            "completion_rate": 95.0,
            "effectiveness_score": 4.2,
            "next_education_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        }
    ]
    
    for edu in educations:
        try:
            response = requests.post(f"{API_BASE}/health-education/", json=edu)
            if response.status_code == 201:
                print(f"✅ 보건교육 추가 성공: {edu['topic']}")
            else:
                print(f"❌ 보건교육 추가 실패: {edu['topic']} - {response.text}")
        except Exception as e:
            print(f"❌ 요청 오류: {e}")

def add_sample_accident_reports():
    """산업재해 샘플 데이터 추가"""
    # 먼저 근로자 목록을 가져와서 worker_id 확인
    try:
        workers_response = requests.get(f"{API_BASE}/workers/")
        if workers_response.status_code == 200:
            workers = workers_response.json().get("items", [])
            if workers:
                worker_id = workers[0]["id"]
                
                accident = {
                    "report_date": datetime.now().strftime("%Y-%m-%d"),
                    "incident_date": datetime.now().strftime("%Y-%m-%d"),
                    "incident_time": "14:30:00",
                    "location": "3층 작업장",
                    "accident_type": "cut",
                    "severity": "minor",
                    "injured_worker_id": worker_id,
                    "description": "작업 중 날카로운 도구에 의한 경미한 절상",
                    "immediate_cause": "부주의",
                    "root_cause": "안전장비 미착용",
                    "corrective_actions": "안전교육 강화, 보호장비 점검",
                    "reported_by": "현장관리자",
                    "investigation_status": "completed",
                    "lost_time_days": 0,
                    "medical_treatment": "응급처치",
                    "cost_estimate": 50000.0,
                    "prevention_measures": "작업 전 안전점검 의무화"
                }
                
                response = requests.post(f"{API_BASE}/accident-reports/", json=accident)
                if response.status_code == 201:
                    print(f"✅ 산업재해 추가 성공")
                else:
                    print(f"❌ 산업재해 추가 실패: {response.text}")
            else:
                print("❌ 근로자 데이터가 없어 산업재해 추가 불가")
        else:
            print("❌ 근로자 목록 조회 실패")
    except Exception as e:
        print(f"❌ 요청 오류: {e}")

def clear_all_data():
    """모든 데이터 삭제"""
    endpoints = [
        "accident-reports",
        "health-education", 
        "work-environments",
        "chemical-substances",
        "workers"
    ]
    
    for endpoint in endpoints:
        try:
            # GET으로 모든 아이템 조회
            response = requests.get(f"{API_BASE}/{endpoint}/")
            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    # 각 아이템 삭제
                    delete_response = requests.delete(f"{API_BASE}/{endpoint}/{item['id']}")
                    if delete_response.status_code == 200:
                        print(f"✅ {endpoint} 데이터 삭제: {item.get('name', item.get('id'))}")
                    else:
                        print(f"❌ {endpoint} 삭제 실패: {item.get('id')}")
        except Exception as e:
            print(f"❌ {endpoint} 삭제 중 오류: {e}")

def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        print("🗑️ 모든 데이터를 삭제합니다...")
        clear_all_data()
        print("✅ 데이터 삭제 완료!")
    else:
        print("📝 샘플 데이터를 추가합니다...")
        
        print("\n1️⃣ 근로자 데이터 추가...")
        add_sample_workers()
        
        print("\n2️⃣ 화학물질 데이터 추가...")
        add_sample_chemical_substances()
        
        print("\n3️⃣ 작업환경 데이터 추가...")
        add_sample_work_environments()
        
        print("\n4️⃣ 보건교육 데이터 추가...")
        add_sample_health_education()
        
        print("\n5️⃣ 산업재해 데이터 추가...")
        add_sample_accident_reports()
        
        print("\n✅ 모든 샘플 데이터 추가 완료!")
        production_url = os.getenv("PRODUCTION_URL", "http://192.168.50.215:3001")
        print(f"🌐 대시보드 확인: {production_url}")

if __name__ == "__main__":
    main()