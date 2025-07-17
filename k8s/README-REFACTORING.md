# K8s 구조 리팩토링 계획

## 현재 구조 문제점
- 중복된 디렉토리 구조 (safework, safework-with-cloudflare, argocd 등)
- 분산된 설정 파일들
- 명확하지 않은 환경 분리 (dev/staging/prod)

## 개선된 구조
```
k8s/
├── base/                    # Kustomize 기본 리소스
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   └── kustomization.yaml
├── overlays/                # 환경별 설정
│   ├── development/
│   ├── staging/
│   └── production/
├── argocd/                  # ArgoCD 애플리케이션 정의
│   └── applications/
└── scripts/                 # 배포 스크립트
```

## 작업 단계
1. 기존 파일 백업
2. 새 구조로 재구성
3. Kustomize 기반 환경 분리
4. ArgoCD 애플리케이션 업데이트
5. 문서화 및 검증