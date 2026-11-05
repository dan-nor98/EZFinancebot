# EZFinancebot

A Persian-first Telegram personal-finance system. The modular Finance Core owns every
financial rule; Telegram is only an adapter. Money is stored as integer IRR and parsed
deterministically without an LLM.

## Development

```bash
cp .env.example .env
docker compose up --build
docker compose run --rm api uv run alembic upgrade head
```

The API is available on port 8000 (`/health/live`, `/health/ready`, `/docs`) and the
gateway on port 8001. Local checks use the exact committed lockfile:

```bash
uv sync --frozen
uv run ruff check .
uv run mypy .
uv run pytest
```

See [`docs/operations.md`](docs/operations.md) for migrations, backup, and restore.

