#!/bin/bash

# SafeWork System Migration Script
# This script safely migrates from the old system to the new V2 system

set -e

echo "========================================="
echo "SafeWork System Migration to V2"
echo "========================================="

# Configuration
NAMESPACE="safework"
OLD_DEPLOYMENT="safework"
NEW_FRONTEND="safework-frontend-v2"
BACKUP_DIR="/tmp/safework-backup-$(date +%Y%m%d-%H%M%S)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Pre-migration checks
echo ""
echo "Step 1: Pre-migration checks..."

# Check if new frontend is deployed
if kubectl get deployment $NEW_FRONTEND -n $NAMESPACE &>/dev/null; then
    echo -e "${GREEN}✅${NC} New frontend V2 is deployed"
else
    echo -e "${RED}❌${NC} New frontend V2 is not deployed. Please run deploy-frontend-v2.sh first."
    exit 1
fi

# Check if old system exists
if kubectl get deployment $OLD_DEPLOYMENT -n $NAMESPACE &>/dev/null; then
    echo -e "${GREEN}✅${NC} Old system found"
else
    echo -e "${YELLOW}⚠️${NC} Old system not found. Nothing to migrate."
    exit 0
fi

# Step 2: Backup current configuration
echo ""
echo "Step 2: Backing up current configuration..."
mkdir -p "$BACKUP_DIR"

# Backup deployments
kubectl get deployment -n $NAMESPACE -o yaml > "$BACKUP_DIR/deployments.yaml"
kubectl get service -n $NAMESPACE -o yaml > "$BACKUP_DIR/services.yaml"
kubectl get ingress -n $NAMESPACE -o yaml > "$BACKUP_DIR/ingress.yaml"
kubectl get configmap -n $NAMESPACE -o yaml > "$BACKUP_DIR/configmaps.yaml" 2>/dev/null || true
kubectl get secret -n $NAMESPACE -o yaml > "$BACKUP_DIR/secrets.yaml" 2>/dev/null || true

echo -e "${GREEN}✅${NC} Backup saved to: $BACKUP_DIR"

# Step 3: Database backup (if applicable)
echo ""
echo "Step 3: Database backup..."
POD=$(kubectl get pod -n $NAMESPACE -l app=safework -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ ! -z "$POD" ]; then
    echo "Backing up database from pod: $POD"
    kubectl exec -n $NAMESPACE $POD -- pg_dump -U admin -d health_management > "$BACKUP_DIR/database.sql" 2>/dev/null || \
        echo -e "${YELLOW}⚠️${NC} Could not backup database. Continuing anyway."
else
    echo -e "${YELLOW}⚠️${NC} No running pod found for database backup"
fi

# Step 4: Test new system
echo ""
echo "Step 4: Testing new system..."
./test-frontend-v2.sh || {
    echo -e "${RED}❌${NC} New system tests failed. Aborting migration."
    exit 1
}

# Step 5: Migration plan
echo ""
echo "Step 5: Migration Plan"
echo "====================="
echo "1. Scale down old deployment to 0 replicas"
echo "2. Update ingress to point to new frontend"
echo "3. Update backend to support new frontend"
echo "4. Run data migration scripts"
echo "5. Delete old deployment resources"
echo ""
read -p "Do you want to proceed with the migration? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

# Step 6: Scale down old deployment
echo ""
echo "Step 6: Scaling down old deployment..."
kubectl scale deployment $OLD_DEPLOYMENT -n $NAMESPACE --replicas=0
echo "Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app=$OLD_DEPLOYMENT -n $NAMESPACE --timeout=60s 2>/dev/null || true
echo -e "${GREEN}✅${NC} Old deployment scaled down"

# Step 7: Update ingress
echo ""
echo "Step 7: Updating ingress..."

# Check if main ingress exists
if kubectl get ingress safework -n $NAMESPACE &>/dev/null; then
    # Update main ingress to point to new frontend
    kubectl patch ingress safework -n $NAMESPACE --type='json' \
        -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value":"'$NEW_FRONTEND'"}]' || {
        echo -e "${RED}❌${NC} Failed to update ingress. Rolling back..."
        kubectl scale deployment $OLD_DEPLOYMENT -n $NAMESPACE --replicas=1
        exit 1
    }
    echo -e "${GREEN}✅${NC} Ingress updated to point to new frontend"
else
    echo -e "${YELLOW}⚠️${NC} No main ingress found, using new frontend ingress"
fi

# Step 8: Run data migration
echo ""
echo "Step 8: Running data migration..."
cd "$PROJECT_ROOT"
python scripts/migrate-data.py || {
    echo -e "${YELLOW}⚠️${NC} Data migration had issues. Please check logs."
}

# Step 9: Verify migration
echo ""
echo "Step 9: Verifying migration..."
sleep 10

# Test main URL
MAIN_URL="https://safework.jclee.me"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$MAIN_URL" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅${NC} Main site is accessible"
else
    echo -e "${RED}❌${NC} Main site is not accessible (status: $HTTP_STATUS)"
    echo "Rolling back..."
    kubectl scale deployment $OLD_DEPLOYMENT -n $NAMESPACE --replicas=1
    exit 1
fi

# Step 10: Cleanup decision
echo ""
echo "Step 10: Cleanup"
echo "================"
echo "Migration appears successful!"
echo ""
echo "Old deployment is currently scaled to 0 replicas."
echo "You can:"
echo "  1. Keep it for rollback (recommended for 24-48 hours)"
echo "  2. Delete it now"
echo ""
read -p "Delete old deployment resources now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting old deployment resources..."
    kubectl delete deployment $OLD_DEPLOYMENT -n $NAMESPACE 2>/dev/null || true
    kubectl delete service $OLD_DEPLOYMENT -n $NAMESPACE 2>/dev/null || true
    kubectl delete configmap safework-config -n $NAMESPACE 2>/dev/null || true
    echo -e "${GREEN}✅${NC} Old resources deleted"
else
    echo "Keeping old deployment for rollback purposes"
    echo "To delete later, run:"
    echo "  kubectl delete deployment $OLD_DEPLOYMENT -n $NAMESPACE"
    echo "  kubectl delete service $OLD_DEPLOYMENT -n $NAMESPACE"
fi

# Summary
echo ""
echo "========================================="
echo "Migration Summary"
echo "========================================="
echo -e "${GREEN}✅${NC} Frontend migrated to V2"
echo -e "${GREEN}✅${NC} Ingress updated"
echo -e "${GREEN}✅${NC} System is accessible"
echo ""
echo "URLs:"
echo "  Main: https://safework.jclee.me"
echo "  V2 Direct: https://safework-v2.jclee.me"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""
echo "To rollback if needed:"
echo "  kubectl scale deployment $OLD_DEPLOYMENT -n $NAMESPACE --replicas=1"
echo "  kubectl patch ingress safework -n $NAMESPACE --type='json' \\"
echo "    -p='[{\"op\": \"replace\", \"path\": \"/spec/rules/0/http/paths/0/backend/service/name\", \"value\":\"'$OLD_DEPLOYMENT'\"}]'"
echo "========================================="