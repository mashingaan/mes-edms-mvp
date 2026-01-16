#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

cd /opt/mes-edms-mvp || exit 1

section "DOCKER COMPOSE SERVICES"
docker compose ps

section "BACKEND LOGS (Last 50 lines)"
docker compose logs --tail=50 backend

section "NGINX STATUS"
systemctl status nginx --no-pager

section "NGINX CONFIGURATION TEST"
nginx -t

section "SSL CERTIFICATES"
certbot certificates

section "HEALTH CHECKS"
echo ""
echo -e "${YELLOW}Frontend (https://inspro-mes.ru):${NC}"
curl -I https://inspro-mes.ru 2>&1 | head -n 1

echo ""
echo -e "${YELLOW}API Docs (https://api.inspro-mes.ru/docs):${NC}"
curl -I https://api.inspro-mes.ru/docs 2>&1 | head -n 1

echo ""
echo -e "${YELLOW}API Health (https://api.inspro-mes.ru/health):${NC}"
curl -I https://api.inspro-mes.ru/health 2>&1 | head -n 1 || echo "Health endpoint may not exist"

section "DISK USAGE (Docker Volumes)"
docker system df -v | grep -A 20 "Local Volumes"

echo ""
echo -e "${GREEN}Status check complete.${NC}"
