# Troubleshooting

- `503 /health/ready`: verify PostgreSQL connectivity and run Alembic migrations.
- `401` APIs or WebSockets: verify the access token and browser clock.
- Upload rejected: check `MAX_UPLOAD_SIZE_BYTES` and supported parser formats.
- Dashboard offline: verify the backend is reachable and `/ws/dashboard` is not blocked by a proxy.
- Voice unavailable: verify the WebSocket upgrade path, microphone permission, and selected STT/TTS providers.
- Backend Docker build pulls large CUDA/Torch wheels: keep `EMBEDDING_PROVIDER=deterministic` for local dev, or install `backend/requirements-ml.txt` only when ML embeddings are required. The optional `sentence-transformers` stack can resolve GPU-oriented Torch packages on Linux image builds.
