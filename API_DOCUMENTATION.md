# API Documentation

Interactive OpenAPI documentation is available at `/docs`; schema JSON is available at `/openapi.json`.

All protected HTTP APIs require `Authorization: Bearer <access-token>`. WebSocket endpoints receive the access token through the `token` query parameter. Key groups are Users, Organizations, Knowledge, AI, Escalations, Voice, Dashboard, and Operations.

Operational endpoints: `GET /health`, `GET /health/live`, `GET /health/ready`, `GET /version`, and `GET /metrics`.
