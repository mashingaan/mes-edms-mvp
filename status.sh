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

section "NGINX SSL CONFIGURATION"
echo ""
echo -e "${YELLOW}Checking for SSL directives in Nginx config:${NC}"
echo ""

NGINX_T_CMD="nginx -T"
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        NGINX_T_CMD="sudo nginx -T"
    else
        echo -e "${YELLOW}WARN: nginx -T may require root; run this script with sudo for full output.${NC}"
    fi
fi

if $NGINX_T_CMD 2>/dev/null | grep -q "listen 443"; then
    echo -e "${GREEN}OK Port 443 (HTTPS) is configured${NC}"

    echo ""
    echo "SSL certificates in use:"
    $NGINX_T_CMD 2>/dev/null | grep -E "ssl_certificate " | grep -v "ssl_certificate_key" | sed 's/^[[:space:]]*/  /'

    echo ""
    echo "SSL certificate keys:"
    $NGINX_T_CMD 2>/dev/null | grep "ssl_certificate_key" | sed 's/^[[:space:]]*/  /'

    echo ""
    echo "HTTP to HTTPS redirects:"
    $NGINX_T_CMD 2>/dev/null | grep -B 2 "return 301 https" | grep -E "(server_name|return 301)" | sed 's/^[[:space:]]*/  /'
else
    echo -e "${YELLOW}WARN Port 443 (HTTPS) is NOT configured in Nginx${NC}"
    echo "  This means SSL is not active. Run deploy.sh to configure SSL."
fi

section "SSL CERTIFICATES"
certbot certificates

section "SSL CERTIFICATE VALIDATION"
echo ""

for domain in inspro-mes.ru api.inspro-mes.ru; do
    echo -e "${YELLOW}Validating SSL for $domain (local nginx):${NC}"

    if command -v openssl &> /dev/null; then
        if command -v timeout &> /dev/null; then
            cert_info=$(timeout 10 openssl s_client -servername "$domain" -connect 127.0.0.1:443 </dev/null 2>&1 || true)
        else
            cert_info=$(openssl s_client -servername "$domain" -connect 127.0.0.1:443 </dev/null 2>&1 || true)
        fi

        if echo "$cert_info" | grep -q "Verify return code:"; then
            if echo "$cert_info" | grep -q "Verify return code: 0"; then
                echo -e "  ${GREEN}OK Certificate is valid${NC}"
            else
                echo -e "  ${YELLOW}WARN Certificate verification failed${NC}"
                echo "$cert_info" | grep -i "Verify return code" | sed 's/^/    /' || true
            fi
        elif echo "$cert_info" | grep -q "Verification: OK"; then
            echo -e "  ${GREEN}OK Certificate is valid${NC}"
        elif echo "$cert_info" | grep -qi "certificate verify failed"; then
            echo -e "  ${YELLOW}WARN Certificate verification failed${NC}"
            echo "$cert_info" | grep -i "verify" | sed 's/^/    /' || true
        elif echo "$cert_info" | grep -qi "Connection refused\|timeout"; then
            echo -e "  ${YELLOW}WARN Cannot connect to port 443${NC}"
        else
            echo -e "  ${YELLOW}WARN SSL check inconclusive${NC}"
            echo "$cert_info" | grep -i "Verify return code\|Verification" | sed 's/^/    /' || true
        fi

        # Show expiration date (NOTE: can be optimized to reuse a single s_client call)
        if command -v timeout &> /dev/null; then
            expiry=$(timeout 10 openssl s_client -servername "$domain" -connect 127.0.0.1:443 </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep "notAfter" || true)
        else
            expiry=$(openssl s_client -servername "$domain" -connect 127.0.0.1:443 </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep "notAfter" || true)
        fi
        if [ -n "$expiry" ]; then
            echo "  $expiry"
        fi
    else
        echo "  SSL validation skipped: openssl missing"
    fi
    echo ""
done

section "HEALTH CHECKS (LOCAL)"
echo ""

for endpoint in "Frontend:https://inspro-mes.ru" "API Docs:https://api.inspro-mes.ru/docs" "API Health:https://api.inspro-mes.ru/health"; do
    label=$(echo "$endpoint" | cut -d: -f1)
    url=$(echo "$endpoint" | cut -d: -f2-)

    echo -e "${YELLOW}$label ($url):${NC}"

    resolve_args=""
    if echo "$url" | grep -q "https://inspro-mes.ru"; then
        resolve_args="--resolve inspro-mes.ru:443:127.0.0.1"
    elif echo "$url" | grep -q "https://api.inspro-mes.ru"; then
        resolve_args="--resolve api.inspro-mes.ru:443:127.0.0.1"
    fi

    response=$(curl -sI $resolve_args -w "\n%{http_code}|%{ssl_verify_result}|%{time_total}" "$url" 2>&1 || echo "CURL_FAILED")

    if echo "$response" | grep -q "CURL_FAILED"; then
        echo -e "  ${YELLOW}WARN Connection failed${NC}"
        echo "  Run: curl -vI $resolve_args $url"
    else
        http_code=$(echo "$response" | tail -n 1 | cut -d'|' -f1)
        ssl_verify=$(echo "$response" | tail -n 1 | cut -d'|' -f2)
        time_total=$(echo "$response" | tail -n 1 | cut -d'|' -f3)

        if [ "$http_code" = "200" ] || [ "$http_code" = "301" ] || [ "$http_code" = "302" ]; then
            echo -e "  ${GREEN}OK HTTP $http_code${NC} (${time_total}s)"
        else
            echo -e "  ${YELLOW}WARN HTTP $http_code${NC}"
        fi

        if [ "$ssl_verify" = "0" ]; then
            echo -e "  ${GREEN}OK SSL verification passed${NC}"
        else
            echo -e "  ${YELLOW}WARN SSL verification failed (code: $ssl_verify)${NC}"
        fi
    fi
    echo ""
done

section "HEALTH CHECKS (PUBLIC)"
echo ""

for endpoint in "Frontend:https://inspro-mes.ru" "API Docs:https://api.inspro-mes.ru/docs" "API Health:https://api.inspro-mes.ru/health"; do
    label=$(echo "$endpoint" | cut -d: -f1)
    url=$(echo "$endpoint" | cut -d: -f2-)

    echo -e "${YELLOW}$label ($url):${NC}"

    response=$(curl -sI -w "\n%{http_code}|%{ssl_verify_result}|%{time_total}" "$url" 2>&1 || echo "CURL_FAILED")

    if echo "$response" | grep -q "CURL_FAILED"; then
        echo -e "  ${YELLOW}WARN Connection failed${NC}"
        echo "  Run: curl -vI $url"
    else
        http_code=$(echo "$response" | tail -n 1 | cut -d'|' -f1)
        ssl_verify=$(echo "$response" | tail -n 1 | cut -d'|' -f2)
        time_total=$(echo "$response" | tail -n 1 | cut -d'|' -f3)

        if [ "$http_code" = "200" ] || [ "$http_code" = "301" ] || [ "$http_code" = "302" ]; then
            echo -e "  ${GREEN}OK HTTP $http_code${NC} (${time_total}s)"
        else
            echo -e "  ${YELLOW}WARN HTTP $http_code${NC}"
        fi

        if [ "$ssl_verify" = "0" ]; then
            echo -e "  ${GREEN}OK SSL verification passed${NC}"
        else
            echo -e "  ${YELLOW}WARN SSL verification failed (code: $ssl_verify)${NC}"
        fi
    fi
    echo ""
done

section "DISK USAGE (Docker Volumes)"
docker system df -v | grep -A 20 "Local Volumes"

echo ""
echo -e "${GREEN}Status check complete.${NC}"
