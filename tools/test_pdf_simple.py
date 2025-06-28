#!/usr/bin/env python3
"""
Simple PDF functionality test without external dependencies
"""

import sys
import io
from pathlib import Path

# Add src to path
sys.path.append('src')

try:
    from config.pdf_forms import PDF_FORM_COORDINATES
    from handlers.documents import create_text_overlay
    
    def test_pdf_coordinates():
        """Test PDF form coordinates completeness"""
        print("🔍 Testing PDF form coordinates...")
        
        required_forms = [
            "유소견자_관리대장",
            "MSDS_관리대장", 
            "건강관리_상담방문_일지",
            "특별관리물질_취급일지"
        ]
        
        for form_id in required_forms:
            if form_id not in PDF_FORM_COORDINATES:
                print(f"❌ Missing form coordinates: {form_id}")
                return False
            
            form_config = PDF_FORM_COORDINATES[form_id]
            if "fields" not in form_config:
                print(f"❌ Missing fields in {form_id}")
                return False
            
            if len(form_config["fields"]) == 0:
                print(f"❌ No fields defined for {form_id}")
                return False
            
            print(f"✅ {form_id}: {len(form_config['fields'])} fields defined")
        
        return True
    
    def test_text_overlay():
        """Test text overlay creation"""
        print("🔍 Testing text overlay creation...")
        
        test_data = {
            "company_name": "테스트 건설회사",
            "department": "안전관리팀",
            "worker_name": "홍길동",
            "employee_id": "EMP001",
            "exam_date": "2024-01-15",
            "exam_result": "정상"
        }
        
        form_type = "유소견자_관리대장"
        
        try:
            overlay = create_text_overlay(test_data, form_type)
            if isinstance(overlay, io.BytesIO) and overlay.tell() > 0:
                print("✅ Text overlay created successfully")
                return True
            else:
                print("❌ Text overlay creation failed - empty result")
                return False
        except Exception as e:
            print(f"❌ Text overlay creation failed: {str(e)}")
            return False
    
    def test_korean_text():
        """Test Korean text handling"""
        print("🔍 Testing Korean text handling...")
        
        korean_data = {
            "company_name": "한국건설주식회사",
            "department": "안전보건관리부",
            "worker_name": "김철수",
            "exam_result": "요관찰자 - 추적검사 필요"
        }
        
        form_type = "유소견자_관리대장"
        
        try:
            overlay = create_text_overlay(korean_data, form_type)
            if overlay.tell() > 0:
                print("✅ Korean text handling successful")
                return True
            else:
                print("❌ Korean text handling failed")
                return False
        except Exception as e:
            print(f"❌ Korean text handling failed: {str(e)}")
            return False
    
    def test_coordinate_validation():
        """Test coordinate validation"""
        print("🔍 Testing coordinate validation...")
        
        A4_WIDTH = 595.27
        A4_HEIGHT = 841.89
        
        issues = []
        
        for form_id, form_config in PDF_FORM_COORDINATES.items():
            for field_name, field_info in form_config["fields"].items():
                x = field_info.get("x", 0)
                y = field_info.get("y", 0)
                
                if not (0 <= x <= A4_WIDTH):
                    issues.append(f"{form_id}.{field_name}: Invalid x coordinate {x}")
                
                if not (0 <= y <= A4_HEIGHT):
                    issues.append(f"{form_id}.{field_name}: Invalid y coordinate {y}")
        
        if issues:
            print("❌ Coordinate validation issues:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"   {issue}")
            return False
        else:
            print("✅ All coordinates are valid")
            return True
    
    def test_form_structure():
        """Test form structure completeness"""
        print("🔍 Testing form structure...")
        
        total_fields = 0
        for form_id, form_config in PDF_FORM_COORDINATES.items():
            field_count = len(form_config.get("fields", {}))
            total_fields += field_count
            print(f"   {form_id}: {field_count} fields")
        
        print(f"✅ Total {total_fields} fields across all forms")
        return True
    
    def run_all_tests():
        """Run all tests"""
        print("🚀 Starting PDF functionality tests...\n")
        
        tests = [
            ("PDF Coordinates", test_pdf_coordinates),
            ("Text Overlay", test_text_overlay), 
            ("Korean Text", test_korean_text),
            ("Coordinate Validation", test_coordinate_validation),
            ("Form Structure", test_form_structure)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
        
        print(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("💥 Some tests failed!")
            return False
    
    if __name__ == "__main__":
        success = run_all_tests()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)