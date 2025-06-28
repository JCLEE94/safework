# SafeWork Pro 사용 가이드

## 📁 용도별 파일 정리 완료

SafeWork Pro 프로젝트의 모든 파일을 용도별로 깔끔하게 정리했습니다!

### 🎯 통합된 Docker Compose 설정

이제 **하나의 docker-compose.yml**로 운영과 개발 환경을 모두 관리합니다.

## 🚀 빠른 시작

### 1. 운영 환경 배포
```bash
# 운영 환경 설정 복사
cp config/env.production.example .env

# 운영 환경 실행
docker-compose up -d

# 상태 확인
docker ps
curl http://192.168.50.215:3001/health
```

### 2. 개발 환경 실행
```bash
# 개발 환경 설정 복사
cp config/env.development.example .env

# 개발 환경 실행 
ENVIRONMENT=development docker-compose up -d

# 또는 .env 파일에서 ENVIRONMENT=development로 설정 후
docker-compose up -d
```

## 📊 주요 변경사항

### ✅ 파일 정리
- **이전**: 20개 이상의 docker-compose 파일들이 산재
- **현재**: 1개의 통합된 docker-compose.yml

### ✅ 환경별 설정
```
config/
├── env.production.example   # 운영 환경 설정
└── env.development.example  # 개발 환경 설정
```

### ✅ 아카이브 정리
```
archive/
├── docker-compose/     # 이전 docker-compose 파일들
├── deploy-scripts/     # 사용하지 않는 배포 스크립트들
├── documentation/      # 이전 README 파일들
└── dockerfiles/        # 사용하지 않는 Dockerfile들
```

## ⚙️ 환경 구분 방법

### 환경변수로 제어
```bash
# 운영 환경 (기본값)
ENVIRONMENT=production docker-compose up -d

# 개발 환경
ENVIRONMENT=development docker-compose up -d
```

### 주요 차이점
| 설정 | 운영환경 | 개발환경 |
|------|----------|----------|
| DEBUG | false | true |
| LOG_LEVEL | INFO | DEBUG |
| WORKERS | 4 | 2 |
| WATCHTOWER | 활성화 | 비활성화 |
| CORS | 제한적 | 모든 오리진 허용 |
| UPLOAD_SIZE | 100MB | 200MB |
| RESTART | unless-stopped | no |

## 🔧 설정 파일 구조

### .env 파일 (환경별 설정)
```bash
# 환경 설정
ENVIRONMENT=production|development
DEBUG=false|true

# 컨테이너 설정  
DOCKER_IMAGE=registry.jclee.me/safework:latest
CONTAINER_NAME=safework
HOST_PORT=3001

# 데이터베이스 (All-in-One 내장)
DATABASE_URL=postgresql://admin:password@localhost:5432/health_management

# 보안 설정
JWT_SECRET=your-secret-key
```

## 📋 명령어 레퍼런스

### 기본 명령어
```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps
```

### 환경별 명령어
```bash
# 운영 환경으로 시작
cp config/env.production.example .env
docker-compose up -d

# 개발 환경으로 시작  
cp config/env.development.example .env
docker-compose up -d

# 환경변수로 직접 지정
ENVIRONMENT=development docker-compose up -d
```

### 볼륨 관리
```bash
# 볼륨 확인
docker volume ls | grep safework

# 볼륨 정리 (주의: 데이터 삭제됨)
docker-compose down -v
```

## 🔍 트러블슈팅

### 포트 충돌 시
```bash
# 실행 중인 컨테이너 확인
docker ps | grep 3001

# 충돌하는 컨테이너 중지
docker stop <container_name>
```

### 볼륨 권한 문제 시
```bash
# 볼륨 재생성
docker-compose down -v
docker-compose up -d
```

### 네트워크 충돌 시
```bash
# 네트워크 정리
docker network prune -f
docker-compose up -d
```

## 📁 디렉터리 구조

```
safework/
├── docker-compose.yml          # 통합 Docker Compose 설정
├── .env                        # 환경별 설정 파일
├── config/
│   ├── env.production.example  # 운영 환경 템플릿
│   └── env.development.example # 개발 환경 템플릿
├── archive/                    # 이전 파일들 보관
└── src/                        # 소스 코드
```

## 🚀 배포 방법

### CI/CD 자동 배포 (권장)
```bash
# 코드 푸시하면 자동 배포
git add .
git commit -m "feat: 새 기능 추가"
git push origin main
```

### 수동 배포
```bash
# 최신 이미지 풀
docker pull registry.jclee.me/safework:latest

# 컨테이너 재시작
docker-compose up -d --force-recreate
```

---

**✅ 파일 정리 완료!**  
이제 하나의 docker-compose.yml로 운영과 개발 환경을 모두 관리할 수 있습니다.