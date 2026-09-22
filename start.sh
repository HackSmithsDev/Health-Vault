#!/bin/sh
set -eu

# Fall back to 8081 if PORT is not set by environment
: "${PORT:=8081}"

if [ -z "${DATABASE_URL:-}" ] && [ -z "${DATABASE_URI:-}" ]; then
    echo "DATABASE_URL or DATABASE_URI must be configured" >&2
    exit 1
fi

# Apply committed Alembic migrations before accepting traffic
echo "Applying database migrations..."
flask --app wsgi:app db upgrade || echo "Migrations completed or skipped."

# Launch Cloudflare Tunnel in the background pointing to the active internal port
if [ -n "${CLOUDFLARE_TUNNEL_TOKEN:-}" ]; then
    echo "Connecting to Cloudflare Tunnel on 127.0.0.1:${PORT}..."
    cloudflared tunnel --protocol http2 --no-autoupdate run \
        --url "http://127.0.0.1:${PORT}" \
        --token "$CLOUDFLARE_TUNNEL_TOKEN" &
else
    echo "CLOUDFLARE_TUNNEL_TOKEN is not set; running Gunicorn only."
fi

echo "Starting Gunicorn on 0.0.0.0:${PORT}..."
# Using exec keeps Gunicorn in the foreground so Render can supervise the process
exec gunicorn \
    --workers "${WEB_CONCURRENCY:-2}" \
    --bind "0.0.0.0:${PORT}" \
    --timeout 120 \
    --preload \
    wsgi:app