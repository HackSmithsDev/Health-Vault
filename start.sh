#!/bin/sh
set -eu

: "${PORT:=8080}"

if [ -z "${DATABASE_URL:-}" ] && [ -z "${DATABASE_URI:-}" ]; then
    echo "DATABASE_URL or DATABASE_URI must be configured" >&2
    exit 1
fi

# Apply committed Alembic migrations before accepting traffic.
flask --app wsgi:app db upgrade

echo "Starting Gunicorn on 0.0.0.0:${PORT}..."
gunicorn --workers 2 --bind "0.0.0.0:${PORT}" --timeout 120 wsgi:app &
gunicorn_pid=$!

cleanup() {
    kill "$gunicorn_pid" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

if [ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]; then
    echo "Connecting to Cloudflare Tunnel..."
    cloudflared tunnel --no-autoupdate run --token "$CLOUDFLARE_TUNNEL_TOKEN"
else
    echo "CLOUDFLARE_TUNNEL_TOKEN is not set; serving Gunicorn only."
    wait "$gunicorn_pid"
fi
