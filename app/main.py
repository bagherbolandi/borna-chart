from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.db import Base, engine
from app import models  # noqa: F401
from app.services.config_registry import get_registry
from app.services.workflow_service import WorkflowService
from app.services.security_service import SecurityService
from app.core.db import SessionLocal


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        WorkflowService(db, get_registry()).seed_definitions()
        SecurityService(db).seed_demo_users()
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cache-Control", "no-store")
        if settings.security_hsts_enabled:
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={settings.security_hsts_max_age_seconds}; includeSubDomains",
            )
        return response

    ui_dir = Path(__file__).resolve().parent / "ui"
    console_path = ui_dir / "console.html"
    review_console_path = ui_dir / "review_console.html"

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/console", response_class=HTMLResponse, include_in_schema=False)
    def index() -> HTMLResponse:
        return HTMLResponse(console_path.read_text(encoding="utf-8"))

    @app.get("/review-console", response_class=HTMLResponse, include_in_schema=False)
    def review_console() -> HTMLResponse:
        return HTMLResponse(review_console_path.read_text(encoding="utf-8"))

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
