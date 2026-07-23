from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.donations import router as donations_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "ReWear API — AI-powered clothing donation quality assessment "
            "and upcycling recommendation system."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten to your Flutter app's origin before production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(donations_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    def health_check() -> dict:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
