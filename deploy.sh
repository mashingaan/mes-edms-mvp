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

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root"
    exit 1
fi

log "Starting deployment of MES-EDMS MVP..."

DEMO_SEED_OK=0

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

    log "Seeding demo data..."
    if docker compose exec backend python scripts/seed_demo_data.py; then
        DEMO_SEED_OK=1
        log "Demo data seeded successfully"
    else
        DEMO_SEED_OK=0
        warn "Demo data seeding failed (may already be seeded). Continuing."
    fi
fi

# Step 7: Configure Nginx
log "Step 7: Configuring Nginx..."

# Create Nginx configuration
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
systemctl reload nginx
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

# Check if certificates already exist
if certbot certificates 2>/dev/null | grep -q "inspro-mes.ru"; then
    log "SSL certificates already exist, attempting renewal..."
    certbot renew --nginx --non-interactive
else
    log "Obtaining new SSL certificates..."
    certbot --nginx \
        -d inspro-mes.ru \
        -d api.inspro-mes.ru \
        --non-interactive \
        --agree-tos \
        --email "$CERTBOT_EMAIL" \
        --redirect
fi

log "SSL certificates configured"

# Step 9: Final health checks
log "Step 9: Running health checks..."
sleep 10

HEALTH_FAILED=0

# Check frontend
log "Checking frontend (https://inspro-mes.ru)..."
if curl -sSf -I https://inspro-mes.ru > /dev/null 2>&1; then
    log "✓ Frontend is accessible"
else
    error "✗ Frontend health check failed"
    HEALTH_FAILED=1
fi

# Check API docs
log "Checking API (https://api.inspro-mes.ru/docs)..."
if curl -sSf -I https://api.inspro-mes.ru/docs > /dev/null 2>&1; then
    log "✓ API is accessible"
else
    error "✗ API health check failed"
    HEALTH_FAILED=1
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
    log "✓ Docker services are running"
else
    error "✗ Some Docker services are not running"
    docker compose ps
    HEALTH_FAILED=1
fi

# Final result
echo ""
echo "=========================================="
if [ $HEALTH_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL${NC}"
	echo ""
	echo "Your application is now available at:"
	echo "  - Frontend: https://inspro-mes.ru"
	echo "  - API Docs: https://api.inspro-mes.ru/docs"
	echo ""
	echo "Login credentials are configured in .env (keep them private)."
	if [ "$DEMO_SEED_OK" = "1" ]; then
		echo "Demo users (seeded by seed_demo_data.py):"
		echo "  - engineer@example.com / engineer123 (responsible)"
		echo "  - designer@example.com / designer123 (responsible)"
		echo "  - viewer@example.com / viewer123 (viewer)"
	else
		echo -e "${YELLOW}WARNING:${NC} Demo data was not seeded."
	fi
	echo ""
	echo "To check status: bash /opt/mes-edms-mvp/status.sh"
else
	echo -e "${RED}✗ DEPLOYMENT COMPLETED WITH ERRORS${NC}"
    echo ""
    echo "Some health checks failed. Run these commands to diagnose:"
    echo "  - docker compose logs backend --tail=100"
    echo "  - systemctl status nginx"
    echo "  - nginx -t"
    echo "  - curl -I https://inspro-mes.ru"
    echo "  - curl -I https://api.inspro-mes.ru/docs"
    exit 1
fi
echo "=========================================="
