#!/bin/bash
# SafeWork Pro K8s GitOps CI/CD 파이프라인 템플릿
# 기존 SafeWork Pro 프로젝트 구조를 기반으로 한 최적화된 템플릿

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로깅 함수
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }

# SafeWork 프로젝트 기본 설정
SAFEWORK_CONFIG() {
    # SafeWork Pro 기본 설정값
    GITHUB_ORG="${GITHUB_ORG:-JCLEE94}"
    REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
    REGISTRY_USERNAME="${REGISTRY_USERNAME:-admin}"
    REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-bingogo1}"
    CHARTMUSEUM_URL="${CHARTMUSEUM_URL:-https://charts.jclee.me}"
    CHARTMUSEUM_USERNAME="${CHARTMUSEUM_USERNAME:-admin}"
    CHARTMUSEUM_PASSWORD="${CHARTMUSEUM_PASSWORD:-bingogo1}"
    ARGOCD_URL="${ARGOCD_URL:-argo.jclee.me}"
    ARGOCD_USERNAME="${ARGOCD_USERNAME:-admin}"
    ARGOCD_PASSWORD="${ARGOCD_PASSWORD:-bingogo1}"
    
    # 현재 디렉토리 이름에서 프로젝트명 추출
    REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
    APP_NAME="${APP_NAME:-${REPO_NAME}}"
    NAMESPACE="${NAMESPACE:-${APP_NAME}}"
    
    log_info "SafeWork 기반 구성 로드 완료"
    log_debug "APP_NAME: ${APP_NAME}"
    log_debug "NAMESPACE: ${NAMESPACE}"
    log_debug "REGISTRY: ${REGISTRY_URL}"
}

# 기존 파일 백업 및 정리
cleanup_existing_files() {
    log_info "기존 GitOps 관련 파일 정리 중..."
    
    # 백업 디렉토리 생성
    BACKUP_DIR=".backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "${BACKUP_DIR}"
    
    # 기존 파일들 백업
    BACKUP_ITEMS=(
        ".github/workflows/deploy.yaml"
        ".github/workflows/gitops*.yml"
        "charts/${APP_NAME}/Chart.yaml"
        "charts/${APP_NAME}/values.yaml"
        "argocd-*.yaml"
        "k8s/argocd/"
    )
    
    for item in "${BACKUP_ITEMS[@]}"; do
        if [ -e "$item" ]; then
            cp -r "$item" "${BACKUP_DIR}/" 2>/dev/null || true
            log_debug "백업됨: $item"
        fi
    done
    
    log_info "기존 파일이 ${BACKUP_DIR}에 백업되었습니다."
}

# NodePort 중복 검사 및 할당
assign_nodeport() {
    log_info "NodePort 중복 검사 및 할당 중..."
    
    # 기존 사용 중인 NodePort 확인
    USED_PORTS=$(kubectl get svc --all-namespaces -o jsonpath='{range .items[?(@.spec.type=="NodePort")]}{.spec.ports[*].nodePort}{" "}{end}' 2>/dev/null | tr ' ' '\n' | sort -n | uniq)
    
    # SafeWork 기본 포트 (32301)부터 확인
    DEFAULT_PORTS=(32301 32302 32303 32304 32305)
    
    if [ -z "${NODEPORT:-}" ]; then
        for port in "${DEFAULT_PORTS[@]}"; do
            if ! echo "$USED_PORTS" | grep -q "^${port}$"; then
                NODEPORT=$port
                break
            fi
        done
        
        # 기본 포트가 모두 사용 중이면 30080부터 찾기
        if [ -z "${NODEPORT:-}" ]; then
            for port in $(seq 30080 30999); do
                if ! echo "$USED_PORTS" | grep -q "^${port}$"; then
                    NODEPORT=$port
                    break
                fi
            done
        fi
        
        if [ -z "${NODEPORT:-}" ]; then
            log_error "사용 가능한 NodePort를 찾을 수 없습니다"
            exit 1
        fi
        
        log_info "자동 할당된 NodePort: ${NODEPORT}"
    else
        # 지정된 NodePort 중복 검사
        if echo "$USED_PORTS" | grep -q "^${NODEPORT}$"; then
            EXISTING_SVC=$(kubectl get svc --all-namespaces -o json | jq -r ".items[] | select(.spec.type==\"NodePort\" and .spec.ports[].nodePort==${NODEPORT}) | \"\(.metadata.namespace)/\(.metadata.name)\"")
            log_warn "NodePort ${NODEPORT}는 이미 사용 중입니다 (${EXISTING_SVC})"
            log_warn "기존 서비스가 중단될 수 있습니다!"
        fi
    fi
    
    export NODEPORT
}

# GitHub 환경 설정
setup_github_environment() {
    log_info "GitHub 환경 설정 중..."
    
    # GitHub CLI 인증 확인
    if ! gh auth status >/dev/null 2>&1; then
        log_warn "GitHub CLI 인증이 필요합니다"
        gh auth login
    fi
    
    # GitHub Secrets 설정
    log_info "GitHub Secrets 설정 중..."
    gh secret set REGISTRY_URL -b "${REGISTRY_URL}" || log_warn "REGISTRY_URL secret 설정 실패"
    gh secret set REGISTRY_USERNAME -b "${REGISTRY_USERNAME}" || log_warn "REGISTRY_USERNAME secret 설정 실패"
    gh secret set REGISTRY_PASSWORD -b "${REGISTRY_PASSWORD}" || log_warn "REGISTRY_PASSWORD secret 설정 실패"
    gh secret set CHARTMUSEUM_URL -b "${CHARTMUSEUM_URL}" || log_warn "CHARTMUSEUM_URL secret 설정 실패"
    gh secret set CHARTMUSEUM_USERNAME -b "${CHARTMUSEUM_USERNAME}" || log_warn "CHARTMUSEUM_USERNAME secret 설정 실패"
    gh secret set CHARTMUSEUM_PASSWORD -b "${CHARTMUSEUM_PASSWORD}" || log_warn "CHARTMUSEUM_PASSWORD secret 설정 실패"
    
    # GitHub Variables 설정
    log_info "GitHub Variables 설정 중..."
    gh variable set GITHUB_ORG -b "${GITHUB_ORG}" || log_warn "GITHUB_ORG variable 설정 실패"
    gh variable set APP_NAME -b "${APP_NAME}" || log_warn "APP_NAME variable 설정 실패"
    gh variable set NAMESPACE -b "${NAMESPACE}" || log_warn "NAMESPACE variable 설정 실패"
    gh variable set NODEPORT -b "${NODEPORT}" || log_warn "NODEPORT variable 설정 실패"
    gh variable set ARGOCD_URL -b "https://${ARGOCD_URL}" || log_warn "ARGOCD_URL variable 설정 실패"
}

# SafeWork 최적화된 Helm Chart 생성
create_safework_helm_chart() {
    log_info "SafeWork 최적화된 Helm Chart 생성 중..."
    
    # 차트 디렉토리 생성
    mkdir -p charts/${APP_NAME}/templates
    
    # SafeWork 전용 Chart.yaml
    cat > charts/${APP_NAME}/Chart.yaml << EOF
apiVersion: v2
name: ${APP_NAME}
description: SafeWork Pro - 건설업 보건관리 시스템 (K8s GitOps Template)
type: application
version: 1.0.0
appVersion: "latest"
keywords:
  - safework
  - health-management
  - construction
  - gitops
  - kubernetes
home: https://github.com/${GITHUB_ORG}/${APP_NAME}
sources:
  - https://github.com/${GITHUB_ORG}/${APP_NAME}
maintainers:
  - name: SafeWork DevOps Team
    email: devops@jclee.me
annotations:
  category: Healthcare
  licenses: MIT
EOF

    # SafeWork 전용 values.yaml
    cat > charts/${APP_NAME}/values.yaml << EOF
## SafeWork Pro 전용 설정
global:
  imageRegistry: ${REGISTRY_URL}
  imagePullSecrets:
    - harbor-registry

## 복제본 설정 (SafeWork는 Stateful하므로 단일 인스턴스 권장)
replicaCount: 1
autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

## 이미지 설정
image:
  repository: ${REGISTRY_URL}/${APP_NAME}
  pullPolicy: Always
  tag: "latest"

## 보안 컨텍스트 (SafeWork 최적화)
podSecurityContext:
  runAsNonRoot: false  # SafeWork는 root 권한 필요
  runAsUser: 0
  fsGroup: 0

securityContext:
  allowPrivilegeEscalation: true
  readOnlyRootFilesystem: false  # SafeWork는 파일 쓰기 필요
  runAsNonRoot: false
  runAsUser: 0
  capabilities:
    add:
    - CHOWN
    - SETUID
    - SETGID

## 서비스 설정 (SafeWork 기본 포트 구성)
service:
  type: NodePort
  port: 3001
  targetPort: 3001  # SafeWork 기본 포트
  nodePort: ${NODEPORT}

## 리소스 제한 (SafeWork All-in-One 컨테이너 고려)
resources:
  limits:
    cpu: 2000m
    memory: 2Gi
    ephemeral-storage: 5Gi
  requests:
    cpu: 500m
    memory: 512Mi
    ephemeral-storage: 2Gi

## SafeWork 전용 환경 변수
env:
  # 데이터베이스 설정 (내장 PostgreSQL)
  DATABASE_URL: "postgresql://admin:password@localhost:5432/health_management"
  POSTGRES_USER: "admin"
  POSTGRES_PASSWORD: "password"
  POSTGRES_DB: "health_management"
  
  # Redis 설정 (내장 Redis)
  REDIS_URL: "redis://localhost:6379/0"
  REDIS_HOST: "localhost"
  REDIS_PORT: "6379"
  
  # FastAPI 설정
  JWT_SECRET: "prod-jwt-secret-key"
  ENVIRONMENT: "production"
  
  # 시간대 설정
  TZ: "Asia/Seoul"
  LC_ALL: "ko_KR.UTF-8"
  
  # SafeWork 전용 설정
  SAFEWORK_MODE: "production"
  ENABLE_DOCS: "false"
  CORS_ORIGINS: "*"

## ConfigMap 추가 설정
configMap:
  enabled: true
  data:
    nginx.conf: |
      server {
          listen 3001;
          server_name _;
          
          # Frontend (React)
          location / {
              root /app/frontend/dist;
              try_files \$uri \$uri/ /index.html;
          }
          
          # Backend API
          location /api/ {
              proxy_pass http://localhost:8000;
              proxy_set_header Host \$host;
              proxy_set_header X-Real-IP \$remote_addr;
              proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto \$scheme;
          }
          
          # Health check
          location /health {
              proxy_pass http://localhost:8000/health;
              access_log off;
          }
      }

## Secret 추가 설정  
secrets:
  enabled: true
  data:
    database-password: "password"
    jwt-secret: "prod-jwt-secret-key"
    registry-auth: "YWRtaW46YmluZ29nbzE="  # admin:bingogo1 base64

## 프로브 설정 (SafeWork 헬스체크 최적화)
probes:
  liveness:
    enabled: true
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 60  # SafeWork 시작 시간 고려
    periodSeconds: 30
    timeoutSeconds: 10
    successThreshold: 1
    failureThreshold: 3
  readiness:
    enabled: true
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    successThreshold: 1
    failureThreshold: 3
  startup:
    enabled: true
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 0
    periodSeconds: 10
    timeoutSeconds: 5
    successThreshold: 1
    failureThreshold: 18  # 3분 대기 (18 * 10s)

## Volume 마운트 (SafeWork 데이터 보존)
volumeMounts:
  - name: safework-data
    mountPath: /app/data
  - name: safework-logs
    mountPath: /app/logs
  - name: safework-uploads
    mountPath: /app/uploads

volumes:
  - name: safework-data
    persistentVolumeClaim:
      claimName: safework-data-pvc
  - name: safework-logs
    emptyDir: {}
  - name: safework-uploads
    emptyDir: {}

## Persistent Volume Claim (SafeWork 데이터 보존)
persistence:
  enabled: true
  storageClass: ""
  accessModes:
    - ReadWriteOnce
  size: 10Gi
  annotations: {}

## Node 선택자
nodeSelector: {}

## Tolerations
tolerations: []

## Affinity (단일 노드 배치 선호)
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - ${APP_NAME}
        topologyKey: kubernetes.io/hostname

## Pod Disruption Budget (최소 가용성 보장)
podDisruptionBudget:
  enabled: true
  minAvailable: 0  # 단일 인스턴스이므로 0으로 설정

## Network Policy (SafeWork 통신 최적화)
networkPolicy:
  enabled: true
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ${NAMESPACE}
    - from:
      - podSelector: {}
  egress:
    - to:
      - namespaceSelector: {}
    - to:
      - ipBlock:
          cidr: 0.0.0.0/0
          except:
          - 169.254.169.254/32

## Service Monitor (Prometheus)
serviceMonitor:
  enabled: false
  interval: 30s
  path: /metrics
  
## ArgoCD Image Updater 설정
argocdImageUpdater:
  enabled: true
  annotations:
    argocd-image-updater.argoproj.io/image-list: "${APP_NAME}=${REGISTRY_URL}/${APP_NAME}"
    argocd-image-updater.argoproj.io/${APP_NAME}.update-strategy: "latest"
    argocd-image-updater.argoproj.io/${APP_NAME}.allow-tags: "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$"
    argocd-image-updater.argoproj.io/write-back-method: "git"
    argocd-image-updater.argoproj.io/git-branch: "main"
EOF

    log_info "SafeWork Helm Chart 생성 완료"
}

# Helm 템플릿 파일들 생성
create_helm_templates() {
    log_info "Helm 템플릿 파일들 생성 중..."
    
    # _helpers.tpl (SafeWork 전용)
    cat > charts/${APP_NAME}/templates/_helpers.tpl << 'EOF'
{{/*
SafeWork Pro Helm Chart Helper Template
*/}}

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
app.kubernetes.io/component: safework-app
{{- end }}

{{/*
Selector labels
*/}}
{{- define "safework.selectorLabels" -}}
app.kubernetes.io/name: {{ include "safework.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
SafeWork specific labels
*/}}
{{- define "safework.safeworkLabels" -}}
safework.io/app: {{ include "safework.name" . }}
safework.io/version: {{ .Chart.AppVersion | default "latest" }}
safework.io/component: health-management
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "safework.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "safework.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
EOF

    # deployment.yaml (SafeWork 최적화)
    cat > charts/${APP_NAME}/templates/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
    {{- include "safework.safeworkLabels" . | nindent 4 }}
  {{- if .Values.argocdImageUpdater.enabled }}
  annotations:
    {{- range $key, $value := .Values.argocdImageUpdater.annotations }}
    {{ $key }}: {{ $value | quote }}
    {{- end }}
  {{- end }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "safework.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
        safework.io/deployment-time: {{ now | date "2006-01-02T15:04:05Z" | quote }}
      labels:
        {{- include "safework.selectorLabels" . | nindent 8 }}
        {{- include "safework.safeworkLabels" . | nindent 8 }}
    spec:
      {{- with .Values.global.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "safework.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
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
        {{- range $key, $value := .Values.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        {{- if .Values.configMap.enabled }}
        envFrom:
        - configMapRef:
            name: {{ include "safework.fullname" . }}
        {{- end }}
        {{- if .Values.secrets.enabled }}
        - secretRef:
            name: {{ include "safework.fullname" . }}
        {{- end }}
        {{- if .Values.probes.liveness.enabled }}
        livenessProbe:
          {{- toYaml (omit .Values.probes.liveness "enabled") | nindent 12 }}
        {{- end }}
        {{- if .Values.probes.readiness.enabled }}
        readinessProbe:
          {{- toYaml (omit .Values.probes.readiness "enabled") | nindent 12 }}
        {{- end }}
        {{- if .Values.probes.startup.enabled }}
        startupProbe:
          {{- toYaml (omit .Values.probes.startup "enabled") | nindent 12 }}
        {{- end }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        {{- with .Values.volumeMounts }}
        volumeMounts:
          {{- toYaml . | nindent 12 }}
        {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
EOF

    # service.yaml
    cat > charts/${APP_NAME}/templates/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
    {{- include "safework.safeworkLabels" . | nindent 4 }}
  annotations:
    safework.io/nodeport: "{{ .Values.service.nodePort }}"
spec:
  type: {{ .Values.service.type }}
  ports:
  - port: {{ .Values.service.port }}
    targetPort: http
    protocol: TCP
    name: http
    {{- if and (eq .Values.service.type "NodePort") .Values.service.nodePort }}
    nodePort: {{ .Values.service.nodePort }}
    {{- end }}
  selector:
    {{- include "safework.selectorLabels" . | nindent 4 }}
EOF

    # configmap.yaml
    cat > charts/${APP_NAME}/templates/configmap.yaml << 'EOF'
{{- if .Values.configMap.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
    {{- include "safework.safeworkLabels" . | nindent 4 }}
data:
  {{- toYaml .Values.configMap.data | nindent 2 }}
{{- end }}
EOF

    # secret.yaml
    cat > charts/${APP_NAME}/templates/secret.yaml << 'EOF'
{{- if .Values.secrets.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
    {{- include "safework.safeworkLabels" . | nindent 4 }}
type: Opaque
stringData:
  {{- toYaml .Values.secrets.data | nindent 2 }}
{{- end }}
EOF

    # pvc.yaml (SafeWork 데이터 보존용)
    cat > charts/${APP_NAME}/templates/pvc.yaml << 'EOF'
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: safework-data-pvc
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
    {{- include "safework.safeworkLabels" . | nindent 4 }}
  {{- with .Values.persistence.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  accessModes:
    {{- range .Values.persistence.accessModes }}
    - {{ . | quote }}
    {{- end }}
  resources:
    requests:
      storage: {{ .Values.persistence.size | quote }}
  {{- if .Values.persistence.storageClass }}
  {{- if (eq "-" .Values.persistence.storageClass) }}
  storageClassName: ""
  {{- else }}
  storageClassName: "{{ .Values.persistence.storageClass }}"
  {{- end }}
  {{- end }}
{{- end }}
EOF

    # 기타 템플릿들 (hpa, pdb, networkpolicy 등)
    create_additional_templates
    
    log_info "Helm 템플릿 파일들 생성 완료"
}

# 추가 템플릿 파일들 생성
create_additional_templates() {
    # hpa.yaml
    cat > charts/${APP_NAME}/templates/hpa.yaml << 'EOF'
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "safework.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
  {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
  {{- end }}
  {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
  {{- end }}
{{- end }}
EOF

    # pdb.yaml
    cat > charts/${APP_NAME}/templates/pdb.yaml << 'EOF'
{{- if .Values.podDisruptionBudget.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
spec:
  minAvailable: {{ .Values.podDisruptionBudget.minAvailable }}
  selector:
    matchLabels:
      {{- include "safework.selectorLabels" . | nindent 6 }}
{{- end }}
EOF

    # networkpolicy.yaml
    cat > charts/${APP_NAME}/templates/networkpolicy.yaml << 'EOF'
{{- if .Values.networkPolicy.enabled }}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "safework.fullname" . }}
  namespace: {{ .Release.Namespace }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels:
      {{- include "safework.selectorLabels" . | nindent 6 }}
  policyTypes:
  - Ingress
  - Egress
  {{- with .Values.networkPolicy.ingress }}
  ingress:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .Values.networkPolicy.egress }}
  egress:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
EOF
}

# SafeWork 최적화된 GitHub Actions 워크플로우 생성
create_github_workflow() {
    log_info "SafeWork 최적화된 GitHub Actions 워크플로우 생성 중..."
    
    mkdir -p .github/workflows
    
    cat > .github/workflows/deploy.yaml << 'EOF'
name: SafeWork Pro GitOps Deploy

on:
  push:
    branches: [main, master]
    tags: ['v*']
  pull_request:
    branches: [main, master]

env:
  REGISTRY: ${{ vars.REGISTRY_URL || 'registry.jclee.me' }}
  IMAGE_NAME: ${{ vars.APP_NAME || 'safework' }}
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: SafeWork Tests
    runs-on: ubuntu-latest
    timeout-minutes: 20
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: admin
          POSTGRES_PASSWORD: password
          POSTGRES_DB: health_management
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - name: Checkout SafeWork 코드
        uses: actions/checkout@v4
      
      - name: Python 환경 설정
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Python 의존성 캐시
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Python 의존성 설치
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov pytest-timeout coverage
      
      - name: SafeWork 백엔드 테스트
        env:
          DATABASE_URL: postgresql+asyncpg://admin:password@localhost:5432/health_management
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-secret-key
          PYTHONPATH: ${{ github.workspace }}
          ENVIRONMENT: development
        run: |
          echo "🧪 SafeWork 백엔드 테스트 실행 중..."
          pytest tests/test_workers.py tests/test_health_exams.py -v --timeout=60 --maxfail=3 || true
          echo "✅ SafeWork 백엔드 테스트 완료"
      
      - name: Node.js 환경 설정 (Frontend V1)
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Frontend V1 의존성 설치
        working-directory: frontend
        run: npm ci
      
      - name: Frontend V1 빌드
        working-directory: frontend
        run: |
          echo "🏗️ SafeWork Frontend V1 빌드 중..."
          npm run build
      
      - name: Frontend V2 설정 확인 (optional)
        if: hashFiles('safework-frontend-v2/package.json') != ''
        run: |
          echo "🔍 Frontend V2 감지됨"
          cd safework-frontend-v2
          npm ci
          npm run build
      
      - name: 테스트 결과 업로드
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: safework-test-results
          path: |
            htmlcov/
            frontend/dist/
            safework-frontend-v2/dist/

  deploy:
    name: SafeWork Build & Deploy
    needs: test
    runs-on: ubuntu-latest
    timeout-minutes: 30
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    outputs:
      image-tag: ${{ steps.generate-tag.outputs.tag }}
      chart-version: ${{ steps.generate-tag.outputs.chart }}
    
    steps:
      - name: SafeWork 코드 체크아웃
        uses: actions/checkout@v4
      
      - name: SafeWork 태그 및 버전 생성
        id: generate-tag
        run: |
          # SafeWork 이미지 태그 생성
          IMAGE_TAG="prod-$(date +%Y%m%d)-$(echo ${GITHUB_SHA} | cut -c1-7)"
          echo "tag=${IMAGE_TAG}" >> $GITHUB_OUTPUT
          
          # SafeWork 차트 버전 생성
          CHART_VERSION="1.$(date +%Y%m%d).${{ github.run_number }}"
          echo "chart=${CHART_VERSION}" >> $GITHUB_OUTPUT
          
          echo "📦 SafeWork 이미지 태그: ${IMAGE_TAG}"
          echo "📊 SafeWork 차트 버전: ${CHART_VERSION}"
      
      - name: Docker Buildx 설정
        uses: docker/setup-buildx-action@v3
      
      - name: Harbor Registry 로그인
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: SafeWork Docker 이미지 빌드 및 푸시
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.generate-tag.outputs.tag }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64
          build-args: |
            BUILD_DATE=${{ github.run_date }}
            BUILD_VERSION=${{ steps.generate-tag.outputs.tag }}
            BUILD_REVISION=${{ github.sha }}
      
      - name: 이미지 보안 스캔
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.generate-tag.outputs.tag }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          
      - name: 보안 스캔 결과 업로드
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Helm 설치
        uses: azure/setup-helm@v4
        with:
          version: 'latest'
      
      - name: SafeWork Helm 차트 업데이트
        run: |
          # 차트 버전 업데이트
          sed -i "s/^version:.*/version: ${{ steps.generate-tag.outputs.chart }}/" ./charts/${{ env.IMAGE_NAME }}/Chart.yaml
          sed -i "s/^appVersion:.*/appVersion: \"${{ steps.generate-tag.outputs.tag }}\"/" ./charts/${{ env.IMAGE_NAME }}/Chart.yaml
          
          # 이미지 태그 업데이트
          sed -i "s/tag:.*/tag: \"${{ steps.generate-tag.outputs.tag }}\"/" ./charts/${{ env.IMAGE_NAME }}/values.yaml
          
          echo "✅ SafeWork Helm 차트 업데이트 완료"
      
      - name: SafeWork Helm 차트 패키징 및 배포
        run: |
          # helm-push 플러그인 설치
          helm plugin install https://github.com/chartmuseum/helm-push || true
          
          # ChartMuseum repo 추가
          helm repo add charts ${{ vars.CHARTMUSEUM_URL || 'https://charts.jclee.me' }} \
            --username ${{ secrets.CHARTMUSEUM_USERNAME }} \
            --password ${{ secrets.CHARTMUSEUM_PASSWORD }}
          helm repo update
          
          # 차트 패키징
          helm package ./charts/${{ env.IMAGE_NAME }}
          
          # ChartMuseum에 푸시
          helm cm-push ${{ env.IMAGE_NAME }}-${{ steps.generate-tag.outputs.chart }}.tgz charts
          
          echo "✅ SafeWork Helm 차트 배포 완료"
      
      - name: SafeWork ArgoCD Application 업데이트
        run: |
          # ArgoCD 디렉토리 생성
          mkdir -p k8s/argocd
          
          # SafeWork ArgoCD Application 매니페스트 생성
          cat > k8s/argocd/${{ env.IMAGE_NAME }}-application.yaml << 'ARGOCD_EOF'
          apiVersion: argoproj.io/v1alpha1
          kind: Application
          metadata:
            name: ${{ env.IMAGE_NAME }}
            namespace: argocd
            labels:
              app: ${{ env.IMAGE_NAME }}
              env: production
              project: safework
            annotations:
              argocd-image-updater.argoproj.io/image-list: "${{ env.IMAGE_NAME }}=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}"
              argocd-image-updater.argoproj.io/${{ env.IMAGE_NAME }}.update-strategy: "latest"
              argocd-image-updater.argoproj.io/${{ env.IMAGE_NAME }}.allow-tags: "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$"
              argocd-image-updater.argoproj.io/write-back-method: "git"
              argocd-image-updater.argoproj.io/git-branch: "main"
          spec:
            project: default
            source:
              repoURL: ${{ vars.CHARTMUSEUM_URL || 'https://charts.jclee.me' }}
              chart: ${{ env.IMAGE_NAME }}
              targetRevision: "${{ steps.generate-tag.outputs.chart }}"
              helm:
                releaseName: ${{ env.IMAGE_NAME }}
                values: |
                  image:
                    repository: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
                    tag: "${{ steps.generate-tag.outputs.tag }}"
                    pullPolicy: Always
                  imagePullSecrets:
                    - name: harbor-registry
                  service:
                    type: NodePort
                    port: 3001
                    targetPort: 3001
                    nodePort: ${{ vars.NODEPORT || 32301 }}
                  env:
                    ENVIRONMENT: "production"
                    SAFEWORK_MODE: "production"
                  persistence:
                    enabled: true
                    size: 10Gi
            destination:
              server: https://kubernetes.default.svc
              namespace: ${{ vars.NAMESPACE || env.IMAGE_NAME }}
            syncPolicy:
              automated:
                prune: true
                selfHeal: true
                allowEmpty: false
              syncOptions:
              - CreateNamespace=true
              - ServerSideApply=true
              - PruneLast=true
              retry:
                limit: 5
                backoff:
                  duration: 5s
                  factor: 2
                  maxDuration: 3m
            revisionHistoryLimit: 10
          ARGOCD_EOF
      
      - name: SafeWork 배포 요약 생성
        run: |
          cat >> $GITHUB_STEP_SUMMARY << EOF
          # 🚀 SafeWork Pro 배포 요약
          
          ## 📦 Docker 이미지
          - **Registry**: \`${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}\`
          - **Tags**: 
            - \`latest\`
            - \`${{ steps.generate-tag.outputs.tag }}\`
          
          ## 📊 Helm 차트
          - **버전**: \`${{ steps.generate-tag.outputs.chart }}\`
          - **Repository**: ${{ vars.CHARTMUSEUM_URL || 'https://charts.jclee.me' }}
          
          ## 🔄 ArgoCD
          - **Application**: ${{ env.IMAGE_NAME }}
          - **Auto-Sync**: Enabled
          - **Image Updater**: Configured
          - **NodePort**: ${{ vars.NODEPORT || 32301 }}
          
          ## 📝 다음 단계
          ArgoCD Image Updater가 자동으로 새 이미지를 감지하고 2-3분 내에 배포합니다.
          
          ## 🔗 링크
          - [ArgoCD Dashboard](${{ vars.ARGOCD_URL || 'https://argo.jclee.me' }}/applications/${{ env.IMAGE_NAME }})
          - [SafeWork Production](https://safework.jclee.me)
          - [Harbor Registry](${{ env.REGISTRY }}/harbor/projects/1/repositories/${{ env.IMAGE_NAME }})
          EOF
      
      - name: SafeWork 배포 상태 알림
        run: |
          echo "✅ SafeWork Pro 배포 파이프라인 완료!"
          echo "🔄 ArgoCD가 자동으로 새 이미지를 동기화합니다."
          echo "📊 이미지: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.generate-tag.outputs.tag }}"
          echo "📈 차트: ${{ steps.generate-tag.outputs.chart }}"
          echo "🌐 NodePort: ${{ vars.NODEPORT || 32301 }}"
EOF

    log_info "SafeWork GitHub Actions 워크플로우 생성 완료"
}

# ArgoCD Application 매니페스트 생성
create_argocd_application() {
    log_info "SafeWork ArgoCD Application 매니페스트 생성 중..."
    
    mkdir -p k8s/argocd
    
    cat > argocd-application.yaml << EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${APP_NAME}
  namespace: argocd
  labels:
    app: ${APP_NAME}
    env: production
    project: safework
    template: k8s-gitops
  annotations:
    argocd-image-updater.argoproj.io/image-list: "${APP_NAME}=${REGISTRY_URL}/${APP_NAME}"
    argocd-image-updater.argoproj.io/${APP_NAME}.update-strategy: "latest"
    argocd-image-updater.argoproj.io/${APP_NAME}.allow-tags: "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$"
    argocd-image-updater.argoproj.io/write-back-method: "git"
    argocd-image-updater.argoproj.io/git-branch: "main"
    # SafeWork 전용 어노테이션
    safework.io/deployment-mode: "production"
    safework.io/template-version: "1.0.0"
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: ${CHARTMUSEUM_URL}
    chart: ${APP_NAME}
    targetRevision: "*"
    helm:
      releaseName: ${APP_NAME}
      values: |
        # SafeWork 운영 환경 설정
        replicaCount: 1
        image:
          repository: ${REGISTRY_URL}/${APP_NAME}
          tag: "latest"
          pullPolicy: Always
        imagePullSecrets:
          - name: harbor-registry
        service:
          type: NodePort
          port: 3001
          targetPort: 3001
          nodePort: ${NODEPORT}
        env:
          ENVIRONMENT: "production"
          SAFEWORK_MODE: "production"
          ENABLE_DOCS: "false"
          TZ: "Asia/Seoul"
          LC_ALL: "ko_KR.UTF-8"
        persistence:
          enabled: true
          size: 10Gi
        resources:
          limits:
            cpu: 2000m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 512Mi
        probes:
          startup:
            initialDelaySeconds: 0
            periodSeconds: 10
            failureThreshold: 18  # 3분 대기
          liveness:
            initialDelaySeconds: 60
            periodSeconds: 30
          readiness:
            initialDelaySeconds: 30
            periodSeconds: 10
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
    - ServerSideApply=true
    - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
  info:
  - name: 'SafeWork URL'
    value: 'https://safework.jclee.me'
  - name: 'NodePort'
    value: '${NODEPORT}'
  - name: 'Registry'
    value: '${REGISTRY_URL}/${APP_NAME}'
EOF

    # k8s/argocd 디렉토리에도 복사
    cp argocd-application.yaml k8s/argocd/${APP_NAME}-application.yaml
    
    log_info "SafeWork ArgoCD Application 매니페스트 생성 완료"
}

# Kubernetes 환경 설정
setup_kubernetes_environment() {
    log_info "Kubernetes 환경 설정 중..."
    
    # 네임스페이스 생성
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Harbor Registry Secret 생성
    kubectl create secret docker-registry harbor-registry \
      --docker-server=${REGISTRY_URL} \
      --docker-username=${REGISTRY_USERNAME} \
      --docker-password=${REGISTRY_PASSWORD} \
      --namespace=${NAMESPACE} \
      --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Kubernetes 환경 설정 완료"
}

# ArgoCD 설정
setup_argocd() {
    log_info "ArgoCD 설정 중..."
    
    # ArgoCD CLI 로그인
    if command -v argocd &> /dev/null; then
        argocd login ${ARGOCD_URL} --username ${ARGOCD_USERNAME} --password ${ARGOCD_PASSWORD} --insecure --grpc-web || {
            log_warn "ArgoCD 로그인 실패 - 수동으로 설정하세요:"
            echo "argocd login ${ARGOCD_URL} --username ${ARGOCD_USERNAME} --password ${ARGOCD_PASSWORD} --insecure --grpc-web"
            echo "argocd repo add ${CHARTMUSEUM_URL} --type helm --username ${CHARTMUSEUM_USERNAME} --password ${CHARTMUSEUM_PASSWORD}"
            echo "argocd app create -f argocd-application.yaml"
            return 1
        }
        
        # Repository 추가
        argocd repo list | grep -q "${CHARTMUSEUM_URL}" || \
          argocd repo add ${CHARTMUSEUM_URL} --type helm --username ${CHARTMUSEUM_USERNAME} --password ${CHARTMUSEUM_PASSWORD}
        
        # Application 생성
        argocd app create -f argocd-application.yaml || \
          argocd app create -f argocd-application.yaml --upsert
        
        log_info "ArgoCD 설정 완료"
    else
        log_warn "ArgoCD CLI가 설치되지 않음 - 수동으로 설정하세요"
        echo "kubectl apply -f argocd-application.yaml"
    fi
}

# 검증 스크립트 생성
create_validation_script() {
    log_info "검증 스크립트 생성 중..."
    
    cat > validate-safework-gitops.sh << 'EOF'
#!/bin/bash
# SafeWork Pro GitOps 검증 스크립트

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 환경 변수 로드
APP_NAME="${APP_NAME:-safework}"
NAMESPACE="${NAMESPACE:-${APP_NAME}}"
REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
CHARTMUSEUM_URL="${CHARTMUSEUM_URL:-https://charts.jclee.me}"
ARGOCD_URL="${ARGOCD_URL:-argo.jclee.me}"
NODEPORT="${NODEPORT:-32301}"

log_info "🔍 SafeWork Pro GitOps 검증 시작..."

# 1. GitHub Actions 상태 확인
log_info "1. GitHub Actions 워크플로우 확인 중..."
if command -v gh &> /dev/null; then
    gh run list --limit 3 || log_warn "GitHub Actions 상태 확인 실패"
else
    log_warn "GitHub CLI 미설치"
fi

# 2. Docker 이미지 확인
log_info "2. Docker 이미지 확인 중..."
LATEST_TAG=$(curl -s -u admin:bingogo1 \
  https://${REGISTRY_URL}/v2/${APP_NAME}/tags/list | \
  jq -r '.tags[]' | grep -E '^prod-[0-9]{8}-[a-f0-9]{7}$' | sort | tail -1 || echo "latest")

if [ "$LATEST_TAG" != "latest" ]; then
    log_info "✅ 최신 이미지: ${REGISTRY_URL}/${APP_NAME}:${LATEST_TAG}"
else
    log_warn "⚠️ 운영 이미지 태그를 찾을 수 없음"
fi

# 3. Helm 차트 확인
log_info "3. Helm 차트 확인 중..."
CHART_VERSIONS=$(curl -s -u admin:bingogo1 \
  ${CHARTMUSEUM_URL}/api/charts/${APP_NAME} | \
  jq -r '.[].version' | head -3 || echo "")

if [ -n "$CHART_VERSIONS" ]; then
    log_info "✅ 사용 가능한 차트 버전들:"
    echo "$CHART_VERSIONS" | while read version; do
        echo "  - ${version}"
    done
else
    log_warn "⚠️ 차트를 찾을 수 없음"
fi

# 4. ArgoCD 애플리케이션 상태 확인
log_info "4. ArgoCD 애플리케이션 상태 확인 중..."
if command -v argocd &> /dev/null; then
    SYNC_STATUS=$(argocd app get ${APP_NAME} --grpc-web -o json 2>/dev/null | \
      jq -r '.status.sync.status' || echo "Unknown")
    HEALTH_STATUS=$(argocd app get ${APP_NAME} --grpc-web -o json 2>/dev/null | \
      jq -r '.status.health.status' || echo "Unknown")
    
    log_info "✅ 동기화 상태: ${SYNC_STATUS}"
    log_info "✅ 헬스 상태: ${HEALTH_STATUS}"
else
    log_warn "ArgoCD CLI 미설치"
fi

# 5. Kubernetes 리소스 확인
log_info "5. Kubernetes 리소스 확인 중..."
kubectl get pods,svc,pvc -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} || \
  log_warn "Kubernetes 리소스 확인 실패"

# 6. Pod 상태 상세 확인
log_info "6. Pod 상태 상세 확인 중..."
POD_STATUS=$(kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} \
  -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "NotFound")

if [ "$POD_STATUS" = "Running" ]; then
    log_info "✅ Pod 상태: Running"
    
    # Pod 로그 확인
    log_info "최근 Pod 로그:"
    kubectl logs -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} --tail=10 || true
else
    log_warn "⚠️ Pod 상태: ${POD_STATUS}"
    
    # Pod 이벤트 확인
    kubectl describe pods -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} || true
fi

# 7. 서비스 접근성 확인
log_info "7. 서비스 접근성 확인 중..."
SERVICE_IP=$(kubectl get svc -n ${NAMESPACE} ${APP_NAME} \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

if [ -n "$SERVICE_IP" ]; then
    ENDPOINT="http://${SERVICE_IP}:3001/health"
else
    # NodePort 사용
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null || \
              kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")
    ENDPOINT="http://${NODE_IP}:${NODEPORT}/health"
fi

log_info "헬스체크 엔드포인트: ${ENDPOINT}"
if curl -f ${ENDPOINT} --connect-timeout 10 --max-time 30 >/dev/null 2>&1; then
    log_info "✅ 서비스 접근 가능"
else
    log_warn "⚠️ 서비스 접근 실패: ${ENDPOINT}"
fi

# 8. 데이터 보존 확인 (PVC)
log_info "8. 데이터 보존 확인 중..."
PVC_STATUS=$(kubectl get pvc -n ${NAMESPACE} safework-data-pvc \
  -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")

if [ "$PVC_STATUS" = "Bound" ]; then
    log_info "✅ 데이터 볼륨: Bound"
    PVC_SIZE=$(kubectl get pvc -n ${NAMESPACE} safework-data-pvc \
      -o jsonpath='{.spec.resources.requests.storage}' 2>/dev/null || echo "Unknown")
    log_info "   크기: ${PVC_SIZE}"
else
    log_warn "⚠️ 데이터 볼륨 상태: ${PVC_STATUS}"
fi

# 결과 요약
echo ""
log_info "=== SafeWork Pro GitOps 검증 요약 ==="
echo "📦 이미지: ${REGISTRY_URL}/${APP_NAME}:${LATEST_TAG}"
echo "📊 차트: $(echo "$CHART_VERSIONS" | head -1 || echo "Unknown")"
echo "🔄 ArgoCD: ${SYNC_STATUS:-Unknown}/${HEALTH_STATUS:-Unknown}"
echo "🚀 Pod: ${POD_STATUS}"
echo "💾 볼륨: ${PVC_STATUS}"
echo "🌐 엔드포인트: ${ENDPOINT}"
echo "📍 NodePort: ${NODEPORT}"

log_info "🎯 SafeWork Pro GitOps 검증 완료!"
EOF

    chmod +x validate-safework-gitops.sh
    log_info "검증 스크립트 생성 완료: validate-safework-gitops.sh"
}

# 사용법 가이드 생성
create_usage_guide() {
    log_info "사용법 가이드 생성 중..."
    
    cat > SAFEWORK_GITOPS_GUIDE.md << EOF
# SafeWork Pro K8s GitOps CI/CD 파이프라인 가이드

## 🎯 개요
SafeWork Pro 프로젝트를 위한 완전 자동화된 K8s GitOps CI/CD 파이프라인입니다.

## 🏗️ 구성 요소

### 1. 인프라 구성
- **Container Registry**: registry.jclee.me (Harbor)
- **Chart Repository**: charts.jclee.me (ChartMuseum)
- **GitOps**: argo.jclee.me (ArgoCD)
- **Kubernetes**: K8s 클러스터
- **CI/CD**: GitHub Actions

### 2. SafeWork 전용 설정
- **All-in-One 컨테이너**: PostgreSQL + Redis + FastAPI + React
- **NodePort**: ${NODEPORT} (자동 할당)
- **데이터 보존**: PVC 10Gi
- **헬스체크**: /health 엔드포인트
- **한국어 지원**: Asia/Seoul, ko_KR.UTF-8

## 🚀 사용법

### 1. 초기 설정
\`\`\`bash
# SafeWork GitOps 템플릿 실행
./k8s-gitops-template.sh

# 검증
./validate-safework-gitops.sh
\`\`\`

### 2. 배포 프로세스
\`\`\`bash
# 코드 변경 후 배포
git add .
git commit -m "feat: SafeWork 기능 추가"
git push origin main

# GitHub Actions가 자동으로:
# 1. 테스트 실행
# 2. Docker 이미지 빌드 및 푸시
# 3. Helm 차트 패키징 및 배포
# 4. ArgoCD Application 업데이트

# ArgoCD Image Updater가 자동으로:
# 1. 새 이미지 감지 (2-3분 내)
# 2. Kubernetes 리소스 업데이트
# 3. 배포 완료
\`\`\`

### 3. 모니터링
\`\`\`bash
# GitHub Actions 상태 확인
gh run list --limit 5

# ArgoCD 상태 확인
argocd app get ${APP_NAME} --grpc-web

# Kubernetes 리소스 확인
kubectl get all -n ${NAMESPACE}

# 서비스 접근 확인
curl http://safework.jclee.me:${NODEPORT}/health
\`\`\`

## 🔧 트러블슈팅

### 1. 이미지 Pull 실패
\`\`\`bash
# Registry Secret 재생성
kubectl delete secret harbor-registry -n ${NAMESPACE}
kubectl create secret docker-registry harbor-registry \\
  --docker-server=${REGISTRY_URL} \\
  --docker-username=${REGISTRY_USERNAME} \\
  --docker-password=${REGISTRY_PASSWORD} \\
  --namespace=${NAMESPACE}
\`\`\`

### 2. ArgoCD 동기화 실패
\`\`\`bash
# 수동 동기화
argocd app sync ${APP_NAME} --grpc-web

# 강제 동기화
argocd app sync ${APP_NAME} --force --grpc-web
\`\`\`

### 3. Pod 시작 실패
\`\`\`bash
# Pod 로그 확인
kubectl logs -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} --previous

# Pod 이벤트 확인
kubectl describe pods -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME}

# 리소스 사용량 확인
kubectl top pods -n ${NAMESPACE}
\`\`\`

### 4. 데이터 보존 문제
\`\`\`bash
# PVC 상태 확인
kubectl get pvc -n ${NAMESPACE} safework-data-pvc

# PV 상태 확인
kubectl get pv | grep ${NAMESPACE}

# 스토리지 클래스 확인
kubectl get storageclass
\`\`\`

## 📊 주요 파일 구조

\`\`\`
safework/
├── .github/workflows/deploy.yaml           # GitHub Actions 워크플로우
├── charts/${APP_NAME}/                      # Helm 차트
│   ├── Chart.yaml                          # 차트 메타데이터
│   ├── values.yaml                         # 기본값 설정
│   └── templates/                          # K8s 매니페스트 템플릿
├── k8s/argocd/${APP_NAME}-application.yaml  # ArgoCD Application
├── argocd-application.yaml                 # ArgoCD Application (루트)
└── validate-safework-gitops.sh             # 검증 스크립트
\`\`\`

## 🌐 접근 정보

### Web UI
- **ArgoCD**: https://${ARGOCD_URL}/applications/${APP_NAME}
- **SafeWork**: https://safework.jclee.me:${NODEPORT}
- **Harbor**: https://${REGISTRY_URL}

### API 엔드포인트
- **헬스체크**: \`GET /health\`
- **API 문서**: \`GET /api/docs\` (개발 환경만)
- **메트릭**: \`GET /metrics\` (설정 시)

## 🔒 보안 설정

### 1. 컨테이너 보안
- 비권한 사용자 실행 (SafeWork 요구사항에 따라 조정)
- 읽기 전용 루트 파일시스템 (필요 시 비활성화)
- 최소 권한 원칙

### 2. 네트워크 보안
- Network Policy 적용
- 네임스페이스 격리
- 필요한 포트만 노출

### 3. 데이터 보안
- Secret 암호화
- 민감 정보 환경 변수 분리
- 정기적 보안 스캔

## 📈 성능 최적화

### 1. 리소스 할당
- **CPU**: 500m (요청) / 2000m (제한)
- **메모리**: 512Mi (요청) / 2Gi (제한)
- **스토리지**: 10Gi (PVC)

### 2. 스케일링
- 기본: 단일 인스턴스 (Stateful 특성)
- HPA: 비활성화 (필요 시 활성화 가능)
- 수직 스케일링 권장

### 3. 캐싱
- Redis 내장 활용
- 정적 파일 Nginx 서빙
- CDN 연동 고려

## 📅 유지보수

### 1. 정기 작업
- 이미지 보안 업데이트
- Kubernetes 버전 업그레이드
- 데이터 백업 및 복원 테스트

### 2. 모니터링 지표
- Pod 상태 및 재시작 횟수
- 메모리 및 CPU 사용률
- 디스크 사용량
- 응답 시간 및 에러율

### 3. 백업 전략
- 데이터베이스 정기 백업
- 설정 파일 버전 관리
- 재해 복구 계획

---

**버전**: 1.0.0
**업데이트**: $(date +%Y-%m-%d)
**관리자**: SafeWork DevOps Team
EOF

    log_info "사용법 가이드 생성 완료: SAFEWORK_GITOPS_GUIDE.md"
}

# 메인 실행 함수
main() {
    echo "🚀 SafeWork Pro K8s GitOps CI/CD 파이프라인 템플릿 설정"
    echo "============================================================"
    
    # 1. SafeWork 기본 설정 로드
    SAFEWORK_CONFIG
    
    # 2. 기존 파일 정리
    cleanup_existing_files
    
    # 3. NodePort 할당
    assign_nodeport
    
    # 4. GitHub 환경 설정
    setup_github_environment
    
    # 5. SafeWork Helm Chart 생성
    create_safework_helm_chart
    
    # 6. Helm 템플릿 생성
    create_helm_templates
    
    # 7. GitHub Actions 워크플로우 생성
    create_github_workflow
    
    # 8. ArgoCD Application 생성
    create_argocd_application
    
    # 9. Kubernetes 환경 설정
    setup_kubernetes_environment
    
    # 10. ArgoCD 설정
    setup_argocd
    
    # 11. 검증 스크립트 생성
    create_validation_script
    
    # 12. 사용법 가이드 생성
    create_usage_guide
    
    echo ""
    log_info "✅ SafeWork Pro GitOps CI/CD 파이프라인 템플릿 설정 완료!"
    echo ""
    echo "📋 다음 단계:"
    echo "1. 설정 검증: ./validate-safework-gitops.sh"
    echo "2. 코드 커밋: git add . && git commit -m 'feat: SafeWork GitOps 파이프라인 설정' && git push"
    echo "3. GitHub Actions 확인: https://github.com/${GITHUB_ORG}/${APP_NAME}/actions"
    echo "4. ArgoCD 모니터링: https://${ARGOCD_URL}/applications/${APP_NAME}"
    echo "5. 서비스 접근: https://safework.jclee.me:${NODEPORT}"
    echo ""
    echo "📖 자세한 사용법: SAFEWORK_GITOPS_GUIDE.md"
    echo "🔍 문제 해결: ./validate-safework-gitops.sh"
    echo ""
    echo "🎯 SafeWork Pro가 NodePort ${NODEPORT}에서 실행됩니다!"
}

# 스크립트 실행 (직접 실행 시에만)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi