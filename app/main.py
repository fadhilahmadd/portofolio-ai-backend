import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.limiter import limiter
from slowapi.middleware import SlowAPIMiddleware 
from slowapi.errors import RateLimitExceeded

async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )

def create_app() -> FastAPI:
    """
    Creates and configures the FastAPI application.
    """
    if settings.ENVIRONMENT == "production":
        app = FastAPI(
            title=settings.PROJECT_NAME,
            openapi_url=None,
            docs_url=None,
            redoc_url=None
        )
    else:
        app = FastAPI(
            title=settings.PROJECT_NAME,
            openapi_url=f"{settings.API_V1_STR}/openapi.json"
        )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.on_event("startup")
    async def on_startup():
        """
        Initializes the database when the application starts.
        """
        if not settings.GOOGLE_API_KEY or not str(settings.GOOGLE_API_KEY).strip():
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. Please add it to your .env or environment before starting the server."
            )
            
        os.makedirs(settings.AUDIO_DIR, exist_ok=True)
        
        await init_db()

    static_files_path = os.path.join(os.path.dirname(__file__), "..", "static")
    app.mount("/static", StaticFiles(directory=static_files_path), name="static")

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Health"])
    async def root() -> dict:
        """
        Root endpoint providing a welcome message.
        """
        return {"message": "Welcome to the Portofolio AI Chatbot API"}

    @app.get("/healthz", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app

app = create_app()