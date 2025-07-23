#!/bin/bash
# SafeWork GitOps CI/CD 구축 스크립트
set -e

echo "🚀 SafeWork GitOps CI/CD 구축 시작"
echo "=================================="

# 프로젝트 설정값
GITHUB_ORG="JCLEE94"
APP_NAME="safework"
NAMESPACE="safework"
REGISTRY="registry.jclee.me"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# GitHub CLI 로그인 체크
echo -e "${YELLOW}📋 GitHub CLI 상태 확인...${NC}"
if ! gh auth status &>/dev/null; then
    echo -e "${RED}❌ GitHub CLI 로그인 필요${NC}"
    gh auth login
fi

# GitHub Secrets/Variables 설정
echo -e "${YELLOW}🔐 GitHub Secrets 설정...${NC}"
gh secret list | grep -q "REGISTRY_URL" || gh secret set REGISTRY_URL -b "${REGISTRY}"
gh secret list | grep -q "REGISTRY_USERNAME" || gh secret set REGISTRY_USERNAME -b "admin"
echo -e "${GREEN}✅ Registry secrets 설정 완료${NC}"

# GitHub Variables 설정 (수동 설정 필요)
echo -e "${YELLOW}📝 GitHub Variables 설정 안내${NC}"
echo "GitHub에서 다음 Variables를 수동으로 설정하세요:"
echo "  - GITHUB_ORG: ${GITHUB_ORG}"
echo "  - APP_NAME: ${APP_NAME}" 
echo "  - NAMESPACE: ${NAMESPACE}"
echo "  - REGISTRY_URL: ${REGISTRY}"
echo "  - ORG: ${GITHUB_ORG}"
echo "  - ARGOCD_URL: https://argo.jclee.me"
echo "설정 방법: Settings → Secrets and variables → Actions → Variables"
echo -e "${GREEN}✅ Variables 설정 안내 완료${NC}"

# Helm Chart 생성
echo -e "${YELLOW}📊 Helm Chart 생성...${NC}"
mkdir -p charts/${APP_NAME}/templates

cat > charts/${APP_NAME}/Chart.yaml << EOF
apiVersion: v2
name: ${APP_NAME}
description: SafeWork Pro - 건설업 보건관리 시스템
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - safework
  - health-management
  - construction
home: https://github.com/${GITHUB_ORG}/${APP_NAME}
sources:
  - https://github.com/${GITHUB_ORG}/${APP_NAME}
maintainers:
  - name: SafeWork Team
    email: admin@jclee.me
EOF

cat > charts/${APP_NAME}/values.yaml << EOF
replicaCount: 1

image:
  repository: ${REGISTRY}/${APP_NAME}
  pullPolicy: Always
  tag: "latest"

imagePullSecrets:
  - name: regcred

nameOverride: ""
fullnameOverride: ""

service:
  type: NodePort
  port: 3001
  nodePort: 32301

ingress:
  enabled: true
  className: "traefik"
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
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
    cpu: 1000m
    memory: 1024Mi
  requests:
    cpu: 200m
    memory: 512Mi

env:
  - name: ENVIRONMENT
    value: "production"
  - name: HOST
    value: "0.0.0.0"
  - name: PORT
    value: "3001"
  - name: DATABASE_URL
    value: "postgresql://admin:password@localhost:5432/health_management"
  - name: REDIS_URL
    value: "redis://localhost:6379/0"
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: safework-secrets
        key: jwt-secret
  - name: LOG_LEVEL
    value: "INFO"
  - name: TZ
    value: "Asia/Seoul"

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 3
  targetCPUUtilizationPercentage: 80

nodeSelector: {}
tolerations: []
affinity: {}

probes:
  liveness:
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 120
    periodSeconds: 30
    timeoutSeconds: 10
    failureThreshold: 3
  readiness:
    httpGet:
      path: /health
      port: 3001
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
EOF

cat > charts/${APP_NAME}/templates/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "safework.fullname" . }}
  labels:
    {{- include "safework.labels" . | nindent 4 }}
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
      labels:
        {{- include "safework.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.env | map (dict "name" "PORT") | first | default (dict "value" "3001") | pluck "value" | first }}
          protocol: TCP
        env:
        {{- toYaml .Values.env | nindent 8 }}
        livenessProbe:
          {{- toYaml .Values.probes.liveness | nindent 10 }}
        readinessProbe:
          {{- toYaml .Values.probes.readiness | nindent 10 }}
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
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
    {{- if and (eq .Values.service.type "NodePort") .Values.service.nodePort }}
    nodePort: {{ .Values.service.nodePort }}
    {{- end }}
  selector:
    {{- include "safework.selectorLabels" . | nindent 4 }}
EOF

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

cat > charts/${APP_NAME}/templates/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "safework.fullname" . }}-config
  labels:
    {{- include "safework.labels" . | nindent 4 }}
data:
  app-config.yaml: |
    environment: {{ .Values.env | map (dict "name" "ENVIRONMENT") | first | default (dict "value" "production") | pluck "value" | first }}
    log_level: {{ .Values.env | map (dict "name" "LOG_LEVEL") | first | default (dict "value" "INFO") | pluck "value" | first }}
EOF

echo -e "${GREEN}✅ Helm Chart 생성 완료${NC}"

# GitHub Actions 워크플로우 업데이트
echo -e "${YELLOW}🔧 GitHub Actions 워크플로우 생성...${NC}"
mkdir -p .github/workflows

cat > .github/workflows/gitops-deploy.yml << 'EOF'
# SafeWork GitOps CI/CD Pipeline
name: GitOps CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ${{ vars.REGISTRY_URL }}
  IMAGE_NAME: ${{ vars.APP_NAME }}

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  validate:
    name: Validate
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Validate Helm Chart
        run: |
          curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
          helm lint ./charts/${{ vars.APP_NAME }}

  build:
    name: Build and Push
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name != 'pull_request'
    timeout-minutes: 20
    
    outputs:
      version: ${{ steps.version.outputs.version }}
      image-tag: ${{ steps.meta.outputs.version }}
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Generate Version
        id: version
        run: |
          if [[ "${{ github.ref }}" == refs/tags/* ]]; then
            VERSION="${{ github.ref_name }}"
            VERSION=${VERSION#v}
          else
            VERSION="0.1.0-${{ github.run_number }}"
          fi
          echo "version=${VERSION}" >> $GITHUB_OUTPUT
          
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
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
            type=raw,value={{branch}}-{{date 'YYYYMMDD'}}-{{sha}}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./deployment/Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
          platforms: linux/amd64

  deploy-helm:
    name: Deploy Helm Chart
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name != 'pull_request'
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Install Helm
        uses: azure/setup-helm@v3
        with:
          version: 'v3.13.0'
          
      - name: Update Chart Version
        run: |
          # Update Chart.yaml
          sed -i "s/^version:.*/version: ${{ needs.build.outputs.version }}/" ./charts/${{ vars.APP_NAME }}/Chart.yaml
          sed -i "s/^appVersion:.*/appVersion: \"${{ needs.build.outputs.version }}\"/" ./charts/${{ vars.APP_NAME }}/Chart.yaml
          
          # Update values.yaml with new image tag
          sed -i "s/tag:.*/tag: \"${{ needs.build.outputs.image-tag }}\"/" ./charts/${{ vars.APP_NAME }}/values.yaml
          
      - name: Package Helm Chart
        run: |
          helm package ./charts/${{ vars.APP_NAME }}
          
      - name: Push to ChartMuseum
        if: vars.CHARTMUSEUM_URL != ''
        run: |
          CHART_FILE="${{ vars.APP_NAME }}-${{ needs.build.outputs.version }}.tgz"
          
          # Upload with authentication
          RESPONSE=$(curl -s -w "\n%{http_code}" \
            -u ${{ secrets.CHARTMUSEUM_USERNAME }}:${{ secrets.CHARTMUSEUM_PASSWORD }} \
            --data-binary "@${CHART_FILE}" \
            ${{ vars.CHARTMUSEUM_URL }}/api/charts)
          
          HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
          BODY=$(echo "$RESPONSE" | head -n-1)
          
          if [ "$HTTP_CODE" -eq 201 ] || [ "$HTTP_CODE" -eq 200 ]; then
            echo "✅ Chart uploaded successfully: ${{ needs.build.outputs.version }}"
          else
            echo "❌ Chart upload failed with HTTP $HTTP_CODE"
            echo "Response: $BODY"
            exit 1
          fi

  deploy-status:
    name: Deployment Status
    runs-on: ubuntu-latest
    needs: [build, deploy-helm]
    if: always()
    timeout-minutes: 5
    
    steps:
      - name: Summary
        run: |
          echo "## 🚀 Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          if [[ "${{ needs.build.result }}" == "success" ]]; then
            echo "### ✅ Build Success" >> $GITHUB_STEP_SUMMARY
            echo "- Version: \`${{ needs.build.outputs.version }}\`" >> $GITHUB_STEP_SUMMARY
            echo "- Image: \`${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.image-tag }}\`" >> $GITHUB_STEP_SUMMARY
          else
            echo "### ❌ Build Failed" >> $GITHUB_STEP_SUMMARY
          fi
          
          echo "" >> $GITHUB_STEP_SUMMARY
          
          if [[ "${{ needs.deploy-helm.result }}" == "success" ]]; then
            echo "### ✅ Helm Chart Deployed" >> $GITHUB_STEP_SUMMARY
            echo "- Chart Version: \`${{ needs.build.outputs.version }}\`" >> $GITHUB_STEP_SUMMARY
            echo "- ArgoCD will automatically sync the new version" >> $GITHUB_STEP_SUMMARY
          else
            echo "### ⚠️ Helm Deployment Skipped" >> $GITHUB_STEP_SUMMARY
          fi
          
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### 📊 Links" >> $GITHUB_STEP_SUMMARY
          echo "- [ArgoCD Dashboard](${{ vars.ARGOCD_URL }}/applications/${{ vars.APP_NAME }})" >> $GITHUB_STEP_SUMMARY
          echo "- [Production URL](https://${{ vars.APP_NAME }}.jclee.me)" >> $GITHUB_STEP_SUMMARY
EOF

echo -e "${GREEN}✅ GitHub Actions 워크플로우 생성 완료${NC}"

# ArgoCD Application 생성
echo -e "${YELLOW}🚢 ArgoCD Application 설정...${NC}"
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
          tag: "latest"
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
    - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
EOF

echo -e "${GREEN}✅ ArgoCD Application 설정 완료${NC}"

# 실행 확인
echo ""
echo -e "${GREEN}🎉 GitOps CI/CD 구축 완료!${NC}"
echo ""
echo "다음 단계:"
echo "1. Kubernetes secrets 생성:"
echo "   kubectl create secret generic safework-secrets --from-literal=jwt-secret='your-secret' -n ${NAMESPACE}"
echo ""
echo "2. ArgoCD Application 생성:"
echo "   kubectl apply -f argocd-application.yaml"
echo ""
echo "3. 변경사항 커밋 및 푸시:"
echo "   git add ."
echo "   git commit -m 'feat: GitOps CI/CD 파이프라인 구성'"
echo "   git push origin main"
echo ""
echo "4. 배포 확인:"
echo "   - GitHub Actions: https://github.com/${GITHUB_ORG}/${APP_NAME}/actions"
echo "   - ArgoCD: https://argo.jclee.me/applications/${APP_NAME}"
echo "   - Application: https://safework.jclee.me"