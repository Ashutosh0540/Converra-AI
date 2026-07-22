# Converra AI

[![CI](https://github.com/your-org/converra-ai/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Enterprise AI operations platform for retrieval-augmented conversations, voice sessions, and human-in-the-loop escalation.

## Quick start

1. Copy `backend/.env.example` to `backend/.env` and set strong secrets.
2. Run `docker compose up --build`.
3. Apply migrations: `docker compose exec backend alembic upgrade head`.
4. Open `http://localhost:3000`; API docs are at `http://localhost:8000/docs`.

For local hot reload, use `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`.

## Documentation

- [System architecture](SYSTEM_ARCHITECTURE.md)
- [API documentation](API_DOCUMENTATION.md)
- [Deployment](DEPLOYMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Troubleshooting](TROUBLESHOOTING.md)
