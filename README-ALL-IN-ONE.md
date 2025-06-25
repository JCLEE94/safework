# SafeWork Pro - All-in-One Container

## 개요
SafeWork Pro를 단일 컨테이너로 실행하는 통합 솔루션입니다.
PostgreSQL, Redis, Python Backend, React Frontend가 모두 하나의 컨테이너에 포함됩니다.

## 장점
- **간편한 배포**: 단일 컨테이너로 전체 시스템 실행
- **리소스 효율성**: 하나의 컨테이너로 모든 서비스 관리
- **포트 단순화**: 3001 포트만 사용
- **볼륨 관리 용이**: Docker 볼륨으로 데이터 영속성 보장

## 빠른 시작

### 1. 환경 변수 설정
```bash
cp .env.all-in-one.example .env.all-in-one
# 필요시 .env.all-in-one 파일 편집
```

### 2. 배포 실행
```bash
# 기본 배포
./deploy-all-in-one.sh

# 기존 데이터 백업 후 배포
./deploy-all-in-one.sh --backup-volumes
```

### 3. 접속
- 웹 애플리케이션: http://localhost:3001
- 헬스체크: http://localhost:3001/health
- API 문서: http://localhost:3001/api/docs

## Docker Compose 명령어

### 시작/중지
```bash
# 시작
docker-compose -f docker-compose.all-in-one.yml up -d

# 중지
docker-compose -f docker-compose.all-in-one.yml down

# 재시작
docker-compose -f docker-compose.all-in-one.yml restart
```

### 로그 확인
```bash
# 전체 로그
docker-compose -f docker-compose.all-in-one.yml logs -f

# 최근 100줄
docker-compose -f docker-compose.all-in-one.yml logs --tail=100
```

### 컨테이너 접속
```bash
# Bash 쉘 접속
docker exec -it safework-pro-all-in-one bash

# PostgreSQL 접속
docker exec -it safework-pro-all-in-one psql -U admin -d health_management

# Redis CLI 접속
docker exec -it safework-pro-all-in-one redis-cli
```

## 볼륨 관리

### 볼륨 구조
- `postgres_data`: PostgreSQL 데이터
- `app_uploads`: 업로드된 파일
- `app_logs`: 애플리케이션 로그
- `redis_data`: Redis 데이터

### 볼륨 명령어
```bash
# 볼륨 목록
docker volume ls | grep safework

# 볼륨 정보
docker volume inspect safework-pro_postgres_data

# 볼륨 백업
docker run --rm -v safework-pro_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# 볼륨 복원
docker run --rm -v safework-pro_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

## 문제 해결

### 포트 충돌
```bash
# 3001 포트 사용 프로세스 확인
lsof -i :3001

# docker-compose.all-in-one.yml에서 포트 변경
ports:
  - "3002:3001"  # 3002로 변경
```

### 메모리 부족
```bash
# Docker 리소스 확인
docker system df

# 불필요한 이미지/컨테이너 정리
docker system prune -a
```

### 서비스 시작 실패
```bash
# 상세 로그 확인
docker-compose -f docker-compose.all-in-one.yml logs safework-pro

# 컨테이너 내부 프로세스 확인
docker exec -it safework-pro-all-in-one ps aux
```

## 프로덕션 배포

### 1. 환경 변수 설정
```bash
# .env.all-in-one 파일에서 프로덕션 값으로 변경
POSTGRES_PASSWORD=강력한_비밀번호
JWT_SECRET=프로덕션_시크릿_키
DEBUG=false
```

### 2. 이미지 빌드 및 푸시
```bash
# 이미지 빌드
docker-compose -f docker-compose.all-in-one.yml build

# 태그 지정
docker tag safework-pro-aio:latest registry.jclee.me/safework-pro-aio:latest

# 레지스트리 푸시
docker push registry.jclee.me/safework-pro-aio:latest
```

### 3. 원격 서버 배포
```bash
# 원격 서버에서
docker pull registry.jclee.me/safework-pro-aio:latest
docker-compose -f docker-compose.all-in-one.yml up -d
```

## 모니터링

### 헬스체크
```bash
# 로컬
curl http://localhost:3001/health

# 원격
curl http://your-server:3001/health
```

### 리소스 사용량
```bash
# CPU/메모리 사용량
docker stats safework-pro-all-in-one

# 디스크 사용량
docker exec safework-pro-all-in-one df -h
```

## 보안 고려사항

1. **비밀번호 변경**: 기본 비밀번호를 반드시 변경
2. **방화벽 설정**: 3001 포트 접근 제한
3. **HTTPS 설정**: 프로덕션에서는 리버스 프록시 사용
4. **백업 정책**: 정기적인 볼륨 백업 수행

## 라이선스
SafeWork Pro는 상용 라이선스입니다.