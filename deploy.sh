#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

ssl_certs_exist() {
    CERT_DIR_MAIN=/etc/letsencrypt/live/inspro-mes.ru
    CERT_DIR_API=/etc/letsencrypt/live/api.inspro-mes.ru

    if [ -z "${CERTBOT_CERTS_CACHE:-}" ]; then
        CERTBOT_CERTS_CACHE="$(certbot certificates 2>/dev/null || true)"
    fi

    if [ -n "$CERTBOT_CERTS_CACHE" ]; then
        if [ "${CERTBOT_CERTS_LOGGED:-0}" -eq 0 ]; then
            CERTBOT_DOMAINS="$(echo "$CERTBOT_CERTS_CACHE" | awk -F: '/Domains:/ {print $2}' | xargs)"
            if [ -n "$CERTBOT_DOMAINS" ]; then
                log "certbot sees certificates for: $CERTBOT_DOMAINS"
            fi
            CERTBOT_CERTS_LOGGED=1
        fi

        cert_main=""
        cert_api=""
        current_cert=""
        while IFS= read -r line; do
            case "$line" in
                *"Certificate Name:"*)
                    current_cert="$(echo "$line" | awk '{print $3}')"
                    ;;
                *"Domains:"*)
                    if echo "$line" | grep -qw "inspro-mes.ru"; then
                        cert_main="$current_cert"
                    fi
                    if echo "$line" | grep -qw "api.inspro-mes.ru"; then
                        cert_api="$current_cert"
                    fi
                    ;;
            esac
        done <<< "$CERTBOT_CERTS_CACHE"

        if [ -n "$cert_main" ]; then
            CERT_DIR_MAIN="/etc/letsencrypt/live/$cert_main"
            CERT_DIR_API_EFFECTIVE="$CERT_DIR_MAIN"
            if [ -n "$cert_api" ]; then
                CERT_DIR_API_EFFECTIVE="/etc/letsencrypt/live/$cert_api"
            fi

            if [ -f "$CERT_DIR_MAIN/fullchain.pem" ] && [ -f "$CERT_DIR_MAIN/privkey.pem" ]; then
                if [ "$CERT_DIR_API_EFFECTIVE" = "$CERT_DIR_MAIN" ]; then
                    return 0
                fi
                if [ -f "$CERT_DIR_API_EFFECTIVE/fullchain.pem" ] && [ -f "$CERT_DIR_API_EFFECTIVE/privkey.pem" ]; then
                    return 0
                fi
            fi
            return 1
        fi
    fi

    main_ok=0
    api_ok=0

    if [ -f "$CERT_DIR_MAIN/fullchain.pem" ] && [ -f "$CERT_DIR_MAIN/privkey.pem" ]; then
        main_ok=1
    fi
    if [ -f "$CERT_DIR_API/fullchain.pem" ] && [ -f "$CERT_DIR_API/privkey.pem" ]; then
        api_ok=1
    fi

    if [ "$main_ok" -ne 1 ]; then
        return 1
    fi

    if [ -d "$CERT_DIR_API" ] && [ "$api_ok" -ne 1 ]; then
        return 1
    fi

    CERT_DIR_API_EFFECTIVE="$CERT_DIR_MAIN"
    if [ "$api_ok" -eq 1 ]; then
        CERT_DIR_API_EFFECTIVE="$CERT_DIR_API"
    fi

    return 0
}

reload_nginx() {
    if command -v systemctl &> /dev/null && systemctl is-active --quiet nginx; then
        systemctl reload nginx
        return $?
    fi

    if command -v nginx &> /dev/null; then
        nginx -s reload
        return $?
    fi

    return 1
}

generate_nginx_config() {
    if ssl_certs_exist; then
        log "Generating HTTPS-ready Nginx configuration..."

        SSL_CERTBOT_SNIPPET=""
        if [ -f /etc/letsencrypt/options-ssl-nginx.conf ] && [ -f /etc/letsencrypt/ssl-dhparams.pem ]; then
            SSL_CERTBOT_SNIPPET="    include /etc/letsencrypt/options-ssl-nginx.conf;\n    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;"
        else
            SSL_CERTBOT_SNIPPET="    ssl_protocols TLSv1.2 TLSv1.3;\n    ssl_ciphers HIGH:!aNULL:!MD5;"
        fi

        cat > /etc/nginx/sites-available/inspro-mes <<EOF
server {
    listen 80;
    server_name inspro-mes.ru;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name inspro-mes.ru;

    ssl_certificate $CERT_DIR_MAIN/fullchain.pem;
    ssl_certificate_key $CERT_DIR_MAIN/privkey.pem;
$(echo -e "$SSL_CERTBOT_SNIPPET")

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}

server {
    listen 80;
    server_name api.inspro-mes.ru;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.inspro-mes.ru;

    ssl_certificate $CERT_DIR_API_EFFECTIVE/fullchain.pem;
    ssl_certificate_key $CERT_DIR_API_EFFECTIVE/privkey.pem;
$(echo -e "$SSL_CERTBOT_SNIPPET")

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    else
        log "Generating HTTP-only Nginx configuration..."

        cat > /etc/nginx/sites-available/inspro-mes <<'EOF'
server {
    listen 80;
    server_name inspro-mes.ru;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 80;
    server_name api.inspro-mes.ru;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    fi
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root"
    exit 1
fi

log "Starting deployment of MES-EDMS MVP..."

# Step 1: Update system and install dependencies
log "Step 1: Installing system dependencies..."
apt-get update -qq

# Install basic tools
apt-get install -y curl git ufw nginx certbot python3-certbot-nginx openssl ca-certificates gnupg lsb-release

# Step 2: Install Docker (official repository, not snap)
log "Step 2: Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Remove snap docker if exists
    snap remove docker 2>/dev/null || true
    
    # Add Docker's official GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update -qq
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Enable and start Docker
    systemctl enable docker
    systemctl start docker
    log "Docker installed successfully"
else
    log "Docker already installed"
fi

# Verify docker compose plugin
if ! docker compose version &> /dev/null; then
    warn "Docker Compose plugin not available, attempting to install..."

    install -m 0755 -d /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    fi

    apt-get update -qq
    apt-get install -y docker-compose-plugin

    if ! docker compose version &> /dev/null; then
        error "Docker Compose plugin not available"
        exit 1
    fi

    log "Docker Compose plugin installed successfully"
fi

# Step 3: Configure firewall
log "Step 3: Configuring firewall..."
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
log "Firewall configured"

# Step 4: Clone or update repository
log "Step 4: Managing repository..."
REPO_DIR="/opt/mes-edms-mvp"
REPO_URL="${REPO_URL:-}"  # set this if /opt/mes-edms-mvp is missing and needs clone
ALLOW_DEFAULT_REPO="${ALLOW_DEFAULT_REPO:-}"
DEFAULT_REPO_URL="https://github.com/mashingaan/mes-edms-mvp"

if [ -d "$REPO_DIR/.git" ]; then
    log "Repository exists, pulling latest changes..."
    cd "$REPO_DIR"
    git fetch origin

    DEFAULT_BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')"
    DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

    git pull origin "$DEFAULT_BRANCH" || git pull origin main || git pull origin master
elif [ -d "$REPO_DIR" ]; then
    echo "repo not found, set REPO_URL"
    exit 1
else
    if [ -z "$REPO_URL" ]; then
        if [ "$ALLOW_DEFAULT_REPO" = "1" ]; then
            REPO_URL="$DEFAULT_REPO_URL"
        else
            echo "repo not found, set REPO_URL"
            exit 1
        fi
    fi
    log "Cloning repository from $REPO_URL ..."
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Step 5: Configure environment
log "Step 5: Configuring environment..."
if [ ! -f .env ]; then
    log "Creating .env from env.example..."
    cp env.example .env
    
    # Generate secure SECRET_KEY
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    # IMPORTANT: Do NOT force JSON array format for CORS unless backend explicitly expects it.
    # If you must set it automatically, prefer comma-separated (most compatible):
    # sed -i 's|^CORS_ORIGINS=.*|CORS_ORIGINS=https://inspro-mes.ru,https://api.inspro-mes.ru|' .env
    
    log ".env created with generated secrets"
else
    log ".env already exists, preserving existing configuration"
fi

# Step 6: Start Docker services
log "Step 6: Starting Docker services..."
if [ "${CLEAN_RESTART:-0}" = "1" ]; then
    log "CLEAN_RESTART=1 -> running docker compose down"
    docker compose down || true
fi
docker compose up -d --build

# Wait for services to be ready
log "Waiting for services to start..."
sleep 15

# Check if services are running
required_services=(db backend frontend)
running_services="$(docker compose ps --services --filter status=running 2>/dev/null || true)"

# Fallback if filter is unsupported
if [ -z "$running_services" ]; then
    running_services="$(docker compose ps --services 2>/dev/null || true)"
fi

missing=0
for svc in "${required_services[@]}"; do
    if ! echo "$running_services" | grep -qx "$svc"; then
        missing=1
        warn "Service not running yet: $svc"
    fi
done

if [ "$missing" -eq 1 ]; then
    error "Docker services failed to start"
    docker compose logs --tail=50
    exit 1
fi

log "Docker services started successfully"

# Run Alembic migrations if present
if [ -f "backend/alembic.ini" ] || [ -f "alembic.ini" ]; then
    log "Running Alembic migrations..."
    docker compose exec backend alembic upgrade head
fi

# Step 7: Configure Nginx
log "Step 7: Configuring Nginx..."

# Create Nginx configuration
generate_nginx_config

# Enable site
ln -sf /etc/nginx/sites-available/inspro-mes /etc/nginx/sites-enabled/inspro-mes

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if ! nginx -t; then
    error "Nginx configuration test failed"
    exit 1
fi

# Reload Nginx
systemctl enable nginx
if ! reload_nginx; then
    error "Failed to reload Nginx"
    nginx -t
    exit 1
fi
log "Nginx configured successfully"

# Step 8: Obtain SSL certificates
log "Step 8: Obtaining SSL certificates..."

CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
if [ -z "$CERTBOT_EMAIL" ]; then
    CERTBOT_EMAIL="$(grep -E '^ADMIN_EMAIL=' .env 2>/dev/null | head -n 1 | cut -d= -f2- || true)"
fi
if [ -z "$CERTBOT_EMAIL" ]; then
    CERTBOT_EMAIL="animobit12@mail.ru"
    warn "CERTBOT_EMAIL is not set. Using fallback: $CERTBOT_EMAIL"
fi

CERTBOT_DEPLOY_HOOK=""
if command -v systemctl &> /dev/null && systemctl is-active --quiet nginx; then
    CERTBOT_DEPLOY_HOOK="systemctl reload nginx"
elif command -v nginx &> /dev/null; then
    CERTBOT_DEPLOY_HOOK="nginx -s reload"
fi

CERTBOT_RATE_LIMIT=0

# Check if certificates already exist
if ssl_certs_exist; then
    log "SSL certificates already exist, checking for renewal..."

    set +e
    if [ -n "$CERTBOT_DEPLOY_HOOK" ]; then
        flock -n /var/lock/certbot.lock certbot renew --non-interactive --deploy-hook "$CERTBOT_DEPLOY_HOOK" 2>&1 | tee /tmp/certbot-renew.log
    else
        flock -n /var/lock/certbot.lock certbot renew --non-interactive 2>&1 | tee /tmp/certbot-renew.log
    fi
    CERTBOT_EXIT_CODE=${PIPESTATUS[0]}
    set -e

    if [ "$CERTBOT_EXIT_CODE" -eq 0 ]; then
        if grep -q "No renewals were attempted" /tmp/certbot-renew.log; then
            log "SSL certificates are up to date, no renewal needed"
        elif grep -q "Successfully renewed" /tmp/certbot-renew.log; then
            log "SSL certificates renewed successfully"
        else
            log "Certbot renew completed (certificates may already be fresh)"
        fi
    else
        if grep -qi "too many requests" /tmp/certbot-renew.log 2>/dev/null; then
            CERTBOT_RATE_LIMIT=1
        else
            error "Certbot renewal failed with exit code $CERTBOT_EXIT_CODE"
            cat /tmp/certbot-renew.log
            exit 1
        fi
    fi
else
    log "Obtaining new SSL certificates..."

    set +e
    flock -n /var/lock/certbot.lock certbot certonly --nginx \
        -d inspro-mes.ru \
        -d api.inspro-mes.ru \
        --non-interactive \
        --agree-tos \
        --email "$CERTBOT_EMAIL" 2>&1 | tee /tmp/certbot-obtain.log
    CERTBOT_EXIT_CODE=${PIPESTATUS[0]}
    set -e

    if [ "$CERTBOT_EXIT_CODE" -eq 0 ]; then
        log "SSL certificates obtained successfully"

        unset CERTBOT_CERTS_CACHE
        CERTBOT_CERTS_LOGGED=0
        if ssl_certs_exist; then
            log "Certificates verified, regenerating Nginx configuration with HTTPS..."
            generate_nginx_config

            if ! nginx -t; then
                error "Nginx configuration test failed after SSL setup"
                exit 1
            fi

            if ! reload_nginx; then
                error "Failed to reload Nginx after certbot operation"
                nginx -t
                exit 1
            fi

            log "Nginx reloaded with HTTPS configuration"
        else
            error "Certbot reported success but certificates not found"
            exit 1
        fi
    else
        if grep -qi "too many requests" /tmp/certbot-obtain.log 2>/dev/null; then
            CERTBOT_RATE_LIMIT=1
        else
            error "Certbot failed to obtain certificates (exit code: $CERTBOT_EXIT_CODE)"
            cat /tmp/certbot-obtain.log
            exit 1
        fi
    fi
fi

if grep -qi "too many requests" /tmp/certbot-*.log 2>/dev/null; then
    CERTBOT_RATE_LIMIT=1
fi

if [ "$CERTBOT_RATE_LIMIT" -eq 1 ]; then
    warn "Certbot rate limit reached. Certificates will be obtained on next deployment."
    if ssl_certs_exist; then
        warn "Certbot rate limit reached. Keeping existing HTTPS configuration."
    else
        warn "Certbot rate limit reached. Continuing with HTTP-only configuration (will retry next deploy)."
    fi
fi

log "SSL certificates configured successfully"

# Log certificate expiration info
if ssl_certs_exist; then
    CERT_INFO="$(certbot certificates 2>/dev/null | grep -A 2 "Certificate Name:" || true)"
    if [ -n "$CERT_INFO" ]; then
        log "Certificate status:"
        echo "$CERT_INFO" | grep -E "(Certificate Name|Expiry Date)" || true
    fi
fi

rm -f /tmp/certbot-renew.log /tmp/certbot-obtain.log

check_port_443() {
    local host=$1
    if command -v nc &> /dev/null; then
        if nc -z -w5 "$host" 443 2>/dev/null; then
            return 0
        fi
    elif command -v timeout &> /dev/null; then
        if timeout 5 bash -c "echo > /dev/tcp/$host/443" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

validate_ssl_certificate() {
    local domain=$1
    local output

    if ! command -v openssl &> /dev/null; then
        warn "SSL validation skipped for $domain: openssl missing"
        return 0
    fi

    # Prefer local nginx to avoid DNS/hairpin issues; use SNI via -servername
    if command -v timeout &> /dev/null; then
        output=$(timeout 10 openssl s_client -servername "$domain" -connect 127.0.0.1:443 </dev/null 2>&1 || true)
    else
        output=$(openssl s_client -servername "$domain" -connect 127.0.0.1:443 </dev/null 2>&1 || true)
    fi

    if echo "$output" | grep -q "Verify return code:"; then
        if echo "$output" | grep -q "Verify return code: 0"; then
            return 0
        fi
        warn "SSL certificate verification failed for $domain"
        echo "$output" | grep -i "Verify return code" || true
        return 1
    fi

    if echo "$output" | grep -q "Verification: OK"; then
        return 0
    fi

    if echo "$output" | grep -qi "certificate verify failed"; then
        warn "SSL certificate verification failed for $domain"
        echo "$output" | grep -i "verify" || true
        return 1
    fi

    warn "SSL connection test inconclusive for $domain"
    echo "$output" | grep -i "Verify return code\|Verification" || true
    return 0
}

# Step 9: Final health checks
log "Step 9: Running health checks..."
sleep 10

HEALTH_FAILED=0
CHECK_PUBLIC="${CHECK_PUBLIC:-0}"
STRICT_PUBLIC_CHECKS="${STRICT_PUBLIC_CHECKS:-0}"

# Check frontend
log "Checking frontend (https://inspro-mes.ru)..."

# Check port 443 availability (local nginx)
if ! check_port_443 "127.0.0.1"; then
    error "FAIL Port 443 is not accessible locally (127.0.0.1:443) for inspro-mes.ru"
    warn "Diagnostic commands:"
    warn "  - sudo ufw status | grep 443"
    warn "  - sudo netstat -tlnp | grep :443"
    warn "  - sudo ss -tlnp | grep :443"
    HEALTH_FAILED=1
elif ! validate_ssl_certificate "inspro-mes.ru"; then
    error "FAIL SSL certificate validation failed for inspro-mes.ru"
    warn "Diagnostic commands:"
    warn "  - timeout 10 openssl s_client -servername inspro-mes.ru -connect 127.0.0.1:443 -showcerts"
    warn "  - sudo certbot certificates"
    warn "  - ls -la /etc/letsencrypt/live/"
    HEALTH_FAILED=1
elif curl -sSf -I --resolve inspro-mes.ru:443:127.0.0.1 https://inspro-mes.ru > /dev/null 2>&1; then
    log "OK Frontend is accessible"
else
    error "FAIL Frontend health check failed (HTTPS request failed)"
    warn "Diagnostic commands:"
    warn "  - curl -vI --resolve inspro-mes.ru:443:127.0.0.1 https://inspro-mes.ru"
    warn "  - sudo nginx -T | grep -A 20 'server_name inspro-mes.ru'"
    warn "  - sudo systemctl status nginx"
    HEALTH_FAILED=1
fi

if [ "$CHECK_PUBLIC" = "1" ]; then
    log "Checking public frontend (https://inspro-mes.ru)..."
    if curl -sSf -I https://inspro-mes.ru > /dev/null 2>&1; then
        log "OK Public frontend is accessible"
    else
        if [ "$STRICT_PUBLIC_CHECKS" = "1" ]; then
            error "FAIL Public frontend reachability failed"
            HEALTH_FAILED=1
        else
            warn "WARN Public frontend reachability failed"
        fi
    fi
fi

# Check API docs
log "Checking API (https://api.inspro-mes.ru/docs)..."

# Check port 443 availability (local nginx)
if ! check_port_443 "127.0.0.1"; then
    error "FAIL Port 443 is not accessible locally (127.0.0.1:443) for api.inspro-mes.ru"
    warn "Diagnostic commands:"
    warn "  - sudo ufw status | grep 443"
    warn "  - sudo netstat -tlnp | grep :443"
    warn "  - sudo ss -tlnp | grep :443"
    HEALTH_FAILED=1
elif ! validate_ssl_certificate "api.inspro-mes.ru"; then
    error "FAIL SSL certificate validation failed for api.inspro-mes.ru"
    warn "Diagnostic commands:"
    warn "  - timeout 10 openssl s_client -servername api.inspro-mes.ru -connect 127.0.0.1:443 -showcerts"
    warn "  - sudo certbot certificates"
    warn "  - ls -la /etc/letsencrypt/live/"
    HEALTH_FAILED=1
elif curl -sSf -I --resolve api.inspro-mes.ru:443:127.0.0.1 https://api.inspro-mes.ru/docs > /dev/null 2>&1; then
    log "OK API is accessible"
else
    error "FAIL API health check failed (HTTPS request failed)"
    warn "Diagnostic commands:"
    warn "  - curl -vI --resolve api.inspro-mes.ru:443:127.0.0.1 https://api.inspro-mes.ru/docs"
    warn "  - sudo nginx -T | grep -A 20 'server_name api.inspro-mes.ru'"
    warn "  - docker compose logs backend --tail=50"
    HEALTH_FAILED=1
fi

if [ "$CHECK_PUBLIC" = "1" ]; then
    log "Checking public API (https://api.inspro-mes.ru/docs)..."
    if curl -sSf -I https://api.inspro-mes.ru/docs > /dev/null 2>&1; then
        log "OK Public API is accessible"
    else
        if [ "$STRICT_PUBLIC_CHECKS" = "1" ]; then
            error "FAIL Public API reachability failed"
            HEALTH_FAILED=1
        else
            warn "WARN Public API reachability failed"
        fi
    fi
fi

# Check Docker services
log "Checking Docker services..."
required_services=(db backend frontend)
running_services="$(docker compose ps --services --filter status=running 2>/dev/null || true)"
if [ -z "$running_services" ]; then
    running_services="$(docker compose ps --services 2>/dev/null || true)"
fi

missing=0
for svc in "${required_services[@]}"; do
    if ! echo "$running_services" | grep -qx "$svc"; then
        missing=1
        warn "Service not running: $svc"
    fi
done

if [ "$missing" -eq 0 ]; then
    log "OK Docker services are running"
else
    error "FAIL Some Docker services are not running"
    docker compose ps
    HEALTH_FAILED=1
fi

# Final result
echo ""
echo "=========================================="
if [ $HEALTH_FAILED -eq 0 ]; then
    echo -e "${GREEN}OK DEPLOYMENT SUCCESSFUL${NC}"
    echo ""
    echo "Your application is now available at:"
    echo "  - Frontend: https://inspro-mes.ru"
    echo "  - API Docs: https://api.inspro-mes.ru/docs"
    echo ""
    echo "Login credentials are configured in .env (keep them private)."
    echo ""
    echo "To check status: bash /opt/mes-edms-mvp/status.sh"
else
    echo -e "${RED}DEPLOYMENT COMPLETED WITH ERRORS${NC}"
    echo ""
    echo "Some health checks failed. Run these commands to diagnose:"
    echo ""
    echo "SSL/HTTPS diagnostics (local nginx):"
    echo "  - sudo certbot certificates"
    echo "  - timeout 10 openssl s_client -servername inspro-mes.ru -connect 127.0.0.1:443 -showcerts"
    echo "  - sudo nginx -T | grep -E '(listen 443|ssl_certificate)'"
    echo "  - sudo ufw status | grep 443"
    echo ""
    echo "Service diagnostics:"
    echo "  - docker compose logs backend --tail=100"
    echo "  - sudo systemctl status nginx"
    echo "  - sudo nginx -t"
    echo ""
    echo "Manual health checks (local with SNI/Host):"
    echo "  - curl -vI --resolve inspro-mes.ru:443:127.0.0.1 https://inspro-mes.ru"
    echo "  - curl -vI --resolve api.inspro-mes.ru:443:127.0.0.1 https://api.inspro-mes.ru/docs"
    exit 1
fi
echo "=========================================="
