#!/usr/bin/env bash
# deploy.sh -- deploy the RP1 MSF Map Service (worldforge-msf) to Fly.io.
# Build context = this directory (its own fly.toml). Token from repo-root .env (gitignored).
# Secrets: MVSADMINKEY (the metaverse server admin key, also the Scene Assembler login key) and
# MYSQLPASSWORD (the embedded MariaDB user password) are generated if unset and stored as Fly
# secrets; they are never printed.
set -euo pipefail
cd "$(dirname "$0")"          # cloud/msf-svc -- the fly.toml here names the app and context
ROOT="$(cd ../.. && pwd)"

if [ -z "${FLY_API_TOKEN:-}" ] && [ -f "$ROOT/.env" ]; then
  export $(grep -E '^FLY_API_TOKEN=' "$ROOT/.env" | head -1 | xargs)
fi
: "${FLY_API_TOKEN:?FLY_API_TOKEN not set. Put it in $ROOT/.env (gitignored): FLY_API_TOKEN=... }"
command -v flyctl >/dev/null 2>&1 || { echo "flyctl not installed -> brew install flyctl"; exit 2; }

APP=worldforge-msf
if ! flyctl status -a "$APP" >/dev/null 2>&1; then
  echo "app $APP does not exist; creating..."
  flyctl apps create "$APP" >/dev/null
fi

if [ -z "${MVSADMINKEY:-}" ]; then MVSADMINKEY=$(openssl rand -hex 24); fi
if [ -z "${MSF_MYSQL_PASSWORD:-}" ]; then MSF_MYSQL_PASSWORD=$(openssl rand -hex 24); fi
flyctl secrets set -a "$APP" MVSADMINKEY="$MVSADMINKEY" MYSQLPASSWORD="$MSF_MYSQL_PASSWORD" >/dev/null

flyctl deploy --remote-only
echo "tip: curl https://worldforge-msf.fly.dev/ | head; the service also speaks socket.io on :443"