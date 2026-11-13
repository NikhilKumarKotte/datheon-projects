import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.extractor.config import Settings, get_settings
from src.extractor.api.routes import router

logger = logging.getLogger("extractor.app")
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info(
        "Structured LLM Extractor starting up in %s mode (default model: %s)...",
        settings.environment,
        settings.default_model,
    )
    yield
    logger.info("Structured LLM Extractor shutting down...")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory for FastAPI app instance."""
    app_settings = settings or get_settings()

    app = FastAPI(
        title="Structured LLM Extractor API",
        description="Production API for schema-constrained document extraction with Gemini and Pydantic.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception on %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred during processing.",
                "detail": str(exc) if app_settings.environment != "production" else None,
            },
        )

    # Include API routes
    app.include_router(router)

    # Mount static assets if available
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_dashboard():
            return FileResponse(str(STATIC_DIR / "index.html"))

    return app


# Default ASGI application instance for uvicorn
app = create_app()
