#!/bin/bash
set -e

# SafeWork GitOps CI/CD 구축 스크립트
# 기존 설정을 보존하면서 GitOps 템플릿 적용

echo "=== SafeWork GitOps CI/CD 설정 시작 ==="

# 백업 디렉토리 생성
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 기존 파일 백업
echo "기존 파일 백업 중..."
[ -d ".github/workflows" ] && cp -r .github/workflows "$BACKUP_DIR/" || true
[ -d "k8s" ] && cp -r k8s "$BACKUP_DIR/" || true
[ -f "docker-compose.yml" ] && cp docker-compose.yml "$BACKUP_DIR/" || true
[ -f "argocd-application.yaml" ] && cp argocd-application.yaml "$BACKUP_DIR/" || true

# GitHub CLI 로그인 체크
echo "GitHub CLI 인증 확인..."
gh auth status || gh auth login

# 프로젝트 설정값
GITHUB_ORG="${GITHUB_ORG:-JCLEE94}"
APP_NAME="${APP_NAME:-safework}"
NAMESPACE="${NAMESPACE:-production}"
REGISTRY_URL="registry.jclee.me"

echo "프로젝트 설정:"
echo "  - Organization: $GITHUB_ORG"
echo "  - Application: $APP_NAME"
echo "  - Namespace: $NAMESPACE"
echo "  - Registry: $REGISTRY_URL"

# GitHub Secrets/Variables 설정
echo "GitHub Secrets/Variables 설정 중..."
gh secret list | grep -q "REGISTRY_URL" || gh secret set REGISTRY_URL -b "$REGISTRY_URL"
gh secret list | grep -q "CHARTMUSEUM_URL" || gh secret set CHARTMUSEUM_URL -b "https://charts.jclee.me"
gh secret list | grep -q "CHARTMUSEUM_USERNAME" || gh secret set CHARTMUSEUM_USERNAME -b "admin"
gh secret list | grep -q "CHARTMUSEUM_PASSWORD" || read -sp "ChartMuseum 비밀번호 입력: " CHARTMUSEUM_PWD && echo && gh secret set CHARTMUSEUM_PASSWORD -b "$CHARTMUSEUM_PWD"

gh variable list | grep -q "GITHUB_ORG" || gh variable set GITHUB_ORG -b "${GITHUB_ORG}"
gh variable list | grep -q "APP_NAME" || gh variable set APP_NAME -b "${APP_NAME}"
gh variable list | grep -q "NAMESPACE" || gh variable set NAMESPACE -b "${NAMESPACE}"

# Helm Chart 디렉토리 구조 생성
echo "Helm Chart 생성 중..."
mkdir -p charts/${APP_NAME}/templates

# Chart.yaml 생성
cat > charts/${APP_NAME}/Chart.yaml << EOF
apiVersion: v2
name: ${APP_NAME}
description: SafeWork Pro - 건설업 보건관리 시스템
type: application
version: 1.0.2
appVersion: "1.0.2"
keywords:
  - safework
  - health-management
  - fastapi
  - react
home: https://safework.jclee.me
maintainers:
  - name: SafeWork Pro Team
    email: admin@jclee.me
EOF

# values.yaml 생성 (기존 설정 반영)
cat > charts/${APP_NAME}/values.yaml << EOF
replicaCount: 1

image:
  repository: registry.jclee.me/${APP_NAME}
  pullPolicy: Always
  tag: "latest"

imagePullSecrets: []

nameOverride: ""
fullnameOverride: ""

service:
  type: ClusterIP
  port: 3001
  targetPort: 3001

ingress:
  enabled: true
  className: "traefik"
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web,websecure
    traefik.ingress.kubernetes.io/router.middlewares: default-https-redirect@kubernetescrd
  hosts:
    - host: safework.jclee.me
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: safework-tls
      hosts:
        - safework.jclee.me

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

env:
  - name: ENVIRONMENT
    value: "production"
  - name: DATABASE_HOST
    value: "localhost"
  - name: DATABASE_PORT
    value: "5432"
  - name: DATABASE_NAME
    value: "health_management"
  - name: DATABASE_USER
    value: "admin"
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: safework-secrets
        key: db-password
  - name: REDIS_HOST
    value: "localhost"
  - name: REDIS_PORT
    value: "6379"
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: safework-secrets
        key: jwt-secret

volumes:
  - name: uploads
    hostPath:
      path: /data/safework/uploads
      type: DirectoryOrCreate
  - name: logs
    hostPath:
      path: /data/safework/logs
      type: DirectoryOrCreate
  - name: instance
    hostPath:
      path: /data/safework/instance
      type: DirectoryOrCreate

volumeMounts:
  - name: uploads
    mountPath: /app/uploads
  - name: logs
    mountPath: /app/logs
  - name: instance
    mountPath: /app/instance

probes:
  liveness:
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 60
    periodSeconds: 30
    timeoutSeconds: 10
  readiness:
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5

podSecurityContext:
  fsGroup: 1000
  runAsNonRoot: true
  runAsUser: 1000

securityContext:
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
  allowPrivilegeEscalation: false

# ArgoCD Image Updater 설정
argocd:
  imageUpdater:
    enabled: true
    imageList: |
      safework=registry.jclee.me/safework
    writeBackMethod: git
    gitBranch: main
    gitCommitUser: argocd-image-updater
    gitCommitEmail: image-updater@argocd
    gitCommitTemplate: |
      build: update image to {{.Image.Tag}}
    allowTags: '^prod-[0-9]{8}-[a-f0-9]{7}$'
    updateStrategy: latest
    pullSecret: ""
EOF

# deployment.yaml 생성
cat > charts/${APP_NAME}/templates/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "safework.fullname" . }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
  {{- if .Values.argocd.imageUpdater.enabled }}
  annotations:
    argocd-image-updater.argoproj.io/image-list: {{ .Values.argocd.imageUpdater.imageList }}
    argocd-image-updater.argoproj.io/write-back-method: {{ .Values.argocd.imageUpdater.writeBackMethod }}
    argocd-image-updater.argoproj.io/git-branch: {{ .Values.argocd.imageUpdater.gitBranch }}
    argocd-image-updater.argoproj.io/commit-user: {{ .Values.argocd.imageUpdater.gitCommitUser }}
    argocd-image-updater.argoproj.io/commit-email: {{ .Values.argocd.imageUpdater.gitCommitEmail }}
    argocd-image-updater.argoproj.io/commit-message-template: {{ .Values.argocd.imageUpdater.gitCommitTemplate | quote }}
    argocd-image-updater.argoproj.io/safework.allow-tags: {{ .Values.argocd.imageUpdater.allowTags }}
    argocd-image-updater.argoproj.io/safework.update-strategy: {{ .Values.argocd.imageUpdater.updateStrategy }}
    {{- if .Values.argocd.imageUpdater.pullSecret }}
    argocd-image-updater.argoproj.io/safework.pull-secret: {{ .Values.argocd.imageUpdater.pullSecret }}
    {{- end }}
  {{- end }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "safework.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "safework.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      initContainers:
      - name: wait-for-db
        image: busybox:1.35
        command: ['sh', '-c', 'until nc -z localhost 5432; do echo waiting for database; sleep 2; done;']
      - name: wait-for-redis
        image: busybox:1.35
        command: ['sh', '-c', 'until nc -z localhost 6379; do echo waiting for redis; sleep 2; done;']
      containers:
      - name: {{ .Chart.Name }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
          protocol: TCP
        env:
          {{- toYaml .Values.env | nindent 12 }}
        livenessProbe:
          {{- toYaml .Values.probes.liveness | nindent 12 }}
        readinessProbe:
          {{- toYaml .Values.probes.readiness | nindent 12 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        {{- if .Values.volumeMounts }}
        volumeMounts:
          {{- toYaml .Values.volumeMounts | nindent 12 }}
        {{- end }}
      {{- if .Values.volumes }}
      volumes:
        {{- toYaml .Values.volumes | nindent 8 }}
      {{- end }}
EOF

# service.yaml 생성
cat > charts/${APP_NAME}/templates/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: {{ include "safework.fullname" . }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "safework.selectorLabels" . | nindent 4 }}
EOF

# ingress.yaml 생성
cat > charts/${APP_NAME}/templates/ingress.yaml << 'EOF'
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "safework.fullname" . }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "safework.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
EOF

# _helpers.tpl 생성
cat > charts/${APP_NAME}/templates/_helpers.tpl << 'EOF'
{{/*
Expand the name of the chart.
*/}}
{{- define "safework.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "safework.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "safework.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "safework.labels" -}}
helm.sh/chart: {{ include "safework.chart" . }}
{{ include "safework.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "safework.selectorLabels" -}}
app.kubernetes.io/name: {{ include "safework.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
EOF

# GitHub Actions 워크플로우 생성
echo "GitHub Actions 워크플로우 생성 중..."
mkdir -p .github/workflows

cat > .github/workflows/gitops-deploy.yaml << 'EOF'
name: GitOps CI/CD Pipeline
on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ${{ secrets.REGISTRY_URL }}
  IMAGE_NAME: ${{ vars.APP_NAME }}
  CHART_NAME: ${{ vars.APP_NAME }}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME || 'anonymous' }}
          password: ${{ secrets.REGISTRY_PASSWORD || '' }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=prod-{{date 'YYYYMMDD'}}-{{sha}},enable=${{ github.ref == 'refs/heads/main' }}
            type=raw,value=1.{{date 'YYYYMMDD'}}.{{github.run_number}},enable=${{ github.ref == 'refs/heads/main' }}
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
          build-args: |
            BUILD_DATE=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.created'] }}
            VERSION=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.version'] }}

      - name: Install Helm
        if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')
        uses: azure/setup-helm@v3
        with:
          version: 'v3.13.0'

      - name: Package and push Helm chart
        if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')
        run: |
          # Chart 버전 설정
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            CHART_VERSION="${{ github.ref_name }}"
            CHART_VERSION=${CHART_VERSION#v}
          else
            CHART_VERSION="0.1.0-${{ github.sha }}"
          fi
          
          # 프로덕션 이미지 태그 추출
          PROD_TAG=$(echo "${{ steps.meta.outputs.tags }}" | grep -E "prod-[0-9]{8}-[a-f0-9]{7}" | head -n1 | cut -d: -f2)
          if [ -z "$PROD_TAG" ]; then
            PROD_TAG="latest"
          fi
          
          echo "Chart Version: ${CHART_VERSION}"
          echo "Image Tag: ${PROD_TAG}"
          
          # Chart 버전과 이미지 태그 업데이트
          sed -i "s/^version:.*/version: ${CHART_VERSION}/" ./charts/${{ env.CHART_NAME }}/Chart.yaml
          sed -i "s/^appVersion:.*/appVersion: \"${PROD_TAG}\"/" ./charts/${{ env.CHART_NAME }}/Chart.yaml
          sed -i "s/tag:.*/tag: \"${PROD_TAG}\"/" ./charts/${{ env.CHART_NAME }}/values.yaml
          
          # Helm chart 패키징
          helm package ./charts/${{ env.CHART_NAME }}
          
          # ChartMuseum에 업로드
          CHART_FILE="${{ env.CHART_NAME }}-${CHART_VERSION}.tgz"
          echo "Uploading ${CHART_FILE} to ChartMuseum..."
          
          response=$(curl -s -w "\n%{http_code}" \
            -u ${{ secrets.CHARTMUSEUM_USERNAME }}:${{ secrets.CHARTMUSEUM_PASSWORD }} \
            --data-binary "@${CHART_FILE}" \
            ${{ secrets.CHARTMUSEUM_URL }}/api/charts)
          
          http_code=$(echo "$response" | tail -n1)
          body=$(echo "$response" | head -n-1)
          
          if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
            echo "✅ Chart upload successful: ${CHART_VERSION}"
            echo "Response: $body"
          else
            echo "❌ Chart upload failed with HTTP $http_code"
            echo "Response: $body"
            exit 1
          fi

      - name: Summary
        if: always()
        run: |
          echo "## Build Summary" >> $GITHUB_STEP_SUMMARY
          echo "- Registry: ${{ env.REGISTRY }}" >> $GITHUB_STEP_SUMMARY
          echo "- Image: ${{ env.IMAGE_NAME }}" >> $GITHUB_STEP_SUMMARY
          echo "- Tags:" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          echo "${{ steps.meta.outputs.tags }}" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
EOF

# ArgoCD Application 생성
echo "ArgoCD Application 매니페스트 생성 중..."
cat > argocd-application.yaml << EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${APP_NAME}
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://charts.jclee.me
    chart: ${APP_NAME}
    targetRevision: ">=1.0.0"
    helm:
      releaseName: ${APP_NAME}
      values: |
        replicaCount: 1
        image:
          repository: registry.jclee.me/${APP_NAME}
          tag: latest
  destination:
    server: https://kubernetes.default.svc
    namespace: ${NAMESPACE}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - ServerSideApply=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
EOF

# 환경별 설정 파일 생성
echo "환경별 설정 파일 생성 중..."
mkdir -p charts/${APP_NAME}/environments

cat > charts/${APP_NAME}/environments/production.yaml << EOF
# Production environment overrides
replicaCount: 2

resources:
  limits:
    cpu: 3000m
    memory: 6Gi
  requests:
    cpu: 1000m
    memory: 2Gi

env:
  - name: ENVIRONMENT
    value: "production"
  - name: LOG_LEVEL
    value: "INFO"
EOF

cat > charts/${APP_NAME}/environments/staging.yaml << EOF
# Staging environment overrides
replicaCount: 1

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 200m
    memory: 512Mi

env:
  - name: ENVIRONMENT
    value: "staging"
  - name: LOG_LEVEL
    value: "DEBUG"
EOF

# Kubernetes 시크릿 생성 스크립트
cat > scripts/create-k8s-secrets.sh << 'EOF'
#!/bin/bash
set -e

NAMESPACE=${1:-production}

echo "Creating Kubernetes secrets for namespace: $NAMESPACE"

# Database password
read -sp "Enter database password: " DB_PASSWORD
echo
kubectl create secret generic safework-secrets \
  --from-literal=db-password="$DB_PASSWORD" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets created successfully"
EOF

chmod +x scripts/create-k8s-secrets.sh

# 배포 검증 스크립트
cat > scripts/verify-deployment.sh << 'EOF'
#!/bin/bash
set -e

APP_NAME=${1:-safework}
NAMESPACE=${2:-production}

echo "=== 배포 검증 시작 ==="
echo "App: $APP_NAME, Namespace: $NAMESPACE"

# 1. GitHub Actions 상태 확인
echo -n "1. GitHub Actions 실행 상태: "
LAST_RUN=$(gh run list --limit 1 --json status,conclusion,name --jq '.[0]')
echo "$LAST_RUN"

# 2. Helm Chart 확인
echo -n "2. ChartMuseum에서 Chart 확인: "
curl -s https://charts.jclee.me/api/charts/${APP_NAME} | jq -r '.[0].version' || echo "Chart not found"

# 3. ArgoCD 애플리케이션 상태
echo "3. ArgoCD 애플리케이션 상태:"
argocd app get ${APP_NAME} --grpc-web || echo "ArgoCD app not found"

# 4. Kubernetes 리소스 확인
echo "4. Kubernetes 리소스:"
kubectl get all -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME}

# 5. Pod 이미지 확인
echo -n "5. 실행 중인 이미지: "
kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} -o jsonpath='{.items[0].spec.containers[0].image}' || echo "No pods found"
echo

# 6. 헬스체크
echo -n "6. 애플리케이션 헬스체크: "
curl -sf https://${APP_NAME}.jclee.me/health || echo "Health check failed"
echo

echo "=== 검증 완료 ==="
EOF

chmod +x scripts/verify-deployment.sh

echo "=== GitOps 설정 완료 ==="
echo ""
echo "다음 단계:"
echo "1. Kubernetes 시크릿 생성:"
echo "   ./scripts/create-k8s-secrets.sh production"
echo ""
echo "2. ArgoCD 애플리케이션 생성:"
echo "   kubectl apply -f argocd-application.yaml"
echo ""
echo "3. 첫 배포 실행:"
echo "   git add ."
echo "   git commit -m 'feat: GitOps CI/CD 구성'"
echo "   git push origin main"
echo ""
echo "4. 배포 검증:"
echo "   ./scripts/verify-deployment.sh safework production"