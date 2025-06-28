# SafeWork Pro 배포 가이드

## 🚀 빠른 시작

### 운영 환경 (단일 컨테이너)
```bash
# 1. 환경 설정
cp config/env.production.example .env

# 2. 배포 실행
docker-compose up -d

# 3. 상태 확인
curl http://localhost:3001/health
```

### 개발 환경 (분리된 서비스)
```bash
# 1. 환경 설정
cp config/env.development.example .env

# 2. 개발 환경 실행 (docker-compose.override.yml 자동 적용)
docker-compose up -d

# 3. 개발 서버 확인
curl http://localhost:3001/health
```

## 📁 정리된 파일 구조

### 사용 중인 파일들
```
├── docker-compose.yml           # 메인 설정 (환경변수로 운영/개발 구분)
├── docker-compose.dev.yml       # 개발 환경 (별도 사용 시)
├── docker-compose.override.yml  # 개발 환경 오버라이드 (자동 적용)
├── deploy-single.sh            # 현재 사용 중인 배포 스크립트
├── Dockerfile.prod             # 운영용 Dockerfile
├── Dockerfile                  # 기본 Dockerfile
└── config/
    ├── env.production.example  # 운영 환경 설정 예제
    └── env.development.example # 개발 환경 설정 예제
```

### 정리된 파일들 (archive/)
```
archive/
├── docker-compose/            # 사용하지 않는 docker-compose 파일들
├── deploy-scripts/            # 사용하지 않는 배포 스크립트들
├── documentation/             # 이전 README 파일들
├── dockerfiles/              # 사용하지 않는 Dockerfile들
├── configs/                  # 사용하지 않는 설정 파일들
└── docker/                   # 전체 docker 디렉터리
```

## 🔧 환경 설정

### 환경변수 우선순위
1. 명령행 환경변수
2. .env 파일
3. docker-compose.yml의 기본값

### 주요 환경변수
- `ENVIRONMENT`: production/development/test
- `DEBUG`: true/false
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR
- `DATABASE_URL`: 데이터베이스 연결 URL
- `REDIS_URL`: Redis 연결 URL
- `JWT_SECRET`: JWT 토큰 비밀키

## 🐳 Docker Compose 사용법

### 기본 명령어
```bash
# 운영 환경 시작
docker-compose up -d

# 개발 환경 시작 (override 파일 자동 적용)
ENVIRONMENT=development docker-compose up -d

# 특정 compose 파일 사용
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose logs -f safework

# 서비스 중지
docker-compose down

# 볼륨까지 삭제
docker-compose down -v
```

### 환경별 설정
```bash
# 운영 환경
ENVIRONMENT=production docker-compose up -d

# 개발 환경
ENVIRONMENT=development docker-compose up -d

# 테스트 환경
ENVIRONMENT=test docker-compose up -d
```

## 📦 배포 방법

### 자동 배포 (CI/CD)
GitHub Actions를 통해 자동으로 배포됩니다:
1. `git push origin main`
2. GitHub Actions 빌드
3. registry.jclee.me에 이미지 푸시
4. Watchtower가 자동으로 업데이트

### 수동 배포
```bash
# 현재 사용 중인 배포 스크립트
./deploy-single.sh
```

## 🔍 트러블슈팅

### 일반적인 문제들
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs safework

# 데이터베이스 연결 확인
docker-compose exec safework psql -U admin -d health_management -c "SELECT 1"

# Redis 연결 확인
docker-compose exec safework redis-cli ping

# 헬스체크 확인
curl http://localhost:3001/health
```

### 개발 환경 문제
```bash
# 개발 환경 재시작
docker-compose down && docker-compose up -d

# 볼륨 초기화
docker-compose down -v && docker-compose up -d

# 캐시 클리어 후 빌드
docker-compose build --no-cache
```

## 📚 참고 문서

- `archive/documentation/`: 이전 문서들
- `scripts/deploy/`: 추가 배포 스크립트들
- `.github/workflows/`: CI/CD 설정 파일들