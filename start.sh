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

# Do not let the tunnel hide a failed web process from Render's port scanner.
ready=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
    if curl --fail --silent --show-error "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
        ready=1
        break
    fi
    if ! kill -0 "$gunicorn_pid" 2>/dev/null; then
        echo "Gunicorn exited before binding to port ${PORT}" >&2
        wait "$gunicorn_pid"
    fi
    sleep 1
done

if [ "$ready" -ne 1 ]; then
    echo "Gunicorn did not become ready on port ${PORT}" >&2
    exit 1
fi

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
