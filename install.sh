#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/opt/docker-compose-manager}"
APP_PORT="${APP_PORT:-5000}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
COMPOSE_URL="${COMPOSE_URL:-https://raw.githubusercontent.com/wuyou69/Docker-Compose-Manager/main/docker-compose.yml}"

if command -v docker >/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
else
  echo "Docker is not installed or not in PATH. Please install Docker first."
  exit 1
fi

mkdir -p "$APP_DIR/data"
cd "$APP_DIR"

if command -v wget >/dev/null 2>&1; then
  wget -O docker-compose.yml "$COMPOSE_URL"
elif command -v curl >/dev/null 2>&1; then
  curl -L "$COMPOSE_URL" -o docker-compose.yml
else
  echo "wget or curl is required to download docker-compose.yml."
  exit 1
fi

touch docker_compose_file.db
cat > .env <<EOF
APP_PORT=$APP_PORT
GITHUB_TOKEN=$GITHUB_TOKEN
EOF

if [ -n "$ADMIN_PASSWORD" ]; then
  printf 'ADMIN_PASSWORD=%s\n' "$ADMIN_PASSWORD" >> .env
fi

$DOCKER_COMPOSE pull
$DOCKER_COMPOSE up -d

echo
echo "Docker Compose Manager started."
echo "URL: http://SERVER_IP:$APP_PORT"
echo "Username: admin"
echo "Password: generated in application startup logs"
echo "View password: docker logs docker-compose-file | grep 'Generated admin password'"
