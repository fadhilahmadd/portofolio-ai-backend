from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db
import os

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    @app.on_event("startup")
    async def on_startup():
        """
        Initializes the database when the application starts.
        """
        # Validate critical configuration early (fail fast)
        if not settings.GOOGLE_API_KEY or not str(settings.GOOGLE_API_KEY).strip():
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Please add it to your .env or environment before starting the server."
            )
        await init_db()

    static_files_path = os.path.join(os.path.dirname(__file__), "..", "static")
    app.mount("/static", StaticFiles(directory=static_files_path), name="static")

    # Set up CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Centralized error handlers
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Avoid leaking internals; log in real deployments
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Include the API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/healthz")
    async def health() -> dict:
        return {"status": "ok"}

    return app

app = create_app()