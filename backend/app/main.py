from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.escalation import router as escalation_router
from app.auth.exceptions import (
    AuthenticationError,
    ForbiddenError,
)
from app.core.config import settings
from app.core.logging import app_logger
from app.core.observability import ApplicationMetrics
from app.core.rate_limit import InMemoryRateLimiter
from app.database.session import engine
from app.voice.voice_router import router as voice_router

OPENAPI_TAGS = [
    {
        "name": "Operations",
        "description": "Health, readiness, version, and metrics endpoints for production platforms.",
    },
    {
        "name": "Authentication",
        "description": "Login, token refresh, and session management.",
    },
    {
        "name": "Organizations",
        "description": "Organization lifecycle and tenancy management.",
    },
    {"name": "Users", "description": "User administration and role-aware access."},
    {
        "name": "Knowledge",
        "description": "Document ingestion, search, and RAG retrieval.",
    },
    {
        "name": "Orchestration",
        "description": "AI conversation routing and agent responses.",
    },
    {
        "name": "Escalations",
        "description": "Human-in-the-loop queue and operator actions.",
    },
    {
        "name": "Dashboard",
        "description": "Enterprise dashboard metrics and live activity.",
    },
    {
        "name": "Voice",
        "description": "Voice sessions, transcripts, and takeover support.",
    },
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI Agent Platform",
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "Converra AI Platform Team"},
    license_info={"name": "MIT", "identifier": "MIT"},
)
app.state.metrics = ApplicationMetrics()
app.state.rate_limiter = InMemoryRateLimiter(
    settings.rate_limit_requests,
    settings.rate_limit_window_seconds,
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
if settings.app_env.lower() in {"production", "prod"}:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.include_router(api_router)
app.include_router(escalation_router)
app.include_router(dashboard_router)
app.include_router(voice_router)


@app.middleware("http")
async def production_request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    client_ip = request.client.host if request.client else "unknown"
    if not request.url.path.startswith(
        ("/health", "/metrics", "/docs", "/openapi.json")
    ):
        if not app.state.rate_limiter.allowed(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded.", "request_id": request_id},
                headers={"Retry-After": str(settings.rate_limit_window_seconds)},
            )

    started_at = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "microphone=(self)"
    route_path = getattr(request.scope.get("route"), "path", request.url.path)
    app.state.metrics.record_request(request.method, route_path, response.status_code)
    app_logger.info(
        "request_id={} method={} path={} status={} duration_ms={}",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    status_code = status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, ForbiddenError):
        status_code = status.HTTP_403_FORBIDDEN

    app_logger.warning(
        "Authentication error on {}: {}",
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    app_logger.warning("Validation error on {}: {}", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    app_logger.exception("Unhandled error on {}", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error."},
    )


@app.on_event("startup")
async def startup():

    app_logger.info("Starting Converra AI")


@app.on_event("shutdown")
async def shutdown():

    app_logger.info("Stopping Converra AI")


@app.get("/")
async def root():

    app_logger.info("Root endpoint accessed")

    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "message": "Welcome to Converra AI 🚀",
    }


@app.get("/health")
async def health():

    app_logger.info("Health endpoint checked")

    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


@app.get("/health/live", tags=["Operations"], summary="Liveness probe")
async def liveness() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready", tags=["Operations"], summary="Readiness probe")
async def readiness() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        app_logger.warning("Readiness check failed: {}", exc.__class__.__name__)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready"},
        )
    return JSONResponse(content={"status": "ready"})


@app.get("/version", tags=["Operations"], summary="Application version")
async def version() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@app.get("/metrics", tags=["Operations"], summary="Basic Prometheus-compatible metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        app.state.metrics.render_prometheus(), media_type="text/plain; version=0.0.4"
    )
