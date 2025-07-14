# ArgoCD Configuration Guide for SafeWork

## 접속 정보
- **URL**: https://argo.jclee.me
- **Username**: admin
- **Password**: bingogo1

## 1. ArgoCD Web UI를 통한 설정

### Step 1: 로그인
1. 브라우저에서 https://argo.jclee.me 접속
2. Username: `admin`, Password: `bingogo1` 입력

### Step 2: Repository 등록 (이미 완료됨)
- Repository URL: https://github.com/JCLEE94/safework.git
- Username: JCLEE94
- Password: GitHub Token

### Step 3: Application 생성/확인

#### 기존 앱이 있는 경우
1. Applications 메뉴에서 `safework` 찾기
2. 앱 클릭하여 상태 확인

#### 새로 생성하는 경우
1. **NEW APP** 버튼 클릭
2. 다음 정보 입력:

**General**
- Application Name: `safework`
- Project: `default`
- Sync Policy: `Automatic`
  - ✅ Prune Resources
  - ✅ Self Heal

**Source**
- Repository URL: `https://github.com/JCLEE94/safework.git`
- Revision: `main`
- Path: `k8s/safework`

**Destination**
- Cluster URL: `https://kubernetes.default.svc`
- Namespace: `safework`

**Sync Options**
- ✅ Auto-Create Namespace
- ✅ Server Side Apply
- ✅ Prune Last

### Step 4: Image Updater Annotations 추가

앱 생성 후 YAML 편집 모드로 전환하여 metadata.annotations에 다음 추가:

```yaml
metadata:
  annotations:
    argocd-image-updater.argoproj.io/image-list: safework=registry.jclee.me/safework:latest
    argocd-image-updater.argoproj.io/safework.update-strategy: latest
    argocd-image-updater.argoproj.io/safework.allow-tags: "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$"
    argocd-image-updater.argoproj.io/write-back-method: git
    argocd-image-updater.argoproj.io/git-branch: main
```

### Step 5: Sync 실행
1. **SYNC** 버튼 클릭
2. Synchronize 창에서:
   - Revision: `main`
   - ✅ Prune
   - ✅ Dry Run (먼저 테스트)
3. **SYNCHRONIZE** 클릭

## 2. ArgoCD Image Updater 설정 확인

### Image Updater 설치 확인
```bash
# ArgoCD namespace에서 확인
kubectl get deployment -n argocd | grep image-updater
```

### Image Updater 설치 (필요한 경우)
```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml
```

### Registry Secret 생성
```bash
kubectl create secret docker-registry regcred \
  --docker-server=registry.jclee.me \
  --docker-username=qws9411 \
  --docker-password=bingogo1 \
  --docker-email=qws9411@example.com \
  -n argocd
```

### Image Updater ConfigMap 설정
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-image-updater-config
  namespace: argocd
data:
  registries.conf: |
    registries:
    - name: registry.jclee.me
      api_url: https://registry.jclee.me
      credentials: secret:argocd/regcred
      defaultns: library
      insecure: no
EOF
```

## 3. 문제 해결

### Kustomization 오류 해결
만약 "Kustomization not found" 오류가 발생하면:

1. k8s/safework/kustomization.yaml 파일 생성:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - namespace.yaml
  - secrets.yaml
  - regcred.yaml
  - postgres.yaml
  - redis.yaml
  - deployment.yaml
  - service.yaml
```

2. Git에 커밋 및 푸시:
```bash
git add k8s/safework/kustomization.yaml
git commit -m "feat: add kustomization.yaml for ArgoCD"
git push
```

### Manual Sync
자동 동기화가 작동하지 않으면:
1. ArgoCD UI에서 앱 선택
2. **REFRESH** 클릭
3. **SYNC** 클릭
4. 특정 리소스만 선택하여 동기화 가능

## 4. 모니터링

### Application 상태 확인
- **Healthy**: 모든 리소스가 정상 실행 중
- **Progressing**: 배포 진행 중
- **Degraded**: 일부 리소스에 문제 발생
- **Missing**: 리소스가 클러스터에 없음

### Image Updater 로그 확인
```bash
kubectl logs -n argocd deployment/argocd-image-updater -f
```

### 배포 확인
```bash
# Pod 상태 확인
kubectl get pods -n safework

# Service 확인
kubectl get svc -n safework

# 로그 확인
kubectl logs -n safework deployment/safework
```

## 5. CI/CD 파이프라인과 연동

### GitHub Actions에서 이미지 푸시 후
1. Image Updater가 자동으로 새 이미지 감지 (2-5분 소요)
2. Git repository에 이미지 태그 업데이트 커밋
3. ArgoCD가 Git 변경사항 감지하고 자동 배포

### 수동 이미지 업데이트 트리거
```bash
kubectl annotate app safework -n argocd \
  argocd-image-updater.argoproj.io/force-update="true" --overwrite
```

## 6. 접근 URL

배포 완료 후:
- **Application**: https://safework.jclee.me
- **Health Check**: https://safework.jclee.me/health
- **API Docs**: https://safework.jclee.me/api/docs

---

**Note**: 현재 Docker 이미지가 registry에 푸시되지 않아 배포가 대기 중입니다. GitHub Actions에 Registry 인증 정보를 추가하면 자동으로 배포가 시작됩니다.