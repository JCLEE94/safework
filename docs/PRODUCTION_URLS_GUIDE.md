# SafeWork Pro 운영 환경 접속 URL 가이드

## 🌐 메인 접속 URL
**운영 URL**: https://safework.jclee.me

## 📱 QR 코드 등록 시스템 URL

### 1. 근로자용 QR 등록 페이지 (모바일 최적화)
```
https://safework.jclee.me/qr-register/{token}
```

**실제 사용 예시:**
- QR 스캔 후 자동 이동: `https://safework.jclee.me/qr-register/abc123def456`
- 토큰은 관리자가 생성한 고유값

### 2. 관리자 로그인
```
https://safework.jclee.me/
```
- 로그인 화면 자동 표시
- 인증 후 대시보드 접근

## 🔧 API 엔드포인트 URL (safework.jclee.me 기준)

### QR 시스템 API
```bash
# 1. 토큰 검증 (무인증 - 근로자용)
https://safework.jclee.me/api/v1/qr-registration/validate/{token}

# 2. 등록 완료 (무인증 - 근로자용)  
https://safework.jclee.me/api/v1/qr-registration/complete

# 3. QR 생성 (관리자용 - JWT 필요)
https://safework.jclee.me/api/v1/qr-registration/generate

# 4. 등록 상태 확인 (관리자용)
https://safework.jclee.me/api/v1/qr-registration/status/{token}

# 5. 대기 목록 조회 (관리자용)
https://safework.jclee.me/api/v1/qr-registration/pending

# 6. 통계 조회 (관리자용)
https://safework.jclee.me/api/v1/qr-registration/statistics

# 7. 등록 취소 (관리자용)
https://safework.jclee.me/api/v1/qr-registration/token/{token}
```

### 심혈관계 관리 API
```bash
# 위험도 계산
https://safework.jclee.me/api/v1/cardiovascular/risk-calculation

# 평가 관리
https://safework.jclee.me/api/v1/cardiovascular/assessments/

# 모니터링
https://safework.jclee.me/api/v1/cardiovascular/monitoring/

# 응급상황
https://safework.jclee.me/api/v1/cardiovascular/emergency/

# 교육
https://safework.jclee.me/api/v1/cardiovascular/education/

# 통계
https://safework.jclee.me/api/v1/cardiovascular/statistics
```

## 📋 시스템 상태 확인 URL

### 헬스체크
```
https://safework.jclee.me/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "service": "건설업 보건관리 시스템",
  "version": "1.0.1",
  "components": {
    "database": "connected",
    "api": "running",
    "frontend": "active"
  }
}
```

### API 문서
```
# Swagger UI
https://safework.jclee.me/api/docs

# ReDoc
https://safework.jclee.me/api/redoc

# OpenAPI JSON
https://safework.jclee.me/openapi.json
```

## 🔐 인증 관련 URL

### 로그인
```bash
POST https://safework.jclee.me/api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

### 로그아웃
```bash
POST https://safework.jclee.me/api/v1/auth/logout
Authorization: Bearer {JWT_TOKEN}
```

## 📲 모바일 QR 사용 시나리오

### 1. QR 코드 생성 (관리자)
```bash
curl -X POST https://safework.jclee.me/api/v1/qr-registration/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_data": {
      "name": "홍길동",
      "phone": "010-1234-5678"
    },
    "department": "건설팀",
    "position": "작업자",
    "expires_in_hours": 24
  }'
```

### 2. QR 코드 스캔 (근로자)
- 스마트폰 카메라로 QR 코드 스캔
- 자동 리다이렉트: `https://safework.jclee.me/qr-register/TOKEN`
- 등록 폼 자동 표시

### 3. 등록 완료
- 폼 작성 후 제출
- 완료 메시지 표시
- 관리자 대시보드에 실시간 반영

## 🎯 주요 페이지 직접 접속 URL

### 관리자 대시보드
```
https://safework.jclee.me/
(로그인 필요)
```

### QR 등록 관리
```
https://safework.jclee.me/#qr-registration
(로그인 필요)
```

### 심혈관계 관리
```
https://safework.jclee.me/#cardiovascular
(로그인 필요)
```

### 근로자 관리
```
https://safework.jclee.me/#workers
(로그인 필요)
```

## 🧪 테스트용 URL

### 개발 환경 (로컬)
```
http://localhost:3001/
http://localhost:3001/api/docs
http://localhost:3001/health
```

### 운영 환경 테스트
```bash
# 헬스체크
curl https://safework.jclee.me/health

# QR 토큰 검증 (테스트)
curl https://safework.jclee.me/api/v1/qr-registration/validate/test123

# API 엔드포인트 목록
curl https://safework.jclee.me/openapi.json | jq '.paths | keys[]'
```

## 📱 모바일 브라우저 호환성

### 권장 브라우저
- **iOS**: Safari 14+, Chrome 90+
- **Android**: Chrome 90+, Samsung Internet 15+

### 지원 기능
- ✅ 반응형 디자인
- ✅ 터치 최적화
- ✅ QR 코드 스캔
- ✅ 폼 자동완성
- ✅ 오프라인 캐싱 (PWA)

## 🚨 긴급 접속 정보

### 시스템 관리자 접속
```
SSH: ssh deploy@safework.jclee.me
컨테이너: docker exec -it safework bash
로그 확인: docker logs safework --tail=100
```

### 모니터링 대시보드
```
https://safework.jclee.me/monitoring
(별도 인증 필요)
```

## 📞 지원 연락처

### 기술 지원
- **이메일**: support@jclee.me
- **전화**: 02-XXXX-XXXX
- **근무시간**: 평일 09:00-18:00

### 긴급 지원
- **24시간 핫라인**: 010-XXXX-XXXX
- **시스템 장애**: alert@jclee.me

---

**업데이트**: 2025-01-18  
**버전**: 1.0.1  
**상태**: 운영 중 ✅  
**URL**: https://safework.jclee.me