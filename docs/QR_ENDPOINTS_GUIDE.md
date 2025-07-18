# SafeWork Pro QR 코드 시스템 사용 가이드

## 📱 사용자용 QR 엔드포인트

### 1. QR 코드 스캔 후 등록 페이지
```
https://safework.jclee.me/qr-register/{token}
```

**사용법:**
1. 관리자가 생성한 QR 코드를 스캔
2. 자동으로 등록 페이지로 이동
3. 개인정보 입력 후 등록 완료

**예시 URL:**
```
https://safework.jclee.me/qr-register/abc123def456
```

### 2. 토큰 검증 API (개발자용)
```
GET /api/v1/qr-registration/validate/{token}
```

**응답 예시:**
```json
{
  "valid": true,
  "token_info": {
    "id": "uuid-here",
    "department": "건설팀",
    "position": "작업자",
    "worker_data": {
      "name": "홍길동",
      "phone": "010-1234-5678"
    },
    "expires_at": "2025-01-20T12:00:00",
    "status": "pending"
  }
}
```

### 3. 등록 완료 API
```
POST /api/v1/qr-registration/complete
```

**요청 본문:**
```json
{
  "token": "abc123def456",
  "worker_data": {
    "name": "홍길동",
    "phone": "010-1234-5678",
    "email": "hong@example.com",
    "birth_date": "1990-01-01",
    "gender": "male",
    "address": "서울시 강남구",
    "emergency_contact": "010-9876-5432",
    "emergency_relationship": "spouse",
    "work_type": "construction",
    "employment_type": "regular",
    "hire_date": "2025-01-18",
    "health_status": "normal"
  }
}
```

## 🔧 관리자용 QR 생성 API

### 1. QR 코드 생성
```
POST /api/v1/qr-registration/generate
```

**요청 본문:**
```json
{
  "worker_data": {
    "name": "홍길동",
    "phone": "010-1234-5678"
  },
  "department": "건설팀",
  "position": "작업자",
  "expires_in_hours": 24
}
```

**응답:**
```json
{
  "token": "abc123def456",
  "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "registration_url": "https://safework.jclee.me/qr-register/abc123def456",
  "expires_at": "2025-01-19T18:00:00",
  "status": "pending"
}
```

### 2. 등록 상태 확인
```
GET /api/v1/qr-registration/status/{token}
```

## 🌟 실제 사용 시나리오

### 시나리오 1: 신규 근로자 등록
1. **관리자**: QR 코드 생성 API 호출
   ```bash
   curl -X POST https://safework.jclee.me/api/v1/qr-registration/generate \
   -H "Content-Type: application/json" \
   -H "Authorization: Bearer YOUR_TOKEN" \
   -d '{
     "worker_data": {"name": "김철수", "phone": "010-1111-2222"},
     "department": "전기팀",
     "position": "기술자",
     "expires_in_hours": 48
   }'
   ```

2. **관리자**: 생성된 QR 코드를 근로자에게 제공

3. **근로자**: 스마트폰으로 QR 코드 스캔
   - 자동으로 `https://safework.jclee.me/qr-register/TOKEN` 페이지 열림

4. **근로자**: 등록 폼 작성 및 제출
   - 이름, 연락처, 생년월일, 성별 등 입력
   - "등록 완료" 버튼 클릭

5. **시스템**: 근로자 정보 데이터베이스에 저장 완료

### 시나리오 2: 대량 등록
1. **관리자**: 여러 QR 코드 한번에 생성
2. **인쇄**: QR 코드를 배지나 스티커로 제작
3. **배포**: 근로자들에게 개별 QR 코드 제공
4. **등록**: 각자 편한 시간에 스캔하여 등록

## 📱 모바일 최적화

### 지원 기능
- ✅ 반응형 디자인 (모바일, 태블릭, PC)
- ✅ 터치 친화적 인터페이스
- ✅ 자동완성 및 입력 검증
- ✅ 진행 상황 표시
- ✅ 오류 메시지 및 안내

### 권장 사양
- **iOS**: Safari 14+ 또는 Chrome 90+
- **Android**: Chrome 90+ 또는 Samsung Internet 15+
- **인터넷 연결**: 4G/WiFi 권장

## 🔒 보안 및 유효성

### 토큰 보안
- **만료 시간**: 기본 24시간 (최대 168시간)
- **일회성**: 등록 완료 후 토큰 비활성화
- **검증**: 매 요청시 토큰 유효성 확인

### 데이터 보호
- **HTTPS**: 모든 통신 암호화
- **개인정보**: 최소 필요 정보만 수집
- **동의**: 개인정보 처리 동의 확인

## 🎯 실제 테스트용 URL

### 개발/테스트 환경
```
http://localhost:3001/qr-register/{token}
```

### 운영 환경 (배포 후)
```
https://safework.jclee.me/qr-register/{token}
```

## 📞 지원 및 문의

문제 발생 시 연락처:
- **기술지원**: IT팀 내선 1234
- **시스템 관리**: 안전관리팀 내선 5678
- **긴급상황**: 대표번호 02-0000-0000

---

**업데이트**: 2025-01-18  
**버전**: 1.0.0  
**문서 관리**: SafeWork Pro Development Team