"""
XRD Compound Identification and Analysis System
================================================
FastAPI application entry point.

Registers all routers, configures CORS, initialises the SQLite database,
creates required upload/output directories, and exposes a health-check
endpoint.

Run with:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from routes.upload_routes import router as upload_router
from routes.analysis_routes import router as analysis_router
from routes.report_routes import router as report_router
from database.sqlite.db_init import init_db

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create directories and initialise the database on startup."""
    logger.info("Starting XRD Analysis System …")

    # Ensure all required directories exist
    required_dirs = [
        settings.UPLOAD_CSV_DIR,
        settings.UPLOAD_TEMP_DIR,
        settings.REPORTS_PDF_DIR,
        settings.REPORTS_GRAPHS_DIR,
        settings.REPORTS_OVERLAY_DIR,
        settings.EXPERIMENTAL_DATA_DIR,
        settings.SQLITE_DIR,
    ]
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info("Ensured directory: %s", directory)

    # Initialise SQLite schema
    init_db()
    logger.info("Database initialised.")

    yield  # application runs here

    logger.info("Shutting down XRD Analysis System.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        contact={
            "name": "XRD Analysis Team",
            "email": "support@xrd-analysis.example.com",
        },
        license_info={"name": "MIT"},
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Static files — serve generated graphs and PDF reports
    # -----------------------------------------------------------------------
    application.mount(
        "/reports",
        StaticFiles(directory=settings.REPORTS_BASE_DIR),
        name="reports",
    )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    application.include_router(
        upload_router,
        prefix="/api/upload",
        tags=["Upload"],
    )
    application.include_router(
        analysis_router,
        prefix="/api/analysis",
        tags=["Analysis"],
    )
    application.include_router(
        report_router,
        prefix="/api/report",
        tags=["Reports"],
    )

    # -----------------------------------------------------------------------
    # Health check
    # -----------------------------------------------------------------------
    @application.get("/api/health", tags=["Health"])
    async def health_check():
        """Returns service status and version."""
        return {
            "status": "ok",
            "version": settings.APP_VERSION,
            "service": settings.APP_TITLE,
        }

    # -----------------------------------------------------------------------
    # Root redirect info
    # -----------------------------------------------------------------------
    @application.get("/", tags=["Root"])
    async def root():
        return {
            "message": "XRD Compound Identification and Analysis System API",
            "docs": "/docs",
            "health": "/api/health",
        }

    return application


# ---------------------------------------------------------------------------
# Application instance (used by uvicorn)
# ---------------------------------------------------------------------------
app = create_app()