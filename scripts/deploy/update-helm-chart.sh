#!/bin/bash
set -e

echo "📦 Helm Chart 업데이트 스크립트"
echo "================================="

APP_NAME="safework"
CHART_PATH="./charts/${APP_NAME}"

if [ ! -d "$CHART_PATH" ]; then
    echo "❌ Helm Chart 경로를 찾을 수 없습니다: $CHART_PATH"
    exit 1
fi

echo "🔧 Helm Chart 검증..."
helm lint $CHART_PATH

echo "📋 Chart.yaml 정보:"
cat $CHART_PATH/Chart.yaml | grep -E "^(name|version|appVersion):"

echo "🎯 values.yaml 주요 설정:"
echo "  Image Repository: $(grep -E "^  repository:" $CHART_PATH/values.yaml | awk '{print $2}')"
echo "  Replica Count: $(grep -E "^replicaCount:" $CHART_PATH/values.yaml | awk '{print $2}')"
echo "  Service Type: $(grep -E "^  type:" $CHART_PATH/values.yaml | awk '{print $2}')"
echo "  Node Port: $(grep -E "^  nodePort:" $CHART_PATH/values.yaml | awk '{print $2}')"

echo "✅ Helm Chart 업데이트 완료"