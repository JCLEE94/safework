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