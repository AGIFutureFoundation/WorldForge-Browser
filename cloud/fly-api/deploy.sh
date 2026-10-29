#!/usr/bin/env bash
# deploy.sh -- deploy the WorldForge API to Fly.io.
# The token is read from FLY_API_TOKEN in the environment or the .env at repo root (gitignored).
# Never place the token in a committed file, a chat message, or a log.
#
# Create a token:  flyctl auth login  (browser), then:  flyctl tokens deploy -a worldforge-api
#                  -- OR -- https://fly.io/dashboard -> Account settings -> Access tokens
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ -z "${FLY_API_TOKEN:-}" ] && [ -f .env ]; then
  # shellcheck disable=SC2046
  export $(grep -E '^FLY_API_TOKEN=' .env | head -1 | xargs)
fi
: "${FLY_API_TOKEN:?FLY_API_TOKEN not set. Put it in .env at the repo root (gitignored): FLY_API_TOKEN=... }"

command -v flyctl >/dev/null 2>&1 || { echo "flyctl not installed -> brew install flyctl (or: curl -L https://fly.io/install.sh | sh)"; exit 2; }

flyctl deploy --remote-only
echo "tip: flyctl status && curl https://worldforge-api.fly.dev/health"
