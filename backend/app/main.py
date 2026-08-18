from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.database.base import Base
from app.database.session import engine, SessionLocal
from app.services.scheme_service import seed_schemes_if_empty
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and seed if connected
    if engine is not None and SessionLocal is not None:
        try:
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                seed_schemes_if_empty(db)
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="GramSetu AI - AI-powered civic intelligence platform backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to GramSetu AI Backend API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "status": "active",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )
