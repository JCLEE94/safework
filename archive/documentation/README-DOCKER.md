# Docker Compose 구성

## 파일 설명

### docker-compose.yml (기본 프로덕션용)
- 프로덕션 환경에서 사용하는 기본 구성
- PostgreSQL, Redis, Health App 포함
- registry.jclee.me에서 이미지 pull
- Watchtower 라벨로 자동 업데이트 지원

### docker-compose.dev.yml (개발용)
- 로컬 개발 환경용 구성
- 소스 코드 마운트로 hot-reload 지원
- 디버그 모드 활성화
- 로컬 빌드 사용

### docker-compose.prod.yml (원격 프로덕션용)
- 원격 서버(192.168.50.215) 배포용
- 외부 네트워크 사용
- 환경변수 분리
- 볼륨 경로 프로덕션용으로 설정

## 사용 방법

### 개발 환경
```bash
# 개발 환경 시작 (hot-reload 지원)
docker-compose -f docker-compose.dev.yml up --build

# 백그라운드 실행
docker-compose -f docker-compose.dev.yml up -d --build
```

### 프로덕션 환경 (로컬)
```bash
# 프로덕션 이미지로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f health-app
```

### 프로덕션 환경 (원격)
```bash
# 원격 서버에서 실행
docker-compose -f docker-compose.prod.yml up -d

# 업데이트 (Watchtower가 자동으로 처리)
# 수동 업데이트가 필요한 경우
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 환경 변수

`.env` 파일 생성:
```bash
cp .env.example .env
# 필요한 값 수정
```

## 네트워크

- **health-network**: 로컬 개발/테스트용 내부 네트워크
- **health-network-dev**: 개발 환경 전용 네트워크
- **health-network** (external): 프로덕션 서버의 기존 네트워크 사용

## 볼륨

- **postgres_data**: PostgreSQL 데이터 영구 저장
- **redis_data**: Redis 데이터 영구 저장
- **uploads**: 업로드 파일 저장
- **logs**: 애플리케이션 로그 저장

## 헬스체크

모든 서비스는 헬스체크 설정됨:
- PostgreSQL: pg_isready 명령
- Redis: redis-cli ping
- Health App: /health 엔드포인트

## Watchtower 자동 배포

프로덕션 환경에서는 Watchtower가 30초마다 새 이미지를 확인하고 자동 배포합니다.

라벨 설정:
```yaml
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```