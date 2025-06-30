#!/usr/bin/env python3
import os
import urllib.parse
import requests

def test_pdf_api():
    # URL 인코딩
    form_id = urllib.parse.quote('MSDS_관리대장', safe='')
    base_url = os.getenv('PRODUCTION_URL', 'http://soonmin.jclee.me')
    url = f'{base_url}/api/v1/documents/fill-pdf/{form_id}'
    print(f'URL: {url}')

    # 테스트 데이터
    data = {
        'chemical_name': '수정된톨루엔',
        'manufacturer': '새로운제조사',
        'cas_number': '108-88-3-FIX',
        'usage': '테스트용도'
    }

    try:
        response = requests.post(url, 
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        print(f'Status: {response.status_code}')
        print(f'Headers: {dict(response.headers)}')
        
        if response.status_code != 200:
            print(f'Error: {response.text}')
        else:
            print(f'Success: PDF size {len(response.content)} bytes')
            with open('/tmp/msds_encoded_test.pdf', 'wb') as f:
                f.write(response.content)
            print('PDF saved to /tmp/msds_encoded_test.pdf')
            
    except Exception as e:
        print(f'Request failed: {str(e)}')

if __name__ == '__main__':
    test_pdf_api()