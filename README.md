# Health Vault

Health Vault is a Flask application for provider-managed clinical intake,
medical-image routing, specialist analysis, patient access, and report export.

## Requirements

- Python 3.11 or newer
- PostgreSQL
- Redis, or the built-in FakeRedis development fallback
- A Groq API key for specialist responses
- Clinical model weights in `ai/weights`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 wsgi.py
```

Set `DATABASE_URL`, `REDIS_URL`, `GROQ_API_KEY`, and the SMTP variables in
`.env`. Never commit `.env` or production credentials.

The development server runs at `http://127.0.0.1:8081` when `FLASK_RUN_PORT`
is set to `8080`.

## AI models

Runtime inference uses the existing files under `ai/weights`. The training
tools are retained so those weights can be reproduced:

```bash
python3 ai/setup_clinical_data.py
python3 ai/train.py router --mode global
python3 ai/train.py router --mode subject
python3 ai/train.py specialists
```

The upload gate is a separate binary model. It uses the clinical images as
positive examples and CIFAR-10 as non-clinical negatives. Trainable gate data
is stored under `ai/ai_models/medical_gate/training/`, with the download cache
kept separately under `ai/ai_models/medical_gate/datasets/`:

```bash
python3 ai/prepare_medical_gate.py
python3 ai/train.py gate
```

This creates `ai/weights/medical_gate.pth`. Without that file, the application
still validates image format and lets the clinical router process the upload;
with it, the binary gate rejects non-clinical images before routing.

## Project layout

- `app/`: Flask application, blueprints, models, services, templates, and assets
- `ai/`: dataset setup, reproducible training tools, and model weights
- `migrations/`: Alembic database migrations
- `config.py`: environment-backed application configuration
- `wsgi.py`: application entry point

## Render deployment

The repository includes a Docker deployment with Gunicorn and an optional
Cloudflare Tunnel token:

```bash
docker build -t health-vault .
docker run --env-file .env -e FLASK_ENV=production -e CLOUDFLARE_TUNNEL_TOKEN="$CLOUDFLARE_TUNNEL_TOKEN" -p 8080:8080 health-vault
```

On Render, select **Docker** and configure these environment variables in the
dashboard rather than committing them: `CLOUDFLARE_TUNNEL_TOKEN`,
`DATABASE_URL`, `DIRECT_URL`, `REDIS_URL`, `GROQ_API_KEY`, `SECRET_KEY`, and
the mail settings. The container runs `flask db upgrade` before Gunicorn.

The Cloudflare tunnel's public hostname must route to the container's Gunicorn
origin on the same port Render provides through `PORT` (use `8080` when running
the container locally).

## License

MIT. See [LICENSE](LICENSE).
