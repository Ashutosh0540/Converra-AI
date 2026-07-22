# Security

Never commit `.env` files, API keys, JWT secrets, or database dumps. Production requires a strong JWT secret, explicit CORS origins, and TLS at the edge. The application applies security headers, input validation, upload-size limits, role checks, and process-local rate limiting. Report vulnerabilities privately to the maintainers; do not disclose exploitable details in public issues.

Run `pip-audit -r backend/requirements.txt`, `pip-audit -r backend/requirements-dev.txt`, and `npm audit --omit=dev --audit-level=high` before release. Next.js has been upgraded to `15.5.20`; npm audit still reports moderate PostCSS advisories in Next's dependency tree, so keep Next and PostCSS current before production exposure.
