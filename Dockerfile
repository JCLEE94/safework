# SafeWork Pro - Advanced Health Management System
# 건설업 보건관리 시스템 - 고도화된 엔터프라이즈 아키텍처

FROM node:24-alpine AS frontend-builder
ARG BUILD_TIME
ENV VITE_BUILD_TIME=$BUILD_TIME

WORKDIR /app
COPY package*.json ./
COPY index.html ./
RUN npm install

COPY src/ ./src/
COPY vite.config.ts tsconfig.json tsconfig.node.json ./
COPY tailwind.config.js* postcss.config.js** ./
RUN npm run build

# 빌드 결과 검증
RUN ls -la /app/dist/ && test -f /app/dist/index.html || (echo "❌ React 빌드 실패: index.html 없음" && exit 1)

# Python backend
FROM python:3.11-slim AS backend

ARG BUILD_TIME
ENV BUILD_TIME=$BUILD_TIME
ENV TZ=Asia/Seoul

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    wget \
    tzdata \
    wkhtmltopdf \
    fonts-nanum \
    libreoffice \
    --no-install-recommends \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 복사
COPY src/ ./src/
COPY main.py ./

# 프론트엔드 빌드 복사
COPY --from=frontend-builder /app/dist ./dist/

# Document 폴더 복사
COPY document/ ./document/

# 업로드 및 로그 디렉토리 생성
RUN mkdir -p uploads logs

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "main.py"]