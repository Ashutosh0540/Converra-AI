# Deployment

Set production values in `backend/.env`: `APP_ENV=production`, `DEBUG=false`, a long unique `JWT_SECRET`, PostgreSQL `DATABASE_URL`, exact `CORS_ORIGINS`, and `TRUSTED_HOSTS`.

Run `docker compose up -d --build`, then `docker compose exec backend alembic upgrade head`. Confirm `/health/ready` returns 200 before routing traffic. Terminate TLS at the ingress or load balancer; keep PostgreSQL private to the Docker network. Back up `postgres_data` and `chroma_data` regularly.

Backend production images install `backend/requirements.txt`; local and CI quality tools live in `backend/requirements-dev.txt`.

Local development defaults to deterministic embeddings. For ML embeddings, install `backend/requirements-ml.txt` and set `EMBEDDING_PROVIDER=sentence_transformers`.

For a non-production demonstration, run `docker compose exec backend python scripts/seed_demo.py`. The script prints its demo credentials; change or remove them before any shared deployment.
