#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    printf '\n==> %s\n' "$1"
}

fail() {
    printf 'ERROR: %s\n' "$1" >&2
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

cd "$PROJECT_DIR"

command_exists php || fail "PHP CLI is required. Install PHP >= 5.3.3 and run this script again."

if command_exists composer; then
    COMPOSER_CMD=(composer)
elif [ -f "$PROJECT_DIR/composer.phar" ]; then
    COMPOSER_CMD=(php "$PROJECT_DIR/composer.phar")
else
    fail "Composer is required. Install Composer globally or place composer.phar in the project root."
fi

export COMPOSER_ALLOW_SUPERUSER="${COMPOSER_ALLOW_SUPERUSER:-1}"

log "Installing Composer dependencies"
"${COMPOSER_CMD[@]}" install --no-interaction --prefer-dist

log "Ensuring Symfony cache and log directories exist"
mkdir -p "$PROJECT_DIR/app/cache" "$PROJECT_DIR/app/logs"
chmod -R u+rwX "$PROJECT_DIR/app/cache" "$PROJECT_DIR/app/logs" 2>/dev/null || true

log "Checking Symfony requirements"
php "$PROJECT_DIR/app/check.php"

log "Clearing development cache"
php "$PROJECT_DIR/app/console" cache:clear --env=dev --no-warmup

log "Installing web assets"
php "$PROJECT_DIR/app/console" assets:install "$PROJECT_DIR/web" --symlink --relative 2>/dev/null \
    || php "$PROJECT_DIR/app/console" assets:install "$PROJECT_DIR/web"

cat <<'EOF'

Setup complete.

Next steps:
  1. Review app/config/parameters.yml for database and mailer settings.
  2. Start a local web server with the web/ directory as the document root.
  3. Open /app_dev.php/demo/hello/Fabien in your browser.
EOF
