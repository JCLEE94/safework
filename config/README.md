# SafeWork Pro 설정 구조

## 📁 폴더 구조
```
config/
├── project.yml          # 프로젝트 전체 설정
├── workflows.yml        # GitHub Actions 워크플로우 설정
├── watchtower.yml       # Watchtower 자동 배포 설정
├── env/                 # 환경변수 템플릿
│   ├── .env.example
│   └── .env.production
├── secrets/             # 비밀 정보 관리 (gitignore)
│   └── README.md
└── README.md           # 이 파일
```

## 🚀 배포 흐름 (간소화)

### 1. 개발자 푸시
```bash
git push origin main
```

### 2. GitHub Actions (자동)
- 코드 체크아웃
- Docker 이미지 빌드
- registry.jclee.me로 푸시
- **끝** (SSH 배포 제거됨)

### 3. Watchtower (운영서버에서 자동)
- 30초마다 registry.jclee.me 체크
- 새 이미지 발견시 자동 pull
- 컨테이너 자동 재시작
- 이전 이미지 자동 정리

## 🔧 설정 파일 설명

### project.yml
- 프로젝트 메타데이터
- Docker Registry 정보
- 포트 설정
- 배포 서버 정보

### workflows.yml
- GitHub Actions 공통 설정
- 타임아웃, 재시도 설정
- 보안 스캔 설정

### watchtower.yml
- 운영 서버용 Watchtower 설정
- 30초 간격 모니터링
- 라벨 기반 자동 업데이트

## 📝 환경변수 관리

### 로컬 개발
```bash
cp config/env/.env.example .env
# 필요한 값 수정
```

### GitHub Secrets (필수)
- REGISTRY_USERNAME
- REGISTRY_PASSWORD

### 운영 서버 (Watchtower가 처리)
- Docker config.json에 인증 정보 저장됨
- 추가 설정 불필요