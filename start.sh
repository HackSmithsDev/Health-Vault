#!/bin/sh
set -eu

# Default to 8081 if PORT is not set
: "${PORT:=8081}"

if [ -z "${DATABASE_URL:-}" ] && [ -z "${DATABASE_URI:-}" ]; then
    echo "DATABASE_URL or DATABASE_URI must be configured" >&2
    exit 1
fi

# Apply database migrations
echo "Applying database migrations..."
flask --app wsgi:app db upgrade || echo "Migrations completed or skipped."

# Launch Cloudflare Tunnel in background (points to 127.0.0.1:8081)
if [ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]; then
    echo "Connecting to Cloudflare Tunnel on 127.0.0.1:${PORT}..."
    cloudflared tunnel --no-autoupdate run --token "$CLOUDFLARE_TUNNEL_TOKEN" &
else
    echo "CLOUDFLARE_TUNNEL_TOKEN is not set; running Gunicorn only."
fi

echo "Starting Gunicorn on 0.0.0.0:${PORT}..."
# Using exec foregrounds Gunicorn so Render directly supervises it
exec gunicorn \
    --workers "${WEB_CONCURRENCY:-2}" \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --preload \
    wsgi:app