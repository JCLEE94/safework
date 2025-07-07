#!/usr/bin/env python3
"""
하드코딩 제거 스크립트
Remove hardcoded values from handlers
"""

import os
import re
from pathlib import Path

def fix_handler_file(file_path):
    """핸들러 파일의 하드코딩 수정"""
    print(f"Processing {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Import 추가 (아직 없는 경우)
    if 'from src.utils.auth_deps import get_current_user_id' not in content:
        # 마지막 import 문 다음에 추가
        import_pattern = r'(from src\.schemas\.[^)]+\))'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r'\1\nfrom src.utils.auth_deps import get_current_user_id',
                content
            )
    
    # 2. 함수 시그니처에 current_user_id 파라미터 추가
    # "system" 하드코딩이 있는 함수들 찾기
    functions_with_system = []
    
    system_patterns = [
        r'\.created_by = "system"',
        r'\.updated_by = "system"',
        r'user_id: str = "system"'
    ]
    
    for pattern in system_patterns:
        for match in re.finditer(pattern, content):
            # 해당 라인이 속한 함수 찾기
            lines_before = content[:match.start()].split('\n')
            for i in range(len(lines_before) - 1, -1, -1):
                line = lines_before[i].strip()
                if line.startswith('async def ') or line.startswith('def '):
                    func_name = line.split('(')[0].replace('async def ', '').replace('def ', '')
                    if func_name not in functions_with_system:
                        functions_with_system.append(func_name)
                    break
    
    print(f"Found functions with hardcoded values: {functions_with_system}")
    
    # 3. 함수 시그니처 수정
    for func_name in functions_with_system:
        # 함수 정의 찾기
        func_pattern = rf'(async def {func_name}\([^)]+)(\):\s*\n)'
        
        def replace_func_signature(match):
            params = match.group(1)
            closing = match.group(2)
            
            # 이미 current_user_id가 있는지 확인
            if 'current_user_id' in params:
                return match.group(0)  # 이미 있으면 변경하지 않음
            
            # user_id: str = "system" 패턴을 current_user_id로 교체
            if 'user_id: str = "system"' in params:
                params = params.replace(
                    'user_id: str = "system"',
                    'current_user_id: str = Depends(get_current_user_id)'
                )
            else:
                # 마지막 파라미터 뒤에 추가
                if not params.endswith(','):
                    params += ','
                params += '\n    current_user_id: str = Depends(get_current_user_id)'
            
            return params + closing
        
        content = re.sub(func_pattern, replace_func_signature, content, flags=re.MULTILINE | re.DOTALL)
    
    # 4. 하드코딩된 값들 교체
    replacements = [
        (r'\.created_by = "system"', '.created_by = current_user_id'),
        (r'\.updated_by = "system"', '.updated_by = current_user_id'),
        (r'user_id: str = "system"', 'current_user_id: str = Depends(get_current_user_id)'),
        (r'created_by="system"', 'created_by=current_user_id'),
        (r'updated_by="system"', 'updated_by=current_user_id'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # 5. Depends import 추가
    if 'Depends(get_current_user_id)' in content and 'from fastapi import' in content:
        # Depends가 이미 import되어 있는지 확인
        if 'Depends' not in re.search(r'from fastapi import ([^)]+)', content).group(1):
            content = re.sub(
                r'from fastapi import ([^)]+)',
                lambda m: f"from fastapi import {m.group(1)}, Depends" if not m.group(1).endswith(',') else f"from fastapi import {m.group(1)} Depends",
                content
            )
    
    # 변경사항이 있는 경우에만 저장
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")
        return True
    else:
        print(f"🔵 No changes needed for {file_path}")
        return False

def main():
    """메인 실행 함수"""
    handlers_dir = Path('src/handlers')
    updated_files = []
    
    for py_file in handlers_dir.glob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        if fix_handler_file(py_file):
            updated_files.append(str(py_file))
    
    print(f"\n✅ Completed! Updated {len(updated_files)} files:")
    for file in updated_files:
        print(f"  - {file}")
    
    if not updated_files:
        print("🎉 All files are already up to date!")

if __name__ == '__main__':
    main()