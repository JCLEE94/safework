#!/bin/bash

echo "🔧 ArgoCD Image Updater 설정 중..."

# ArgoCD 애플리케이션에 Image Updater annotations 추가
argocd app patch safework --patch '[
  {
    "op": "add",
    "path": "/metadata/annotations",
    "value": {
      "argocd-image-updater.argoproj.io/image-list": "safework=registry.jclee.me/safework:latest",
      "argocd-image-updater.argoproj.io/safework.allow-tags": "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$",
      "argocd-image-updater.argoproj.io/safework.update-strategy": "latest",
      "argocd-image-updater.argoproj.io/safework.helm.image-name": "image.repository",
      "argocd-image-updater.argoproj.io/safework.helm.image-tag": "image.tag",
      "argocd-image-updater.argoproj.io/write-back-method": "git",
      "argocd-image-updater.argoproj.io/git-branch": "main"
    }
  }
]' --type json

echo "✅ ArgoCD Image Updater 설정 완료!"
echo "📊 애플리케이션 상태:"
argocd app get safework